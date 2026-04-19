"""Safety checks on agent draft responses; log triggers for eval."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from database import GuardrailLog

ED_KEYWORDS = [
    "restrict",
    "purge",
    "starve",
    "binge",
    "laxative",
    "vomit",
    "thinspo",
    "pro-ana",
    "pro-mia",
]

MEDICAL_PATTERNS = [
    r"\bdiagnos(e|is|ed)\b",
    r"\bprescrib(e|ed)\b",
    r"\bmedication\b",
    r"\btreat(ment)?\s+(your|the)\b",
    r"\bcancer\b",
    r"\bdiabetes\b",
    r"\bdisorder\b.*\b(eat|food)\b",
]

CRISIS_RESPONSE = """I'm not able to help with harmful eating or purging behaviors. If you're struggling with food or body image, please reach out to a trusted professional or crisis line.

National Eating Disorders Association (NEDA) helpline: Call or text **988** (Suicide & Crisis Lifeline) or visit https://www.nationaleatingdisorders.org/help-support/contact-helpline for the NEDA Helpline.

CMU students can also use CMU Counseling and Psychological Services (CaPS)."""


def _log_trigger(db: Session | None, user_id: int | None, trigger_type: str, snippet: str | None) -> None:
    if db is None:
        return
    db.add(GuardrailLog(user_id=user_id, trigger_type=trigger_type, message_snippet=(snippet or "")[:2000]))
    db.commit()


def apply_guardrails(
    draft: str,
    *,
    db: Session | None = None,
    user_id: int | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """
    Returns safe text. Logs triggers. Eating disorder keywords short-circuit to crisis response.
    """
    text = draft or ""
    lower = text.lower()

    for kw in ED_KEYWORDS:
        if kw in lower:
            _log_trigger(db, user_id, "eating_disorder_signal", kw)
            return CRISIS_RESPONSE

    # Extreme calorie targets in structured context
    if context:
        cal = context.get("target_calories") or context.get("calories")
        if isinstance(cal, (int, float)) and cal < 1200:
            _log_trigger(db, user_id, "calorie_floor", str(cal))
            return (
                "For most adults, sustained intake far below about 1200 kcal/day needs personalized medical "
                "guidance. Let's aim for at least ~1200 kcal unless a clinician says otherwise, and focus on "
                "balanced meals you can keep up with."
            )

    out = text
    for pat in MEDICAL_PATTERNS:
        if re.search(pat, lower, re.I):
            _log_trigger(db, user_id, "medical_language", pat)
            out = re.sub(pat, "[general wellness note]", out, flags=re.I)

    # Strip common diagnosis-style phrasing
    if re.search(r"\byou (have|are experiencing) [a-z]+ (disorder|disease)\b", lower):
        _log_trigger(db, user_id, "medical_language", "diagnosis_phrase")
        out = "I'm not able to diagnose conditions. " + re.sub(
            r"(?i)you (have|are experiencing) [^.!?]+[.!?]",
            "Here's what tends to help generally: prioritize sleep, balanced meals, and sustainable training. ",
            out,
            count=1,
        )

    # Progressive overload cap reminder if suggestion leaked >10% jump in same line
    m = re.search(r"\+?\s*(\d+(?:\.\d+)?)\s*%", out)
    if m and float(m.group(1)) > 10:
        _log_trigger(db, user_id, "overload_cap", m.group(0))
        out = re.sub(
            r"\+?\s*\d+(?:\.\d+)?\s*%",
            "a small, gradual increase (capped around 10% per week unless a coach says otherwise)",
            out,
            count=1,
        )

    return out
