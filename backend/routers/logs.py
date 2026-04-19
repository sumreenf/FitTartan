"""Workout, food, and weight logging."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database import FoodLog, User, WeightLog, WorkoutLog, get_db
from tools import log_food_with_macros
from workout_meta import EXERCISE_CATALOG

router = APIRouter(prefix="/logs", tags=["logs"])


class WorkoutBody(BaseModel):
    user_id: int
    exercise: str = ""
    sets: int = Field(default=1, ge=1, le=50)
    reps: int = Field(default=1, ge=1, le=200)
    weight_kg: float | None = Field(default=None)

    @field_validator("weight_kg")
    @classmethod
    def weight_when_present(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if v <= 0 or v >= 600:
            raise ValueError("weight_kg must be between 0 and 600 kg when provided")
        return v


class FoodBody(BaseModel):
    user_id: int
    item_name: str
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None


class WeightBody(BaseModel):
    user_id: int
    weight_kg: float = Field(..., gt=20, lt=400)
    log_date: date | None = None


@router.get("/exercises")
def exercise_catalog():
    """Preset lifts for logging UI (each maps to muscle zones on the dashboard)."""
    return {"exercises": EXERCISE_CATALOG}


@router.delete("/workout/{workout_id}")
def delete_workout(
    workout_id: int,
    user_id: int = Query(..., ge=1, description="Owner user id (must match the log row)."),
    db: Session = Depends(get_db),
):
    w = db.get(WorkoutLog, workout_id)
    if not w or w.user_id != user_id:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(w)
    db.commit()
    return {"ok": True, "id": workout_id}


@router.post("/workout")
def log_workout_ep(body: WorkoutBody, db: Session = Depends(get_db)):
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    ex = (body.exercise or "").strip() or "Session"
    w = WorkoutLog(
        user_id=body.user_id,
        date=date.today(),
        exercise=ex,
        sets=body.sets,
        reps=body.reps,
        weight_kg=body.weight_kg,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"id": w.id, "message": "Logged (training changes are suggestions only). "}


@router.get("/workouts/{user_id}")
def list_workouts(
    user_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    rows = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id)
        .order_by(WorkoutLog.date.desc(), WorkoutLog.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "workouts": [
            {
                "id": r.id,
                "date": str(r.date),
                "exercise": r.exercise,
                "sets": r.sets,
                "reps": r.reps,
                "weight_kg": r.weight_kg,
            }
            for r in rows
        ]
    }


@router.post("/food")
def log_food_ep(body: FoodBody, db: Session = Depends(get_db)):
    from tools import log_food as lf

    if not db.get(User, body.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if (
        body.calories is not None
        and body.protein is not None
        and body.carbs is not None
        and body.fat is not None
    ):
        return log_food_with_macros(
            db,
            body.user_id,
            body.item_name,
            body.calories,
            body.protein,
            body.carbs,
            body.fat,
        )
    return lf(db, body.user_id, body.item_name)


@router.post("/weight")
def log_weight_ep(body: WeightBody, db: Session = Depends(get_db)):
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    d = body.log_date or date.today()
    wl = WeightLog(user_id=body.user_id, date=d, weight_kg=body.weight_kg)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return {"id": wl.id, "date": str(wl.date), "weight_kg": wl.weight_kg}
