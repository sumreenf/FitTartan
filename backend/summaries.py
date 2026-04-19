"""Target vs achieved metrics + short insights for daily/weekly summary API."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from database import FoodLog, User, WeightLog, WorkoutLog
from tools import get_daily_nutrition_target, get_weekly_summary
from workout_meta import BODY_ZONES, infer_body_parts, rough_set_kcal


def _pct_diff(achieved: float, target: float) -> float | None:
    if target <= 0:
        return None
    return round((achieved - target) / target * 100.0, 1)


def build_daily_vs_target(
    targets: dict[str, Any],
    consumed: dict[str, float],
) -> dict[str, Any]:
    tc = float(targets.get("calories", 0) or 0)
    tp = float(targets.get("protein", 0) or 0)
    tcb = float(targets.get("carbs", 0) or 0)
    tf = float(targets.get("fat", 0) or 0)
    ac = float(consumed.get("calories", 0) or 0)
    ap = float(consumed.get("protein", 0) or 0)
    acb = float(consumed.get("carbs", 0) or 0)
    af = float(consumed.get("fat", 0) or 0)

    cal_ok = tc > 0 and abs(ac - tc) <= 150
    prot_ok = tp > 0 and ap >= 0.85 * tp

    return {
        "targets": {
            "calories": tc,
            "protein": tp,
            "carbs": tcb,
            "fat": tf,
        },
        "achieved": {
            "calories": round(ac, 1),
            "protein": round(ap, 1),
            "carbs": round(acb, 1),
            "fat": round(af, 1),
        },
        "delta_pct": {
            "calories": _pct_diff(ac, tc),
            "protein": _pct_diff(ap, tp),
            "carbs": _pct_diff(acb, tcb),
            "fat": _pct_diff(af, tf),
        },
        "on_track": {
            "calories_within_range": cal_ok,
            "protein_mostly_met": prot_ok,
        },
        "remaining": {
            "calories": max(0.0, tc - ac),
            "protein": max(0.0, tp - ap),
            "carbs": max(0.0, tcb - acb),
            "fat": max(0.0, tf - af),
        },
    }


def _aggregate_food_by_day(
    db: Session, user_id: int, start: date, end: date
) -> dict[date, dict[str, float]]:
    rows = (
        db.query(FoodLog)
        .filter(FoodLog.user_id == user_id, FoodLog.date >= start, FoodLog.date <= end)
        .all()
    )
    by_day: dict[date, dict[str, float]] = defaultdict(
        lambda: {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    )
    for r in rows:
        d = r.date
        by_day[d]["calories"] += r.calories
        by_day[d]["protein"] += r.protein
        by_day[d]["carbs"] += r.carbs
        by_day[d]["fat"] += r.fat
    return dict(by_day)


def build_weekly_progress(
    db: Session,
    user_id: int,
    target_cal: float,
    target_protein: float,
    days: int = 7,
) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    by_day = _aggregate_food_by_day(db, user_id, start, end)

    near_cal_days = 0
    protein_strong_days = 0
    tracked_days = 0
    total_cal = 0.0
    total_prot = 0.0
    for d in range(days):
        d0 = start + timedelta(days=d)
        if d0 not in by_day:
            continue
        tracked_days += 1
        cals = by_day[d0]["calories"]
        p = by_day[d0]["protein"]
        total_cal += cals
        total_prot += p
        if target_cal > 0 and abs(cals - target_cal) <= 150:
            near_cal_days += 1
        if target_protein > 0 and p >= 0.85 * target_protein:
            protein_strong_days += 1

    wrows = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id, WorkoutLog.date >= start, WorkoutLog.date <= end)
        .all()
    )
    training_days = len({w.date for w in wrows})

    weights = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id, WeightLog.date >= start, WeightLog.date <= end)
        .order_by(WeightLog.date)
        .all()
    )
    w_delta = None
    if len(weights) >= 2:
        w_delta = round(weights[-1].weight_kg - weights[0].weight_kg, 3)

    n_logged_days = len(by_day)
    total_carb = sum(by_day[d]["carbs"] for d in by_day)
    total_fat = sum(by_day[d]["fat"] for d in by_day)
    avg_cal = (total_cal / n_logged_days) if n_logged_days else 0.0
    avg_prot = (total_prot / n_logged_days) if n_logged_days else 0.0
    avg_carb = (total_carb / n_logged_days) if n_logged_days else 0.0
    avg_fat = (total_fat / n_logged_days) if n_logged_days else 0.0

    tc = float(target_cal)
    tp = float(target_protein)

    daily_nutrition_trend: list[dict[str, Any]] = []
    for d in range(days):
        d0 = start + timedelta(days=d)
        rec = by_day.get(d0)
        has = d0 in by_day
        cal_ok = bool(has and tc > 0 and abs(rec["calories"] - tc) <= 150)
        prot_ok = bool(has and (tp <= 0 or rec["protein"] >= 0.85 * tp))
        daily_nutrition_trend.append(
            {
                "date": str(d0),
                "weekday": d0.strftime("%a"),
                "logged": has,
                "calories": round(rec["calories"], 0) if has else None,
                "protein": round(rec["protein"], 1) if has else None,
                "on_track": cal_ok and prot_ok,
            }
        )

    logging_streak = 0
    for i in range(days):
        d0 = end - timedelta(days=i)
        if d0 not in by_day:
            break
        logging_streak += 1

    on_track_streak = 0
    for i in range(days):
        d0 = end - timedelta(days=i)
        if d0 not in by_day:
            break
        rec = by_day[d0]
        if tc <= 0 or abs(rec["calories"] - tc) > 150:
            break
        if tp > 0 and rec["protein"] < 0.85 * tp:
            break
        on_track_streak += 1

    training_dates = {w.date for w in wrows}
    training_streak = 0
    for i in range(days):
        d0 = end - timedelta(days=i)
        if d0 not in training_dates:
            break
        training_streak += 1

    return {
        "window_days": days,
        "days_with_food_logs": n_logged_days,
        "days_near_calorie_target": near_cal_days,
        "days_high_protein": protein_strong_days,
        "avg_daily_calories": round(avg_cal, 1),
        "avg_daily_protein": round(avg_prot, 1),
        "avg_daily_carbs": round(avg_carb, 1),
        "avg_daily_fat": round(avg_fat, 1),
        "target_calories": round(tc, 1),
        "target_protein": round(tp, 1),
        "training_days": training_days,
        "weight_change_kg_in_window": w_delta,
        "daily_nutrition_trend": daily_nutrition_trend,
        "logging_streak_days": logging_streak,
        "on_track_streak_days": on_track_streak,
        "training_log_streak_days": training_streak,
    }


def weight_series(db: Session, user_id: int, days: int = 14) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id, WeightLog.date >= start, WeightLog.date <= end)
        .order_by(WeightLog.date)
        .all()
    )
    return [{"date": str(r.date), "kg": round(r.weight_kg, 2)} for r in rows]


def build_insights(
    user: User,
    weekly_api: dict[str, Any],
    daily_snap: dict[str, Any],
    weekly_prog: dict[str, Any],
) -> dict[str, list[str]]:
    """Rule-based strengths / gaps (not medical advice)."""
    goal = (user.goal or "maintain").lower()
    done: list[str] = []
    improve: list[str] = []

    # Today
    ot = daily_snap.get("on_track") or {}
    ach = daily_snap.get("achieved") or {}
    tgt = daily_snap.get("targets") or {}
    if ot.get("calories_within_range"):
        done.append("Today's calories are close to your daily target (±150 kcal band).")
    elif float(tgt.get("calories", 0) or 0) > 0:
        improve.append(
            "Today's calories are still a bit off your target — small snacks or portions can close the gap."
        )
    if ot.get("protein_mostly_met"):
        done.append("Protein is roughly on target for today.")
    elif float(tgt.get("protein", 0) or 0) > 0 and float(ach.get("protein", 0) or 0) < 0.75 * float(
        tgt.get("protein", 1)
    ):
        improve.append("Protein is below your goal range for today — consider an extra lean serving.")

    # Weekly aggregates
    madh = float(weekly_api.get("macro_adherence_pct") or 0)
    wcons = float(weekly_api.get("workout_consistency_score") or 0)
    td = int(weekly_prog.get("training_days") or 0)
    d_near = int(weekly_prog.get("days_near_calorie_target") or 0)
    d_hp = int(weekly_prog.get("days_high_protein") or 0)
    wlog = int(weekly_prog.get("days_with_food_logs") or 0)

    if madh >= 40:
        done.append("Several days this week landed near your calorie target.")
    elif wlog >= 3 and madh < 25:
        improve.append("Calorie intake varied day to day — steadier meals can make trends easier to read.")

    if d_hp >= 4:
        done.append("Most days hit a solid protein floor vs your target.")
    elif wlog >= 3 and d_hp <= 1:
        improve.append("Protein was inconsistent across days — aim to repeat yesterday's wins.")

    if wcons >= 0.5 or td >= 3:
        done.append("Training showed up multiple times this week — good consistency.")
    elif td <= 1:
        improve.append("Few structured training days logged — add one or two short sessions if possible.")

    w_delta = weekly_prog.get("weight_change_kg_in_window")
    if w_delta is not None:
        if goal == "cut" and w_delta < -0.05:
            done.append("Weight moved down this week vs your cut goal.")
        elif goal == "bulk" and w_delta > 0.05:
            done.append("Weight moved up this week vs your bulk goal.")
        elif goal == "maintain" and abs(w_delta) < 0.25:
            done.append("Weight was fairly stable this week vs maintenance.")
        elif goal == "cut" and w_delta > 0.15:
            improve.append("Weight ticked up vs a cut — double-check intake and activity when ready.")
        elif goal == "bulk" and w_delta < -0.1:
            improve.append("Weight was flat or down vs bulk — a modest calorie nudge may help if training is on.")

    note = weekly_api.get("auto_adjust_note")
    if note and isinstance(note, str) and len(note) > 10:
        improve.append(note)

    # Dedupe while preserving order
    def _uniq(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out[:6]

    return {"done_well": _uniq(done), "needs_improvement": _uniq(improve)}


def build_macro_day_pie(daily: dict[str, Any]) -> dict[str, Any]:
    """Kcal from macros logged today + remaining calories (rough plate view)."""
    ach = daily.get("achieved") or {}
    rem = daily.get("remaining") or {}
    pk = float(ach.get("protein", 0)) * 4
    ck = float(ach.get("carbs", 0)) * 4
    fk = float(ach.get("fat", 0)) * 9
    rest = max(0.0, float(rem.get("calories") or 0))
    slices = [
        {"name": "Protein", "value": round(pk, 0)},
        {"name": "Carbs", "value": round(ck, 0)},
        {"name": "Fat", "value": round(fk, 0)},
    ]
    if rest > 0:
        slices.append({"name": "Calories left", "value": round(rest, 0)})
    filtered = [s for s in slices if s["value"] > 0]
    return {"slices": filtered or [{"name": "Nothing logged yet", "value": 1}]}


def build_nutrition_hints(user: User, daily: dict[str, Any]) -> dict[str, Any]:
    rem = daily.get("remaining") or {}
    ach = daily.get("achieved") or {}
    tgt = daily.get("targets") or {}
    eat_more: list[str] = []
    ease_off: list[str] = []
    rp = float(rem.get("protein") or 0)
    rc = float(rem.get("calories") or 0)
    tc = float(tgt.get("calories") or 0)
    ac = float(ach.get("calories") or 0)
    if rp > 20:
        eat_more.append(
            "Lean protein (Greek yogurt, cottage cheese, chicken, tofu) helps close today's protein gap."
        )
    if rc > 350 and tc > 0 and ac < tc:
        eat_more.append("Whole grains, fruit, and vegetables spread through the day fit remaining calories well.")
    if tc > 0 and ac > tc * 1.08:
        ease_off.append("Fried foods and sugary drinks add calories fast — lighter swaps can rebalance tomorrow.")
    if (user.dietary_restrictions or "").strip():
        eat_more.append(f"Keep honoring your notes: {user.dietary_restrictions}.")
    return {"eat_more": eat_more[:4], "ease_off": ease_off[:3]}


def build_weekly_workout_zones(db: Session, user_id: int, days: int = 7) -> dict[str, Any]:
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id, WorkoutLog.date >= start, WorkoutLog.date <= end)
        .all()
    )
    vol = {z: 0.0 for z in BODY_ZONES}
    burn = 0.0
    for w in rows:
        burn += rough_set_kcal(w.sets, w.reps, w.weight_kg, w.exercise)
        parts = [p for p in infer_body_parts(w.exercise) if p in vol]
        if not parts:
            continue
        wkg = float(w.weight_kg) if w.weight_kg is not None else 0.0
        lift = float(w.sets) * float(w.reps) * wkg
        share = lift / len(parts)
        for p in parts:
            vol[p] += share
    tot = sum(vol.values())
    zone_pct = {z: (round(vol[z] / tot * 100, 1) if tot > 0 else 0.0) for z in vol}
    not_hit = [z for z in BODY_ZONES if vol[z] == 0]
    pie = [{"name": z.title(), "value": round(vol[z], 1)} for z in BODY_ZONES if vol[z] > 0]
    if not pie:
        pie = [{"name": "No sets logged", "value": 1}]
    return {
        "window_days": days,
        "zones_volume_index": {k: round(v, 1) for k, v in vol.items()},
        "zones_pct": zone_pct,
        "zones_not_trained_this_week": not_hit,
        "volume_pie": pie,
        "est_workout_kcal_week": round(burn, 0),
    }


def get_enriched_summary(db: Session, user_id: int) -> dict[str, Any]:
    """Single payload for GET /summary: targets vs achieved + insights + weight series."""
    user = db.get(User, user_id)
    if not user:
        return {"error": "user not found"}

    weekly = get_weekly_summary(db, user_id)
    targets = get_daily_nutrition_target(db, user_id)
    if isinstance(targets, dict) and targets.get("error"):
        return {
            "weekly": weekly,
            "targets": targets,
            "today_consumed": {},
            "insights": {"done_well": [], "needs_improvement": []},
            "profile_incomplete": False,
        }

    today = date.today()
    foods = db.query(FoodLog).filter(FoodLog.user_id == user_id, FoodLog.date == today).all()
    consumed = {
        "calories": sum(f.calories for f in foods),
        "protein": sum(f.protein for f in foods),
        "carbs": sum(f.carbs for f in foods),
        "fat": sum(f.fat for f in foods),
    }

    daily = build_daily_vs_target(targets, consumed)
    wp = build_weekly_progress(
        db,
        user_id,
        float(targets.get("calories", 0) or 0),
        float(targets.get("protein", 0) or 0),
    )
    insights = build_insights(user, weekly, daily, wp)
    ws = weight_series(db, user_id, 14)
    wz = build_weekly_workout_zones(db, user_id)
    mp = build_macro_day_pie(daily)
    nh = build_nutrition_hints(user, daily)
    profile_incomplete = user.age is None or user.height_cm is None or user.sex is None

    return {
        "weekly": weekly,
        "targets": targets,
        "today_consumed": consumed,
        "daily": daily,
        "weekly_progress": wp,
        "insights": insights,
        "weight_series": ws,
        "workout_zones": wz,
        "macro_day_pie": mp,
        "nutrition_hints": nh,
        "profile_incomplete": profile_incomplete,
    }
