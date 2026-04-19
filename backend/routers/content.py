"""Menu and weekly summary endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from daily_motivation import get_daily_motivation
from database import User, get_db
from scraper import get_cached_menu
from summaries import get_enriched_summary
from tools import get_meal_suggestions

router = APIRouter(tags=["content"])


@router.get("/motivation/daily")
def motivation_daily(
    user_id: int = Query(..., ge=1, description="User id (for stable daily pick)."),
    db: Session = Depends(get_db),
):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return get_daily_motivation(user_id)


@router.get("/menu/today")
def menu_today(db: Session = Depends(get_db)):
    items = get_cached_menu(db)
    return {
        "date": str(date.today()),
        "items": [
            {
                "name": i.name,
                "location": i.location,
                "meal_period": i.meal_period,
                "macros_ranges": {
                    "calories": f"~{i.calories * 0.88:.0f}–{i.calories * 1.12:.0f} kcal",
                    "protein": f"~{i.protein * 0.88:.0f}–{i.protein * 1.12:.0f} g",
                    "carbs": f"~{i.carbs * 0.88:.0f}–{i.carbs * 1.12:.0f} g",
                    "fat": f"~{i.fat * 0.88:.0f}–{i.fat * 1.12:.0f} g",
                },
            }
            for i in items
        ],
    }


@router.get("/meals/suggestions/{user_id}")
def meal_suggestions(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return get_meal_suggestions(db, user_id)


@router.get("/summary/{user_id}")
def summary(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return get_enriched_summary(db, user_id)
