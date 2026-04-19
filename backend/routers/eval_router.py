"""Hackathon eval dashboard metrics."""

from __future__ import annotations

import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import (
    CrowdPredictionEval,
    FoodLog,
    GymCheckin,
    MealSuggestionRating,
    OverloadSuggestionLog,
    User,
    WeightLog,
    WorkoutLog,
    get_db,
)
from tools import get_daily_nutrition_target

router = APIRouter(prefix="/eval", tags=["eval"])


class MealRateBody(BaseModel):
    user_id: int
    suggestion_text: str
    rating: int = Field(..., ge=-1, le=1)


@router.post("/meal-rating")
def meal_rating(body: MealRateBody, db: Session = Depends(get_db)):
    if not db.get(User, body.user_id):
        raise HTTPException(404, "User not found")
    r = MealSuggestionRating(
        user_id=body.user_id,
        suggestion_text=body.suggestion_text[:4000],
        rating=body.rating,
    )
    db.add(r)
    db.commit()
    return {"ok": True}


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """Aggregate eval table + heuristics for dashboard."""
    overload_rows = db.query(OverloadSuggestionLog).order_by(desc(OverloadSuggestionLog.created_at)).limit(200).all()
    matched = [x for x in overload_rows if x.matched is True]
    attempted = [x for x in overload_rows if x.matched is not None]
    overload_accuracy = (len(matched) / len(attempted)) if attempted else None

    ratings = db.query(MealSuggestionRating).all()
    up = sum(1 for r in ratings if r.rating > 0)
    down = sum(1 for r in ratings if r.rating < 0)
    meal_net = up - down

    crowd_rows = db.query(CrowdPredictionEval).all()
    crowd_samples = len(crowd_rows)

    # Calorie adherence: days within ±150 of target for users with logs
    end = date.today()
    start = end - timedelta(days=30)
    users = [u.id for u in db.query(User).all()]
    adherence_days = 0
    total_days = 0
    for uid in users[:50]:
        tgt = get_daily_nutrition_target(db, uid)
        cal_t = float(tgt.get("calories", 0) or 0)
        if cal_t <= 0:
            continue
        foods = (
            db.query(FoodLog)
            .filter(FoodLog.user_id == uid, FoodLog.date >= start, FoodLog.date <= end)
            .all()
        )
        by_day: dict[date, float] = {}
        for f in foods:
            by_day[f.date] = by_day.get(f.date, 0) + f.calories
        for d, cals in by_day.items():
            total_days += 1
            if abs(cals - cal_t) <= 150:
                adherence_days += 1
    calorie_adherence_pct = (adherence_days / total_days * 100) if total_days else None

    # Weight trend alignment: compare last 7d delta vs goal direction
    alignment_scores = []
    for uid in users[:50]:
        u = db.get(User, uid)
        if not u:
            continue
        ws = (
            db.query(WeightLog)
            .filter(WeightLog.user_id == uid)
            .order_by(WeightLog.date)
            .all()
        )
        if len(ws) < 2:
            continue
        delta = ws[-1].weight_kg - ws[0].weight_kg
        if u.goal == "cut" and delta < -0.05:
            alignment_scores.append(1)
        elif u.goal == "bulk" and delta > 0.05:
            alignment_scores.append(1)
        elif u.goal == "maintain" and abs(delta) < 0.3:
            alignment_scores.append(1)
        else:
            alignment_scores.append(0)
    weight_alignment = sum(alignment_scores) / len(alignment_scores) if alignment_scores else None

    return {
        "overload_suggestion_accuracy": overload_accuracy,
        "overload_samples": len(attempted),
        "meal_ratings_up": up,
        "meal_ratings_down": down,
        "meal_rating_net": meal_net,
        "crowd_eval_samples": crowd_samples,
        "calorie_adherence_pct": calorie_adherence_pct,
        "calorie_adherence_days": adherence_days,
        "calorie_days_tracked": total_days,
        "weight_trend_alignment_pct": (weight_alignment * 100) if weight_alignment is not None else None,
        "weight_alignment_users": len(alignment_scores),
    }


@router.post("/crowd-snapshot")
def crowd_snapshot(db: Session = Depends(get_db)):
    """Store a simple crowd prediction snapshot for eval (optional)."""
    gyms = ["CUC Gym", "Tepper Gym", "Swimming pool"]
    today_dow = date.today().weekday()
    for g in gyms:
        rows = db.query(GymCheckin).filter(GymCheckin.gym_location == g).all()
        by_hour: dict[int, int] = {}
        for c in rows:
            if c.timestamp.weekday() != today_dow:
                continue
            h = c.timestamp.hour
            by_hour[h] = by_hour.get(h, 0) + 1
        peak_hour = max(by_hour, key=by_hour.get) if by_hour else None
        quiet = sorted(by_hour, key=lambda h: by_hour[h])[:3] if by_hour else [7, 14, 21]
        ev = CrowdPredictionEval(
            gym=g,
            day_of_week=today_dow,
            predicted_quiet_hours=json.dumps(quiet),
            actual_peak_hour=peak_hour,
            checkin_count=len(rows),
        )
        db.add(ev)
    db.commit()
    return {"ok": True, "snapshots": len(gyms)}
