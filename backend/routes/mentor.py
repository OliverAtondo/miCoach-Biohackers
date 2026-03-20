from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
import aiofiles

from database import get_db
import models
import schemas
from auth import get_current_user
from services.ai import analyze_user_profile, generate_roadmap, chat_with_mentor
from services.github import fetch_all_repos
from services.pdf import extract_text_from_pdf

router = APIRouter(prefix="/api/mentor", tags=["mentor"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


async def _read_cv_text(cv_filename: str) -> str:
    cv_path = os.path.join(UPLOAD_DIR, cv_filename)
    if not os.path.exists(cv_path):
        return "CV not found."
    async with aiofiles.open(cv_path, "rb") as f:
        content = await f.read()
    return extract_text_from_pdf(content)


@router.post("/onboard")
async def onboard(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run Gemini analysis and roadmap generation after registration."""
    if current_user.onboarding_complete:
        return {"message": "Already onboarded", "analysis": current_user.analysis, "roadmap": current_user.roadmap}

    # Extract CV text
    cv_text = ""
    if current_user.cv_filename:
        cv_text = await _read_cv_text(current_user.cv_filename)

    # Fetch GitHub repos
    github_links = []
    if current_user.github_links:
        try:
            github_links = json.loads(current_user.github_links)
        except Exception:
            github_links = []

    github_summaries = await fetch_all_repos(github_links)

    # Step 1: Analyze profile
    analysis = analyze_user_profile(
        name=current_user.name,
        career_path=current_user.career_path,
        cv_text=cv_text,
        github_summaries=github_summaries,
    )

    # Step 2: Generate roadmap
    roadmap = generate_roadmap(
        name=current_user.name,
        career_path=current_user.career_path,
        analysis=analysis,
    )

    # Save to DB
    current_user.analysis = analysis
    current_user.roadmap = roadmap
    current_user.onboarding_complete = True
    db.commit()
    db.refresh(current_user)

    return {"analysis": analysis, "roadmap": roadmap}


@router.post("/chat", response_model=schemas.ChatMessageOut)
async def chat(
    message: schemas.ChatMessageIn,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.onboarding_complete:
        raise HTTPException(status_code=400, detail="Complete onboarding first")

    # Save user message
    user_msg = models.ChatMessage(user_id=current_user.id, role="user", content=message.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build history for context (last 20 messages)
    history_records = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id, models.ChatMessage.id != user_msg.id)
        .order_by(models.ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_records]

    # Get Gemini response
    reply = chat_with_mentor(
        name=current_user.name,
        career_path=current_user.career_path,
        analysis=current_user.analysis or "",
        roadmap=current_user.roadmap or "",
        history=history,
        user_message=message.content,
    )

    # Save model reply
    model_msg = models.ChatMessage(user_id=current_user.id, role="model", content=reply)
    db.add(model_msg)
    db.commit()
    db.refresh(model_msg)

    return model_msg


@router.get("/chat/history", response_model=list[schemas.ChatMessageOut])
def chat_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return messages
