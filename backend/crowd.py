"""Gym crowd aggregation from check-ins."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import GymCheckin


def hour_bucket(ts: datetime) -> int:
    return ts.hour


def aggregate_by_hour_and_dow(db: Session, gym: str) -> dict[tuple[int, int], int]:
    """Returns (dow 0-6, hour) -> count."""
    rows = db.query(GymCheckin).filter(GymCheckin.gym_location == gym).all()
    counts: dict[tuple[int, int], int] = defaultdict(int)
    for c in rows:
        counts[(c.timestamp.weekday(), hour_bucket(c.timestamp))] += 1
    return dict(counts)


def quietest_windows_today(db: Session, gym: str, n: int = 3) -> tuple[list[dict], int]:
    """
    Returns up to n quietest hour windows for today's weekday, plus total check-in count for gym.
    """
    today_dow = datetime.now().weekday()
    agg = aggregate_by_hour_and_dow(db, gym)
    hours_for_today = [(h, agg.get((today_dow, h), 0)) for h in range(24)]
    hours_for_today.sort(key=lambda x: x[1])
    total_n = db.query(func.count(GymCheckin.id)).filter(GymCheckin.gym_location == gym).scalar() or 0

    if total_n == 0:
        fallback = [
            {"hour_start": 6, "hour_end": 10, "relative_busyness": "usually quieter"},
            {"hour_start": 20, "hour_end": 23, "relative_busyness": "usually quieter"},
            {"hour_start": 12, "hour_end": 14, "relative_busyness": "moderate (lunch rush elsewhere)"},
        ]
        return fallback[:n], 0

    best = hours_for_today[:n]
    out = []
    for h, cnt in best:
        out.append(
            {
                "hour_start": h,
                "hour_end": h + 1,
                "relative_busyness": "lower than other hours today" if cnt == best[0][1] else "moderate",
                "estimated_checkins_this_hour": cnt,
            }
        )
    return out, int(total_n)
