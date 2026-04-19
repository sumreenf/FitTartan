"""Scrape CMU dining menus and enrich with USDA macros."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from database import DiningMenuItem
from usda import estimate_macros_for_label

logger = logging.getLogger(__name__)

TARGET_LOCATIONS = [
    "Resnik",
    "Tepper Café",
    "Entropy",
    "La Prima",
    "The Exchange",
]

MENU_URL = "https://dining.cmu.edu/dining/menus/index.html"

# Browser-like headers help some campus sites that reject generic clients.
_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _mock_menu_for_today() -> list[dict[str, Any]]:
    """Deterministic fallback when live scrape fails (demo / network)."""
    today = date.today()
    base = [
        ("Grilled Chicken Bowl", "Resnik", "Lunch"),
        ("Veggie Stir Fry", "Resnik", "Dinner"),
        ("Turkey Sandwich", "Tepper Café", "Lunch"),
        ("Greek Salad", "Tepper Café", "Dinner"),
        ("Entropy Burger", "Entropy", "Dinner"),
        ("Margherita Pizza Slice", "Entropy", "Lunch"),
        ("Cappuccino", "La Prima", "Breakfast"),
        ("Almond Croissant", "La Prima", "Breakfast"),
        ("Sushi Roll Combo", "The Exchange", "Lunch"),
        ("Grain Bowl", "The Exchange", "Dinner"),
    ]
    rows = []
    for name, loc, meal in base:
        rows.append({"name": name, "location": loc, "meal_period": meal, "date_scraped": today})
    return rows


def _parse_menu_html(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    items: list[dict[str, Any]] = []
    today = date.today()

    # Dining sites vary; collect plausible dish names from headings and list items
    for loc in TARGET_LOCATIONS:
        block = soup.find(string=lambda t: t and loc.lower() in t.lower())
        if block and block.parent:
            section = block.find_parent(["section", "div", "article", "li"])
            if section:
                for li in section.find_all(["li", "p", "span"]):
                    text = (li.get_text() or "").strip()
                    if 4 < len(text) < 120 and not text.lower().startswith("http"):
                        items.append(
                            {
                                "name": text,
                                "location": loc,
                                "meal_period": "All day",
                                "date_scraped": today,
                            }
                        )

    # Generic: all list items that look like food lines
    if not items:
        for li in soup.find_all("li"):
            text = (li.get_text() or "").strip()
            if 6 < len(text) < 100:
                items.append(
                    {
                        "name": text,
                        "location": "Resnik",
                        "meal_period": "All day",
                        "date_scraped": today,
                    }
                )

    # Dedupe by name+location
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        key = (it["name"], it["location"])
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out[:40]


def fetch_raw_menu_html() -> str | None:
    try:
        with httpx.Client(timeout=25.0, follow_redirects=True) as client:
            r = client.get(MENU_URL, headers=_DEFAULT_HEADERS)
            r.raise_for_status()
            return r.text
    except Exception as e:
        # Common causes: offline / DNS error (e.g. WinError 11001 getaddrinfo),
        # firewall/VPN, or CMU site temporarily unavailable. Demo menu is used.
        logger.info(
            "Live CMU menu not loaded (%s). Using bundled demo items; meal features still work.",
            e,
        )
        return None


def scrape_today_items() -> list[dict[str, Any]]:
    html = fetch_raw_menu_html()
    if not html:
        return _mock_menu_for_today()
    parsed = _parse_menu_html(html)
    if len(parsed) < 3:
        return _mock_menu_for_today()
    return parsed


def sync_menu_to_db(db: Session) -> int:
    """Upsert today's menu with USDA macros; returns rows written."""
    today = date.today()
    db.query(DiningMenuItem).filter(DiningMenuItem.date_scraped == today).delete()
    db.commit()

    rows = scrape_today_items()
    count = 0
    for row in rows:
        macros, _src = estimate_macros_for_label(row["name"])
        item = DiningMenuItem(
            name=row["name"],
            calories=macros["calories"],
            protein=macros["protein"],
            carbs=macros["carbs"],
            fat=macros["fat"],
            location=row["location"],
            meal_period=row["meal_period"],
            date_scraped=row["date_scraped"],
        )
        db.add(item)
        count += 1
    db.commit()
    return count


def get_cached_menu(db: Session) -> list[DiningMenuItem]:
    today = date.today()
    q = db.query(DiningMenuItem).filter(DiningMenuItem.date_scraped == today).all()
    if not q:
        sync_menu_to_db(db)
        q = db.query(DiningMenuItem).filter(DiningMenuItem.date_scraped == today).all()
    return q
