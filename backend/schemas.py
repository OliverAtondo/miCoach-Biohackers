from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    career_path: str
    github_links: List[str] = []


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    career_path: str
    github_links: Optional[str]
    onboarding_answers: Optional[str]
    analysis: Optional[str]
    roadmap: Optional[str]
    onboarding_complete: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageIn(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
