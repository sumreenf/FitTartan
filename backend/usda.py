"""USDA FoodData Central API — macro lookup with ranges for display."""

from __future__ import annotations

import os
from typing import Any

import httpx

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"


def _get_key() -> str:
    return os.environ.get("USDA_API_KEY", "").strip()


def search_food(query: str, page_size: int = 5) -> list[dict[str, Any]]:
    key = _get_key()
    if not key:
        return []
    params = {"query": query, "pageSize": page_size, "api_key": key}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{USDA_BASE}/foods/search", params=params)
        r.raise_for_status()
        data = r.json()
    return data.get("foods") or []


def _nutrient_map(food_detail: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for n in food_detail.get("foodNutrients", []) or []:
        name = (n.get("nutrient", {}) or {}).get("name", "") or ""
        name_l = name.lower()
        amount = float(n.get("amount") or 0)
        if "energy" in name_l and "kilojoule" not in name_l:
            if "kcal" in name_l or name_l.strip() == "energy":
                out["calories"] = amount
        elif name_l.startswith("protein"):
            out["protein"] = amount
        elif "carbohydrate" in name_l:
            out["carbs"] = amount
        elif name_l.startswith("total lipid") or name_l == "fat":
            out["fat"] = amount
    return out


def get_food_macros_by_fdc_id(fdc_id: int) -> dict[str, float]:
    key = _get_key()
    if not key:
        return {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{USDA_BASE}/food/{fdc_id}", params={"api_key": key})
        r.raise_for_status()
        detail = r.json()
    return _nutrient_map(detail)


def estimate_macros_for_label(query: str) -> tuple[dict[str, float], str]:
    """
    Returns per-100g-style macros when possible; falls back to first search hit detail.
    """
    foods = search_food(query, page_size=3)
    if not foods:
        return (
            {"calories": 150.0, "protein": 10.0, "carbs": 15.0, "fat": 5.0},
            "heuristic_fallback",
        )
    f0 = foods[0]
    fid = f0.get("fdcId")
    if not fid:
        return (
            {"calories": 150.0, "protein": 10.0, "carbs": 15.0, "fat": 5.0},
            "heuristic_fallback",
        )
    macros = get_food_macros_by_fdc_id(int(fid))
    if macros["calories"] <= 0 and macros["protein"] <= 0:
        return (
            {"calories": 180.0, "protein": 12.0, "carbs": 18.0, "fat": 6.0},
            "partial_estimate",
        )
    return macros, f"fdc:{fid}"


def to_macro_ranges(macros: dict[str, float], uncertainty_pct: float = 0.12) -> dict[str, str]:
    """Human-friendly ranges to avoid false precision."""

    def band_g(x: float) -> str:
        if x <= 0:
            return "~0g"
        lo = max(0.0, x * (1 - uncertainty_pct))
        hi = x * (1 + uncertainty_pct)
        return f"~{lo:.0f}–{hi:.0f}g"

    cal = macros.get("calories", 0)
    cal_lo = max(0.0, cal * (1 - uncertainty_pct))
    cal_hi = cal * (1 + uncertainty_pct)
    return {
        "calories": f"~{cal_lo:.0f}–{cal_hi:.0f} kcal",
        "protein": band_g(macros.get("protein", 0)),
        "carbs": band_g(macros.get("carbs", 0)),
        "fat": band_g(macros.get("fat", 0)),
    }
