"""One motivational line per calendar day (deterministic per user + date)."""

from __future__ import annotations

from datetime import date

QUOTES: list[str] = [
    "Small steps today add up to big wins this week.",
    "You do not have to be perfect — you just have to show up.",
    "Consistency beats intensity when intensity is not sustainable.",
    "Fuel the work. Recovery is part of the plan.",
    "Progress is rarely linear — trust the trend, not one tough day.",
    "One good meal and one honest session are enough to call it a win.",
    "Energy follows action — start tiny, then build.",
    "Your future self is cheering for the choice you make right now.",
    "Discipline is remembering what you want — not what you feel like.",
    "Train the body, respect the mind, keep the long game in view.",
    "You are allowed to adjust the plan — you are not allowed to quit on yourself.",
    "Strength is built rep by rep, meal by meal, night of sleep by night.",
    "Comparison is noisy — focus on your own trajectory.",
    "Hydrate, move, eat something real — basics still move the needle.",
    "A walk counts. A stretch counts. Momentum loves small starts.",
    "You have survived every hard day so far — you can navigate this one too.",
    "Courage is showing up when motivation is on vacation.",
    "Better an imperfect session than a perfect excuse.",
    "Rest is not laziness when it is part of a smart plan.",
    "Food is fuel, not a moral test — choose support, not shame.",
    "One more glass of water is a quietly powerful habit.",
    "The goal is sustainable health, not a sprint to burnout.",
    "Celebrate forward motion, even if it is quieter than you hoped.",
    "You are building evidence that you can keep promises to yourself.",
    "Tough days teach resilience — be gentle, then get back on track.",
    "Your body adapts to what you repeat — repeat what you want to grow.",
    "Curiosity beats judgment when learning what works for you.",
    "You do not need the perfect plan — you need the next right step.",
    "Let today be the day you stack one more brick.",
    "Breath, posture, sleep — boring basics unlock dramatic change.",
    "You are closer than you think — keep going.",
    "Kindness to yourself is not weakness — it keeps you in the game.",
    "Choose progress over proof — nobody is grading your rough drafts.",
    "A short workout still counts as belonging to your identity as an athlete.",
    "Nourish so you can perform — restriction without strategy rarely lasts.",
    "Listen to your body like a coach, not a critic.",
    "You get to rewrite the story starting with the next meal.",
    "Patience is a strategy — results compound in the background.",
    "Show up with intention, leave with pride — even for twenty minutes.",
    "The CMU grind is real — fuel and recovery are part of the syllabus.",
    "You are not behind — you are on your own clock.",
    "Let consistency be your flex.",
    "Hard effort plus smart recovery equals durable gains.",
    "Today is a fresh page — write something you will be glad you kept.",
    "Motion creates motivation more often than the reverse — start small.",
    "You deserve a plan that fits real life — adjust and advance.",
    "Keep the promise small enough to keep, important enough to matter.",
    "Steady beats heroic if heroic never shows up twice.",
    "Trust the process on the boring days — that is where the work lives.",
    "You are building a life that supports the goals you care about.",
]


def get_daily_motivation(user_id: int, day: date | None = None) -> dict[str, str]:
    d = day or date.today()
    idx = (user_id * 7919 + d.toordinal()) % len(QUOTES)
    return {"date": str(d), "message": QUOTES[idx]}
