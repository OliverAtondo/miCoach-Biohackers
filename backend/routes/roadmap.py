from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
import models
from auth import get_current_user
from services.ai import parse_roadmap_into_units, evaluate_github_for_unit
from services.github import fetch_repo_summary

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


class SubmitGithubRequest(BaseModel):
    github_link: str


@router.post("/initialize")
async def initialize_units(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse the user's roadmap into structured units and persist them. Idempotent."""
    if not current_user.onboarding_complete or not current_user.roadmap:
        raise HTTPException(status_code=400, detail="Complete onboarding first")

    existing = (
        db.query(models.RoadmapUnit)
        .filter(models.RoadmapUnit.user_id == current_user.id)
        .count()
    )
    if existing > 0:
        units = (
            db.query(models.RoadmapUnit)
            .filter(models.RoadmapUnit.user_id == current_user.id)
            .order_by(models.RoadmapUnit.unit_index)
            .all()
        )
        return [_unit_to_dict(u) for u in units]

    units_data = parse_roadmap_into_units(current_user.roadmap, current_user.career_path)

    db_units = []
    for i, u in enumerate(units_data):
        status = "in_progress" if i == 0 else "locked"
        db_unit = models.RoadmapUnit(
            user_id=current_user.id,
            unit_index=i,
            title=u.get("title", f"Phase {i + 1}"),
            description=u.get("description", ""),
            project_description=u.get("project_description", ""),
            status=status,
        )
        db.add(db_unit)
        db_units.append(db_unit)

    db.commit()
    for u in db_units:
        db.refresh(u)

    return [_unit_to_dict(u) for u in db_units]


@router.get("/units")
def get_units(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all roadmap units for the current user."""
    units = (
        db.query(models.RoadmapUnit)
        .filter(models.RoadmapUnit.user_id == current_user.id)
        .order_by(models.RoadmapUnit.unit_index)
        .all()
    )
    return [_unit_to_dict(u) for u in units]


@router.post("/units/{unit_id}/submit")
async def submit_github(
    unit_id: int,
    body: SubmitGithubRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a GitHub link for a roadmap unit. AI evaluates if the user can advance."""
    unit = (
        db.query(models.RoadmapUnit)
        .filter(
            models.RoadmapUnit.id == unit_id,
            models.RoadmapUnit.user_id == current_user.id,
        )
        .first()
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.status == "locked":
        raise HTTPException(status_code=400, detail="Complete the previous unit first")

    # Fetch GitHub data
    github_data = await fetch_repo_summary(body.github_link)
    if "error" in github_data:
        raise HTTPException(status_code=400, detail=f"Could not fetch GitHub repo: {github_data['error']}")

    # AI evaluation
    result = evaluate_github_for_unit(
        name=current_user.name,
        career_path=current_user.career_path,
        unit_title=unit.title,
        unit_description=unit.description,
        project_description=unit.project_description,
        github_data=github_data,
    )

    unit.github_link = body.github_link
    unit.evaluation_feedback = result.get("feedback", "")
    unit.evaluation_passed = result.get("passed", False)

    if result.get("passed"):
        unit.status = "completed"
        # Unlock next unit
        next_unit = (
            db.query(models.RoadmapUnit)
            .filter(
                models.RoadmapUnit.user_id == current_user.id,
                models.RoadmapUnit.unit_index == unit.unit_index + 1,
            )
            .first()
        )
        if next_unit and next_unit.status == "locked":
            next_unit.status = "in_progress"

    db.commit()
    db.refresh(unit)

    return {
        "unit": _unit_to_dict(unit),
        "passed": result.get("passed", False),
        "score": result.get("score", ""),
        "feedback": result.get("feedback", ""),
    }


def _unit_to_dict(u: models.RoadmapUnit) -> dict:
    return {
        "id": u.id,
        "unit_index": u.unit_index,
        "title": u.title,
        "description": u.description,
        "project_description": u.project_description,
        "status": u.status,
        "github_link": u.github_link,
        "evaluation_feedback": u.evaluation_feedback,
        "evaluation_passed": u.evaluation_passed,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
