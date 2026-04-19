"""User onboarding and profile."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import User, get_db

router = APIRouter(prefix="/users", tags=["users"])

_TRAINING_SPLIT = "^(none|push_pull_legs|upper_lower|full_body|bro_split|arnold|phul)$"


class OnboardBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    weight_lbs: float = Field(..., gt=40, lt=600)
    age: int = Field(..., ge=14, le=95)
    height_cm: float = Field(..., gt=120, lt=230)
    sex: str = Field(..., pattern="^(male|female|other)$")
    goal: str = Field(..., pattern="^(cut|bulk|maintain)$")
    activity_level: str = Field(
        ...,
        pattern="^(sedentary|light|moderate|active|very_active)$",
    )
    dietary_restrictions: str | None = None
    training_split: str = Field(default="none", pattern=_TRAINING_SPLIT)


class UserPatchBody(BaseModel):
    """Partial update; only fields present in the JSON body are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    weight_lbs: float | None = Field(default=None, gt=40, lt=600)
    age: int | None = Field(default=None, ge=14, le=95)
    height_cm: float | None = Field(default=None, gt=120, lt=230)
    sex: str | None = Field(default=None, pattern="^(male|female|other)$")
    goal: str | None = Field(default=None, pattern="^(cut|bulk|maintain)$")
    activity_level: str | None = Field(
        default=None,
        pattern="^(sedentary|light|moderate|active|very_active)$",
    )
    dietary_restrictions: str | None = None
    training_split: str | None = Field(default=None, pattern=_TRAINING_SPLIT)


def _lbs_to_kg(lbs: float) -> float:
    return round(lbs * 0.453592, 2)


@router.post("/onboard")
def onboard(body: OnboardBody, db: Session = Depends(get_db)):
    u = User(
        name=body.name.strip(),
        weight_kg=_lbs_to_kg(body.weight_lbs),
        age=body.age,
        height_cm=round(float(body.height_cm), 1),
        sex=body.sex,
        goal=body.goal,
        activity_level=body.activity_level,
        dietary_restrictions=body.dietary_restrictions,
        training_split=body.training_split,
        created_at=datetime.utcnow(),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"user_id": u.id, "name": u.name, "weight_kg": u.weight_kg}


@router.patch("/{user_id}")
def patch_user(user_id: int, body: UserPatchBody, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    if "name" in updates:
        u.name = updates["name"].strip()
    if "weight_lbs" in updates:
        u.weight_kg = _lbs_to_kg(updates["weight_lbs"])
    if "goal" in updates:
        u.goal = updates["goal"]
    if "activity_level" in updates:
        u.activity_level = updates["activity_level"]
    if "dietary_restrictions" in updates:
        v = updates["dietary_restrictions"]
        if v is None:
            u.dietary_restrictions = None
        elif isinstance(v, str):
            u.dietary_restrictions = v.strip() or None
    if "age" in updates:
        u.age = updates["age"]
    if "height_cm" in updates:
        u.height_cm = round(float(updates["height_cm"]), 1)
    if "sex" in updates:
        u.sex = updates["sex"]
    if "training_split" in updates:
        u.training_split = updates["training_split"]
    db.commit()
    db.refresh(u)
    return {
        "id": u.id,
        "name": u.name,
        "weight_kg": u.weight_kg,
        "age": u.age,
        "height_cm": u.height_cm,
        "sex": u.sex,
        "goal": u.goal,
        "activity_level": u.activity_level,
        "dietary_restrictions": u.dietary_restrictions,
        "training_split": u.training_split,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": u.id,
        "name": u.name,
        "weight_kg": u.weight_kg,
        "age": u.age,
        "height_cm": u.height_cm,
        "sex": u.sex,
        "goal": u.goal,
        "activity_level": u.activity_level,
        "dietary_restrictions": u.dietary_restrictions,
        "training_split": u.training_split,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
