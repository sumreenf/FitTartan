"""Gym check-in and crowd queries."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from crowd import quietest_windows_today
from database import GymCheckin, User, get_db

router = APIRouter(tags=["crowd"])


class CheckinBody(BaseModel):
    user_id: int
    gym_location: str = Field(..., min_length=1, max_length=128)


@router.post("/checkin")
def checkin(body: CheckinBody, db: Session = Depends(get_db)):
    if not db.get(User, body.user_id):
        raise HTTPException(404, "User not found")
    c = GymCheckin(
        user_id=body.user_id,
        timestamp=datetime.utcnow(),
        gym_location=body.gym_location.strip(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "timestamp": c.timestamp.isoformat()}


@router.get("/crowd/{gym}")
def crowd(gym: str, db: Session = Depends(get_db)):
    windows, n = quietest_windows_today(db, gym, n=3)
    return {
        "gym": gym,
        "quiet_windows": windows,
        "based_on_checkins": n,
        "note": "Quieter before 10am and after 8pm is a common heuristic on cold start.",
    }
