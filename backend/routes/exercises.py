from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
import models
from auth import get_current_user
from services.ai import generate_exercise, evaluate_submission
from services.code_runner import run_code

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


class NewExerciseRequest(BaseModel):
    language: str = "python"      # "python" | "javascript"
    difficulty: str = "Easy"      # "Easy" | "Medium" | "Hard"


class RunCodeRequest(BaseModel):
    exercise_id: int
    code: str


class SubmitRequest(BaseModel):
    exercise_id: int
    code: str


class ExerciseOut(BaseModel):
    id: int
    title: str
    difficulty: str
    language: str
    topic: str = ""
    description: str
    examples: str       # JSON string
    constraints: str    # JSON string
    starter_code: str
    test_runner_code: str
    user_code: Optional[str]
    last_output: Optional[str]
    feedback: Optional[str]
    solved: bool

    class Config:
        from_attributes = True


@router.post("/generate", response_model=ExerciseOut)
async def generate(
    req: NewExerciseRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.onboarding_complete:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    if req.language not in ("python", "javascript"):
        raise HTTPException(status_code=400, detail="Language must be python or javascript")
    if req.difficulty not in ("Easy", "Medium", "Hard"):
        raise HTTPException(status_code=400, detail="Difficulty must be Easy, Medium, or Hard")

    # Get previous exercise titles to avoid repetition
    prev = db.query(models.Exercise.title).filter(
        models.Exercise.user_id == current_user.id
    ).all()
    previous_titles = [r.title for r in prev]

    try:
        data = generate_exercise(
            name=current_user.name,
            career_path=current_user.career_path,
            analysis=current_user.analysis or "",
            language=req.language,
            difficulty=req.difficulty,
            previous_titles=previous_titles,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate exercise: {e}")

    import json
    exercise = models.Exercise(
        user_id=current_user.id,
        title=data.get("title", "Untitled"),
        difficulty=data.get("difficulty", req.difficulty),
        language=req.language,
        description=data.get("description", ""),
        starter_code=data.get("starter_code", ""),
        test_runner_code=data.get("test_runner_code", ""),
        user_code=data.get("starter_code", ""),
    )
    # Store extras as JSON in description field extension
    exercise.description = data.get("description", "")
    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    # Attach parsed fields for the response
    exercise.__dict__["topic"] = data.get("topic", "")
    exercise.__dict__["examples"] = json.dumps(data.get("examples", []))
    exercise.__dict__["constraints"] = json.dumps(data.get("constraints", []))
    return exercise


@router.post("/run")
async def run(
    req: RunCodeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == req.exercise_id,
        models.Exercise.user_id == current_user.id,
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Merge user's solution into the test runner
    full_code = _merge_code(req.code, exercise.test_runner_code, exercise.language)
    output, success = run_code(exercise.language, full_code)

    # Persist user code and output
    exercise.user_code = req.code
    exercise.last_output = output
    db.commit()

    return {"output": output, "success": success}


@router.post("/submit")
async def submit(
    req: SubmitRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == req.exercise_id,
        models.Exercise.user_id == current_user.id,
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Run code one final time
    full_code = _merge_code(req.code, exercise.test_runner_code, exercise.language)
    output, success = run_code(exercise.language, full_code)

    # Get Gemini feedback
    feedback = evaluate_submission(
        name=current_user.name,
        exercise_title=exercise.title,
        exercise_description=exercise.description,
        language=exercise.language,
        user_code=req.code,
        execution_output=output,
        passed=success,
    )

    exercise.user_code = req.code
    exercise.last_output = output
    exercise.feedback = feedback
    exercise.solved = success
    db.commit()

    return {"output": output, "success": success, "feedback": feedback}


@router.get("/history", response_model=List[dict])
def history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercises = db.query(models.Exercise).filter(
        models.Exercise.user_id == current_user.id
    ).order_by(models.Exercise.created_at.desc()).limit(20).all()

    return [
        {
            "id": e.id,
            "title": e.title,
            "difficulty": e.difficulty,
            "language": e.language,
            "solved": e.solved,
        }
        for e in exercises
    ]


@router.get("/{exercise_id}", response_model=dict)
def get_exercise(
    exercise_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id,
        models.Exercise.user_id == current_user.id,
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {
        "id": exercise.id,
        "title": exercise.title,
        "difficulty": exercise.difficulty,
        "language": exercise.language,
        "description": exercise.description,
        "starter_code": exercise.starter_code,
        "test_runner_code": exercise.test_runner_code,
        "user_code": exercise.user_code,
        "last_output": exercise.last_output,
        "feedback": exercise.feedback,
        "solved": exercise.solved,
    }


def _merge_code(user_code: str, test_runner: str, language: str) -> str:
    """Replace the stub function in the test runner with the user's actual code."""
    # The test runner contains a stub; we prepend user's code so their definition overrides it
    if language == "python":
        return user_code + "\n\n" + _strip_stub_python(test_runner, user_code)
    else:
        return user_code + "\n\n" + _strip_stub_js(test_runner)


def _strip_stub_python(test_runner: str, user_code: str = "") -> str:
    """Strip only the stub functions (those defined in user_code) from the test runner.

    Helper functions defined only in the test runner (e.g. lists_are_close) are preserved.
    """
    import re
    # Collect function names the user has defined — only strip those from the runner
    stub_names = set(re.findall(r"^def (\w+)\(", user_code, re.MULTILINE))

    lines = test_runner.split("\n")
    result = []
    in_block = False

    for line in lines:
        if in_block:
            # Exit block when we hit a non-indented, non-empty line
            if line.strip() and not line[0].isspace():
                in_block = False
            else:
                continue

        if stub_names:
            # Only strip functions whose name appears in the user's solution
            m = re.match(r"^def (\w+)\(", line)
            if m and m.group(1) in stub_names:
                in_block = True
                continue
        else:
            # Fallback: strip all top-level defs (safe default when no user code)
            if line.startswith("def ") or line.startswith("class "):
                in_block = True
                continue

        result.append(line)

    return "\n".join(result)


def _strip_stub_js(test_runner: str) -> str:
    """Remove stub function from JS test runner."""
    lines = test_runner.split("\n")
    result, brace_depth, in_stub = [], 0, False
    for line in lines:
        if not in_stub and ("function " in line or "const " in line or "let " in line) and "{" in line:
            if "// stub" in line or "// placeholder" in line:
                in_stub = True
                brace_depth = line.count("{") - line.count("}")
                continue
        if in_stub:
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                in_stub = False
            continue
        result.append(line)
    return "\n".join(result)
