from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
import models
from auth import get_current_user
from services.ai import interview_next, TOTAL_INTERVIEW_QUESTIONS

router = APIRouter(prefix="/api/interview", tags=["interview"])


class RespondRequest(BaseModel):
    session_id: int
    turn_number: int
    answer: str


@router.post("/start")
async def start_interview(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.onboarding_complete:
        raise HTTPException(status_code=400, detail="Complete onboarding first")

    session = models.InterviewSession(
        user_id=current_user.id,
        career_path=current_user.career_path,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        result = interview_next(current_user.name, current_user.career_path, [])
    except Exception as e:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")

    turn = models.InterviewTurn(
        session_id=session.id,
        question=result["question"],
        turn_number=1,
    )
    db.add(turn)
    db.commit()

    return {
        "session_id": session.id,
        "question": result["question"],
        "turn": 1,
        "total": TOTAL_INTERVIEW_QUESTIONS,
    }


@router.post("/respond")
async def respond(
    req: RespondRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == req.session_id,
        models.InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    # Save answer to current turn
    current_turn = db.query(models.InterviewTurn).filter(
        models.InterviewTurn.session_id == session.id,
        models.InterviewTurn.turn_number == req.turn_number,
    ).first()
    if not current_turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    current_turn.answer = req.answer
    db.commit()

    # Build full turn history with answers
    turns = db.query(models.InterviewTurn).filter(
        models.InterviewTurn.session_id == session.id,
    ).order_by(models.InterviewTurn.turn_number).all()
    turns_data = [{"question": t.question, "answer": t.answer} for t in turns]

    try:
        result = interview_next(current_user.name, current_user.career_path, turns_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {e}")

    if result["is_final"]:
        session.status = "completed"
        session.final_feedback = result["feedback"]
        session.score = result.get("score")
        db.commit()
        return {"is_final": True, "feedback": result["feedback"], "score": result.get("score")}

    next_turn = models.InterviewTurn(
        session_id=session.id,
        question=result["question"],
        turn_number=req.turn_number + 1,
    )
    db.add(next_turn)
    db.commit()

    return {
        "is_final": False,
        "question": result["question"],
        "turn": req.turn_number + 1,
        "total": TOTAL_INTERVIEW_QUESTIONS,
    }


@router.get("/sessions")
def list_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.query(models.InterviewSession).filter(
        models.InterviewSession.user_id == current_user.id,
    ).order_by(models.InterviewSession.created_at.desc()).limit(20).all()

    return [
        {
            "id": s.id,
            "career_path": s.career_path,
            "status": s.status,
            "score": s.score,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
def get_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == session_id,
        models.InterviewSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turns = db.query(models.InterviewTurn).filter(
        models.InterviewTurn.session_id == session.id,
    ).order_by(models.InterviewTurn.turn_number).all()

    return {
        "id": session.id,
        "career_path": session.career_path,
        "status": session.status,
        "score": session.score,
        "final_feedback": session.final_feedback,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "turns": [
            {
                "turn_number": t.turn_number,
                "question": t.question,
                "answer": t.answer,
            }
            for t in turns
        ],
    }
