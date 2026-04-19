"""Exercise suggestions + body-part tagging (gym, cardio, free text)."""

from __future__ import annotations

from typing import Any

# Includes cardio for conditioning / zone balance charts.
BODY_ZONES = ("chest", "back", "legs", "shoulders", "arms", "core", "cardio")

# Suggestions for <datalist> — users can type any activity; these are hints only.
EXERCISE_CATALOG: list[dict[str, Any]] = [
    {"name": "Running (outdoor)", "parts": ["cardio", "legs"]},
    {"name": "Treadmill — incline walk", "parts": ["cardio", "legs"]},
    {"name": "Treadmill — jog", "parts": ["cardio", "legs"]},
    {"name": "Cycling", "parts": ["cardio", "legs"]},
    {"name": "Stationary bike", "parts": ["cardio", "legs"]},
    {"name": "Elliptical", "parts": ["cardio", "legs"]},
    {"name": "Swimming", "parts": ["cardio", "back", "arms"]},
    {"name": "Rowing machine", "parts": ["cardio", "back", "legs"]},
    {"name": "Stair climber", "parts": ["cardio", "legs"]},
    {"name": "Walking", "parts": ["cardio", "legs"]},
    {"name": "Bench press", "parts": ["chest", "arms"]},
    {"name": "Incline bench press", "parts": ["chest", "shoulders", "arms"]},
    {"name": "Overhead press", "parts": ["shoulders", "arms"]},
    {"name": "Squat", "parts": ["legs", "core"]},
    {"name": "Front squat", "parts": ["legs", "core"]},
    {"name": "Deadlift", "parts": ["back", "legs", "core"]},
    {"name": "Romanian deadlift", "parts": ["legs", "back"]},
    {"name": "Barbell row", "parts": ["back", "arms"]},
    {"name": "Pull-up", "parts": ["back", "arms"]},
    {"name": "Lat pulldown", "parts": ["back", "arms"]},
    {"name": "Leg press", "parts": ["legs"]},
    {"name": "Leg curl", "parts": ["legs"]},
    {"name": "Leg extension", "parts": ["legs"]},
    {"name": "Lunge", "parts": ["legs", "core"]},
    {"name": "Calf raise", "parts": ["legs"]},
    {"name": "Bicep curl", "parts": ["arms"]},
    {"name": "Tricep pushdown", "parts": ["arms"]},
    {"name": "Dip", "parts": ["chest", "arms"]},
    {"name": "Plank", "parts": ["core"]},
    {"name": "Cable crunch", "parts": ["core"]},
    {"name": "Hip thrust", "parts": ["legs", "core"]},
    {"name": "Face pull", "parts": ["shoulders", "back"]},
    {"name": "Lateral raise", "parts": ["shoulders"]},
]


def catalog_by_name_lower() -> dict[str, dict[str, Any]]:
    return {e["name"].strip().lower(): e for e in EXERCISE_CATALOG}


def _is_cardio_heuristic(ex: str) -> bool:
    return any(
        k in ex
        for k in (
            "run",
            "jog",
            "walk",
            "swim",
            "cycle",
            "bike",
            "elliptical",
            "stair",
            "rowing machine",
            "rower",
            "ski",
            "aerobic",
            "treadmill",
            "incline",
            "spin",
            "cardio",
            "hiit",
        )
    )


def infer_body_parts(exercise: str) -> list[str]:
    """Map free-text exercise name to BODY_ZONES (heuristic + catalog)."""
    ex = (exercise or "").strip().lower()
    if not ex:
        return ["other"]
    cat = catalog_by_name_lower().get(ex)
    if cat:
        parts = [p for p in cat["parts"] if p in BODY_ZONES]
        return parts or ["other"]

    tags: set[str] = set()

    def add(*ps: str) -> None:
        for p in ps:
            if p in BODY_ZONES:
                tags.add(p)

    if _is_cardio_heuristic(ex):
        add("cardio", "legs")

    if any(k in ex for k in ("bench", "push-up", "pushup", "push up", "chest fly", "pec deck")):
        add("chest")
    if "dip" in ex and "tricep" not in ex:
        add("chest", "arms")
    if any(k in ex for k in ("deadlift", "rdl", "romanian", "good morning", "hyperextension")):
        add("back", "legs", "core")
    if any(k in ex for k in ("row", "pull-up", "pullup", "pulldown", "lat ", "chin-up", "chinup")):
        add("back", "arms")
    if any(k in ex for k in ("squat", "leg press", "lunge", "leg curl", "leg extension", "calf", "hip thrust")):
        add("legs")
    if any(k in ex for k in ("ohp", "overhead", "shoulder press", "lateral raise", "rear delt", "face pull")):
        add("shoulders")
    if any(k in ex for k in ("curl", "tricep", "skull", "extension", "hammer")):
        add("arms")
    if any(k in ex for k in ("plank", "crunch", "ab ", "abs", "pallof", "dead bug", "core")):
        add("core")

    if not tags:
        if "press" in ex and "leg" not in ex:
            add("chest", "shoulders", "arms")
        else:
            return ["other"]
    return sorted(tags)


def rough_set_kcal(sets: int, reps: int, weight_kg: float | None, exercise: str = "") -> float:
    """Very rough kcal per log row (strength vs cardio heuristic). Not lab-grade."""
    try:
        s, r = float(sets), float(reps)
        w = float(weight_kg) if weight_kg is not None else 0.0
        ex = (exercise or "").lower()
        if _is_cardio_heuristic(ex):
            if w < 25:
                return max(0.0, 5.2 * s * r)
            return max(0.0, 0.012 * s * r * w)
        return max(0.0, 0.022 * s * r * w)
    except (TypeError, ValueError):
        return 0.0
