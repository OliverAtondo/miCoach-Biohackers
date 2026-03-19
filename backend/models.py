from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    career_path = Column(String, nullable=False)
    cv_filename = Column(String, nullable=True)
    github_links = Column(Text, nullable=True)  # JSON array stored as string
    analysis = Column(Text, nullable=True)       # Gemini analysis result
    roadmap = Column(Text, nullable=True)        # Gemini roadmap result
    onboarding_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    exercises = relationship("Exercise", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    roadmap_units = relationship("RoadmapUnit", back_populates="user", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)   # "user" or "model"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)   # Easy / Medium / Hard
    language = Column(String, nullable=False)     # python / javascript
    description = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    test_runner_code = Column(Text, nullable=False)  # code that runs tests on the solution
    user_code = Column(Text, nullable=True)
    last_output = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    solved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="exercises")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    career_path = Column(String, nullable=False)
    status = Column(String, default="active")   # active | completed
    score = Column(String, nullable=True)
    final_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    turns = relationship("InterviewTurn", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="interview_sessions")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    turn_number = Column(Integer, nullable=False)

    session = relationship("InterviewSession", back_populates="turns")


class RoadmapUnit(Base):
    __tablename__ = "roadmap_units"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    unit_index = Column(Integer, nullable=False)   # 0-based order
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)     # Topics covered in this phase
    project_description = Column(Text, nullable=False)  # Project to build
    status = Column(String, default="locked")      # locked | in_progress | completed
    github_link = Column(String, nullable=True)
    evaluation_feedback = Column(Text, nullable=True)
    evaluation_passed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="roadmap_units")
