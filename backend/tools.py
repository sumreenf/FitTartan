"""Agent tools — standalone functions + registration metadata."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from rapidfuzz import fuzz, process
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from crowd import quietest_windows_today
from database import (
    DiningMenuItem,
    FoodLog,
    GymCheckin,
    OverloadSuggestionLog,
    User,
    WeightLog,
    WorkoutLog,
)
from scraper import get_cached_menu
from usda import estimate_macros_for_label, to_macro_ranges

ACTIVITY_MULT = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def mifflin_st_jeor_bmr(weight_kg: float, height_cm: float, age: int, sex: str | None) -> float:
    """Mifflin–St Jeor BMR (kcal/day). ``sex``: male | female | other | None."""
    s = (sex or "other").strip().lower()
    base = 10 * float(weight_kg) + 6.25 * float(height_cm) - 5 * int(age)
    if s == "male":
        return base + 5
    if s == "female":
        return base - 161
    # other / unknown: average of male vs female offset
    return base + (5 - 161) / 2


def log_workout(
    db: Session,
    user_id: int,
    exercise: str,
    sets: int,
    reps: int,
    weight: float | None = None,
) -> dict[str, Any]:
    w = WorkoutLog(
        user_id=user_id,
        date=date.today(),
        exercise=(exercise or "").strip() or "Session",
        sets=sets,
        reps=reps,
        weight_kg=weight,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"ok": True, "workout_id": w.id, "message": "Workout logged (suggestion only — adjust to how you feel). "}


def get_progressive_overload_suggestion(db: Session, user_id: int, exercise: str) -> dict[str, Any]:
    ex = exercise.strip().lower()
    rows = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id, func.lower(WorkoutLog.exercise) == ex)
        .order_by(desc(WorkoutLog.date))
        .limit(3)
        .all()
    )
    if not rows:
        return {
            "suggestion": "Log a few sessions for this lift first — then I can suggest small progressions.",
            "reasoning": "No prior sessions found.",
            "confidence": 0.3,
        }

    last_w = rows[0].weight_kg
    if last_w is None:
        return {
            "suggestion": "Your latest log has no weight — add load when you can if you want barbell-style progression tips.",
            "reasoning": "Progression heuristics need a recorded weight on the last session.",
            "confidence": 0.35,
        }
    sessions = list(reversed(rows))
    hit_reps = all(s.reps >= sessions[-1].reps for s in sessions[-2:]) if len(sessions) >= 2 else False
    failed_last = len(rows) >= 2 and rows[0].reps < rows[1].reps

    cap_next = last_w * 1.10  # max +10% vs last session weight for weekly cap messaging

    if failed_last:
        sugg = min(last_w, last_w * 0.9)
        suggestion = f"Consider repeating ~{sugg:.1f}–{last_w:.1f} kg (rough range) or reducing load ~10% until reps feel solid."
        reasoning = "Last session looked tougher than the one before — prioritize clean reps."
        confidence = 0.55
    elif len(sessions) >= 2 and hit_reps:
        sugg = min(last_w + 2.5, cap_next)
        suggestion = (
            f"If the last two sessions felt smooth, try adding a small step — about "
            f"~{last_w:.1f}–{sugg:.1f} kg total range, or one more rep at the same weight (not both at once)."
        )
        reasoning = "Two consecutive sessions hit target reps — small overload is reasonable."
        confidence = 0.65
    else:
        suggestion = f"Hold around ~{last_w * 0.95:.1f}–{last_w * 1.05:.1f} kg until form stays consistent across sets."
        reasoning = "Need one more consistent session to judge progression."
        confidence = 0.5

    log = OverloadSuggestionLog(
        user_id=user_id,
        exercise=exercise,
        suggested_weight_kg=min(last_w * 1.025, cap_next),
        session_note=suggestion[:500],
    )
    db.add(log)
    db.commit()

    return {"suggestion": suggestion, "reasoning": reasoning, "confidence": confidence}


def log_food(db: Session, user_id: int, item_name: str) -> dict[str, Any]:
    menu = get_cached_menu(db)
    names = [m.name for m in menu]
    match_name = None
    macros = None
    source = "usda_estimate"

    if names:
        best = process.extractOne(item_name, names, scorer=fuzz.WRatio)
        if best and best[1] >= 70:
            match_name = best[0]
            mitem = next(x for x in menu if x.name == match_name)
            macros = {
                "calories": mitem.calories,
                "protein": mitem.protein,
                "carbs": mitem.carbs,
                "fat": mitem.fat,
            }
            source = f"cmu_menu:{mitem.location}"

    if macros is None:
        macros, source = estimate_macros_for_label(item_name)

    ranges = to_macro_ranges(macros)
    fl = FoodLog(
        user_id=user_id,
        date=date.today(),
        item_name=item_name.strip(),
        calories=macros["calories"],
        protein=macros["protein"],
        carbs=macros["carbs"],
        fat=macros["fat"],
    )
    db.add(fl)
    db.commit()

    return {
        "logged": True,
        "item": item_name,
        "macros_point": macros,
        "macros_ranges": ranges,
        "source": source,
    }


def log_food_with_macros(
    db: Session,
    user_id: int,
    item_name: str,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
) -> dict[str, Any]:
    """Log food with explicit macros (e.g. CMU meal combo totals from menu math)."""
    macros = {
        "calories": float(calories),
        "protein": float(protein),
        "carbs": float(carbs),
        "fat": float(fat),
    }
    ranges = to_macro_ranges(macros)
    fl = FoodLog(
        user_id=user_id,
        date=date.today(),
        item_name=item_name.strip()[:500],
        calories=macros["calories"],
        protein=macros["protein"],
        carbs=macros["carbs"],
        fat=macros["fat"],
    )
    db.add(fl)
    db.commit()

    return {
        "logged": True,
        "item": item_name,
        "macros_point": macros,
        "macros_ranges": ranges,
        "source": "combo_selection",
    }


def _seven_day_weight_change_kg(db: Session, user_id: int) -> float | None:
    end = date.today()
    start = end - timedelta(days=7)
    rows = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id, WeightLog.date >= start, WeightLog.date <= end)
        .order_by(WeightLog.date)
        .all()
    )
    if len(rows) < 2:
        return None
    return rows[-1].weight_kg - rows[0].weight_kg


def get_daily_nutrition_target(db: Session, user_id: int) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        return {"error": "user not found"}

    height_cm = float(user.height_cm) if user.height_cm is not None else 175.0
    age = int(user.age) if user.age is not None else 25
    bmr = mifflin_st_jeor_bmr(user.weight_kg, height_cm, age, user.sex)
    mult = ACTIVITY_MULT.get(user.activity_level, 1.55)
    tdee = bmr * mult

    adj = 0.0
    reason = "Maintenance-aligned based on goal."
    if user.goal == "cut":
        adj = -400
        reason = "Moderate deficit for sustainable fat loss (~400 kcal under estimated TDEE)."
    elif user.goal == "bulk":
        adj = 300
        reason = "Small surplus for lean gain (~300 kcal over estimated TDEE)."
    elif user.goal == "maintain":
        adj = 0

    delta_w = _seven_day_weight_change_kg(db, user_id)
    adjustment_reason = reason
    if delta_w is not None:
        if user.goal == "bulk" and delta_w < -0.2:
            adj += 150
            adjustment_reason += " 7-day trend looks flat/down vs bulk — bumped target ~+150 kcal."
        elif user.goal == "bulk" and abs(delta_w) < 0.15:
            adj += 150
            adjustment_reason += " 7-day trend is nearly flat vs bulk — nudged target ~+150 kcal (suggestion)."
        elif user.goal == "cut" and delta_w > 0.2:
            adj -= 100
            adjustment_reason += " 7-day trend drifting up vs cut — nudged target ~−100 kcal."
        elif user.goal == "maintain" and abs(delta_w) > 0.3:
            adjustment_reason += " Weight drifting — small tweak suggested; monitor another week."

    target_cal = max(1200.0, tdee + adj)
    protein_g = max(1.6 * user.weight_kg, 0.8 * user.weight_kg * 2)
    fat_g = 0.25 * target_cal / 9
    carb_g = max(0.0, (target_cal - protein_g * 4 - fat_g * 9) / 4)

    return {
        "calories": round(target_cal, -1),
        "protein": round(protein_g, 0),
        "carbs": round(carb_g, 0),
        "fat": round(fat_g, 0),
        "macros_as_ranges": {
            "protein": f"~{protein_g * 0.88:.0f}–{protein_g * 1.12:.0f} g",
            "carbs": f"~{carb_g * 0.88:.0f}–{carb_g * 1.12:.0f} g",
            "fat": f"~{fat_g * 0.88:.0f}–{fat_g * 1.12:.0f} g",
            "calories": f"~{target_cal * 0.95:.0f}–{target_cal * 1.05:.0f} kcal",
        },
        "adjustment_reason": adjustment_reason,
        "bmr_estimate_kcal": round(bmr, 0),
        "tdee_estimate_kcal": round(tdee, 0),
        "activity_factor": mult,
        "biometrics_used": {
            "age": age,
            "height_cm": round(height_cm, 1),
            "sex": user.sex or "other",
            "weight_kg": round(float(user.weight_kg), 2),
        },
    }


def _today_food_totals(db: Session, user_id: int) -> dict[str, float]:
    today = date.today()
    rows = db.query(FoodLog).filter(FoodLog.user_id == user_id, FoodLog.date == today).all()
    tot = defaultdict(float)
    for r in rows:
        tot["calories"] += r.calories
        tot["protein"] += r.protein
        tot["carbs"] += r.carbs
        tot["fat"] += r.fat
    return dict(tot)


def _budget_cook_options(rem: dict[str, float]) -> list[dict[str, Any]]:
    """
    Budget-friendly cook-at-home ideas with rough ingredient costs (discount-grocery style).
    Costs are estimates only, not shopping quotes.
    """
    _ = rem  # reserved for future scaling to remaining macros
    templates: list[dict[str, Any]] = [
        {
            "title": "Egg & rice bowl",
            "subtitle": "Stovetop bowl — cheap, filling protein",
            "ingredients": [
                {"item": "Eggs", "qty": "4 large", "est_cost_usd": 1.0},
                {"item": "Long-grain rice (dry)", "qty": "~⅓ cup dry → ~1 cup cooked", "est_cost_usd": 0.35},
                {"item": "Frozen mixed vegetables", "qty": "1 cup", "est_cost_usd": 0.45},
                {"item": "Soy sauce / hot sauce", "qty": "pantry staples", "est_cost_usd": 0.15},
            ],
            "calories": 620.0,
            "protein": 32.0,
            "carbs": 58.0,
            "fat": 22.0,
        },
        {
            "title": "Bean & cheese quesadilla + side salad",
            "subtitle": "Pantry-friendly, meat optional",
            "ingredients": [
                {"item": "Canned black beans", "qty": "½ can, rinsed", "est_cost_usd": 0.55},
                {"item": "Flour tortillas", "qty": "2 small", "est_cost_usd": 0.5},
                {"item": "Shredded cheese", "qty": "~2 oz", "est_cost_usd": 0.65},
                {"item": "Lettuce + simple dressing", "qty": "side salad", "est_cost_usd": 0.85},
            ],
            "calories": 710.0,
            "protein": 28.0,
            "carbs": 78.0,
            "fat": 28.0,
        },
        {
            "title": "Greek yogurt parfait",
            "subtitle": "Fast protein — breakfast or light dinner",
            "ingredients": [
                {"item": "Plain Greek yogurt", "qty": "2 cups", "est_cost_usd": 1.8},
                {"item": "Banana", "qty": "1", "est_cost_usd": 0.3},
                {"item": "Rolled oats", "qty": "½ cup dry", "est_cost_usd": 0.25},
                {"item": "Honey or jam", "qty": "1 tbsp", "est_cost_usd": 0.2},
            ],
            "calories": 580.0,
            "protein": 42.0,
            "carbs": 72.0,
            "fat": 12.0,
        },
    ]
    out: list[dict[str, Any]] = []
    for tpl in templates:
        ings = tpl["ingredients"]
        total_cost = round(sum(float(x["est_cost_usd"]) for x in ings), 2)
        cal = tpl["calories"]
        p = tpl["protein"]
        c = tpl["carbs"]
        f = tpl["fat"]
        out.append(
            {
                "title": tpl["title"],
                "subtitle": tpl["subtitle"],
                "ingredients": ings,
                "total_est_cost_usd": total_cost,
                "budget_note": "Rough discount-grocery prices (e.g. Aldi/Target); varies by store and sales.",
                "totals": {
                    "calories": round(cal, 1),
                    "protein": round(p, 1),
                    "carbs": round(c, 1),
                    "fat": round(f, 1),
                },
                "approx_macros_ranges": to_macro_ranges(
                    {"calories": cal, "protein": p, "carbs": c, "fat": f}
                ),
            }
        )
    return out


def _meal_bundle(
    combos: list[dict[str, Any]],
    rem: dict[str, float],
    note: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "combos": combos[:3],
        "cook_at_home": {"options": _budget_cook_options(rem)},
        "remaining": rem,
    }
    if note:
        payload["note"] = note
    return payload


def get_meal_suggestions(db: Session, user_id: int) -> dict[str, Any]:
    targets = get_daily_nutrition_target(db, user_id)
    if "error" in targets:
        return targets
    consumed = _today_food_totals(db, user_id)
    rem = {
        "calories": max(0.0, float(targets["calories"]) - consumed.get("calories", 0)),
        "protein": max(0.0, float(targets["protein"]) - consumed.get("protein", 0)),
        "carbs": max(0.0, float(targets["carbs"]) - consumed.get("carbs", 0)),
        "fat": max(0.0, float(targets["fat"]) - consumed.get("fat", 0)),
    }

    menu = get_cached_menu(db)
    if not menu:
        return _meal_bundle(
            [],
            rem,
            note="No CMU menu cached for today — cook-at-home budget ideas are still below.",
        )

    combos = []
    # Greedy simple triples
    for i, a in enumerate(menu[:12]):
        for j, b in enumerate(menu[:12]):
            if i == j:
                continue
            for k, c in enumerate(menu[:12]):
                if k in (i, j):
                    continue
                cal = a.calories + b.calories + c.calories
                p = a.protein + b.protein + c.protein
                if 0.7 * rem["calories"] <= cal <= 1.3 * max(rem["calories"], 400) and p >= 0.6 * rem["protein"]:
                    carb_t = a.carbs + b.carbs + c.carbs
                    fat_t = a.fat + b.fat + c.fat
                    combos.append(
                        {
                            "items": [a.name, b.name, c.name],
                            "cafes": [a.location, b.location, c.location],
                            "meal_periods": [a.meal_period, b.meal_period, c.meal_period],
                            "totals": {
                                "calories": round(cal, 1),
                                "protein": round(p, 1),
                                "carbs": round(carb_t, 1),
                                "fat": round(fat_t, 1),
                            },
                            "approx_macros_ranges": to_macro_ranges(
                                {
                                    "calories": cal,
                                    "protein": p,
                                    "carbs": carb_t,
                                    "fat": fat_t,
                                }
                            ),
                        }
                    )
                if len(combos) >= 3:
                    return _meal_bundle(combos, rem)
    if not combos:
        # pairwise fallback
        for i, a in enumerate(menu[:15]):
            for b in menu[:15]:
                if a.id == b.id:
                    continue
                cal = a.calories + b.calories
                p2 = a.protein + b.protein
                c2 = a.carbs + b.carbs
                f2 = a.fat + b.fat
                combos.append(
                    {
                        "items": [a.name, b.name],
                        "cafes": [a.location, b.location],
                        "meal_periods": [a.meal_period, b.meal_period],
                        "totals": {
                            "calories": round(cal, 1),
                            "protein": round(p2, 1),
                            "carbs": round(c2, 1),
                            "fat": round(f2, 1),
                        },
                        "approx_macros_ranges": to_macro_ranges(
                            {
                                "calories": cal,
                                "protein": p2,
                                "carbs": c2,
                                "fat": f2,
                            }
                        ),
                    }
                )
                if len(combos) >= 3:
                    break
            if len(combos) >= 3:
                break

    return _meal_bundle(combos, rem)


def get_crowd_recommendation(db: Session, gym: str, day_of_week: int | None = None) -> dict[str, Any]:
    _ = day_of_week
    windows, n = quietest_windows_today(db, gym, n=3)
    return {
        "gym": gym,
        "quiet_windows": windows,
        "based_on_checkins": n,
        "note": "Heuristic fallback used when data is sparse — still shown as guidance only.",
    }


def get_weekly_summary(db: Session, user_id: int) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        return {"error": "user not found"}

    end = date.today()
    start = end - timedelta(days=7)
    weights = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == user_id, WeightLog.date >= start)
        .order_by(WeightLog.date)
        .all()
    )
    w_trend = None
    if len(weights) >= 2:
        w_trend = weights[-1].weight_kg - weights[0].weight_kg

    workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.date >= start).all()
    days_with_workout = len({w.date for w in workouts})
    consistency = min(1.0, days_with_workout / 5.0)

    foods = db.query(FoodLog).filter(FoodLog.user_id == user_id, FoodLog.date >= start).all()
    targets = get_daily_nutrition_target(db, user_id)
    tgt_cal = float(targets.get("calories", 2000))
    by_day: dict[date, float] = defaultdict(float)
    for f in foods:
        by_day[f.date] += f.calories
    adherence_days = 0
    tracked_days = 0
    for d in range(7):
        d0 = end - timedelta(days=d)
        if d0 in by_day:
            tracked_days += 1
            if abs(by_day[d0] - tgt_cal) <= 150:
                adherence_days += 1
    macro_adherence = (adherence_days / tracked_days) if tracked_days else 0.0

    overload_wins = len(
        db.query(OverloadSuggestionLog)
        .filter(
            OverloadSuggestionLog.user_id == user_id,
            OverloadSuggestionLog.created_at >= datetime.combine(start, datetime.min.time()),
        )
        .all()
    )

    auto_note = ""
    if user.goal == "bulk" and (w_trend is not None) and w_trend < 0.1:
        auto_note = "Trend is flat vs bulk — consider ~+150 kcal/day bump if training is on track (suggestion, not auto-applied)."
    elif user.goal == "cut" and (w_trend is not None) and w_trend > 0.1:
        auto_note = "Weight trend is up vs cut goal — a small deficit tweak may help (discuss with a coach/RD if unsure)."

    return {
        "weight_trend_kg_per_week": w_trend,
        "goal": user.goal,
        "workout_consistency_score": round(consistency, 2),
        "macro_adherence_pct": round(macro_adherence * 100, 1),
        "progressive_overload_events": overload_wins,
        "auto_adjust_note": auto_note,
    }


TOOL_REGISTRY: dict[str, Any] = {
    "log_workout": log_workout,
    "get_progressive_overload_suggestion": get_progressive_overload_suggestion,
    "log_food": log_food,
    "get_daily_nutrition_target": get_daily_nutrition_target,
    "get_meal_suggestions": get_meal_suggestions,
    "get_crowd_recommendation": get_crowd_recommendation,
    "get_weekly_summary": get_weekly_summary,
}
