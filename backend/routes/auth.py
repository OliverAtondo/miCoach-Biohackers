from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import json
import os
import aiofiles

from database import get_db
import models
import schemas
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


@router.post("/register", response_model=schemas.TokenResponse)
async def register(
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    career_path: str = Form(...),
    onboarding_answers: str = Form(None),
    github_links: str = Form("[]"),  # JSON array string
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save CV
    cv_bytes = await cv.read()
    if not cv.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="CV must be a PDF file")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_filename = f"{email.replace('@', '_').replace('.', '_')}_{cv.filename}"
    cv_path = os.path.join(UPLOAD_DIR, safe_filename)
    async with aiofiles.open(cv_path, "wb") as f:
        await f.write(cv_bytes)

    user = models.User(
        email=email,
        name=name,
        hashed_password=hash_password(password),
        career_path=career_path,
        onboarding_answers=onboarding_answers,
        cv_filename=safe_filename,
        github_links=github_links,
        onboarding_complete=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return {"access_token": token}


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
