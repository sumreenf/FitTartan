"""Seed demo user Alex with plateau + macro gap for hackathon demo."""

from __future__ import annotations

import random
import sys
from datetime import date, datetime, timedelta

from sqlalchemy.exc import OperationalError

from database import (
    Base,
    FoodLog,
    GymCheckin,
    OverloadSuggestionLog,
    SessionLocal,
    User,
    WeightLog,
    WorkoutLog,
    engine,
)


def _reset_schema() -> None:
    """Recreate all tables without deleting the .db file (avoids WinError 32 when file is open)."""
    engine.dispose()
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except OperationalError as e:
        print(
            "Could not reset the database (SQLite may be locked). "
            "Stop the API server (uvicorn) or any process using fittartan.db, then run seed.py again.",
            file=sys.stderr,
        )
        raise SystemExit(1) from e


def main():
    _reset_schema()
    db = SessionLocal()

    alex = User(
        name="Alex",
        weight_kg=82.0,
        age=22,
        height_cm=178.0,
        sex="male",
        goal="bulk",
        activity_level="moderate",
        dietary_restrictions="none",
        training_split="push_pull_legs",
    )
    db.add(alex)
    db.commit()
    db.refresh(alex)
    uid = alex.id

    today = date.today()
    # Flat weight trend (bulk goal)
    for i in range(21):
        d = today - timedelta(days=20 - i)
        noise = random.uniform(-0.15, 0.15)
        db.add(WeightLog(user_id=uid, date=d, weight_kg=82.0 + noise))
    db.commit()

    # Bench plateau: same weight ~3 weeks
    bench_weight = 80.0
    for week in range(3):
        for session in range(2):
            d = today - timedelta(days=14 - week * 7 - session * 3)
            reps = 5 if session == 0 else 4
            db.add(
                WorkoutLog(
                    user_id=uid,
                    date=d,
                    exercise="bench press",
                    sets=4,
                    reps=reps,
                    weight_kg=bench_weight,
                )
            )
    db.add(
        WorkoutLog(
            user_id=uid,
            date=today - timedelta(days=1),
            exercise="squat",
            sets=4,
            reps=6,
            weight_kg=110.0,
        )
    )
    db.commit()

    # Food logs: ~140g protein vs ~180g target
    for i in range(18):
        d = today - timedelta(days=17 - i)
        db.add(
            FoodLog(
                user_id=uid,
                date=d,
                item_name="Demo meal",
                calories=2200,
                protein=140,
                carbs=240,
                fat=70,
            )
        )
    db.commit()

    # Sparse gym check-ins for crowd (locations match CrowdMeter / agent defaults)
    crowd_locations = ["CUC Gym", "Tepper Gym", "Swimming pool"]
    crowd_weights = [18, 12, 10]
    for _ in range(40):
        loc = random.choices(crowd_locations, weights=crowd_weights, k=1)[0]
        db.add(
            GymCheckin(
                user_id=uid,
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(0, 200)),
                gym_location=loc,
            )
        )
    db.commit()

    # Overload eval row
    db.add(
        OverloadSuggestionLog(
            user_id=uid,
            exercise="bench press",
            suggested_weight_kg=82.5,
            session_note="demo suggestion",
            next_session_weight_kg=bench_weight,
            matched=False,
        )
    )
    db.commit()
    db.close()

    print("Seeded user_id=", uid, "name=Alex")


if __name__ == "__main__":
    main()
