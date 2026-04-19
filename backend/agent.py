"""LangGraph agent: intent → tools → draft → guardrails."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from typing import Annotated, Any, TypedDict

from anthropic import Anthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from database import SessionLocal
from guardrails import apply_guardrails
from tools import (
    get_crowd_recommendation,
    get_daily_nutrition_target,
    get_meal_suggestions,
    get_progressive_overload_suggestion,
    get_weekly_summary,
    log_food,
    log_workout,
)

MODEL = "claude-sonnet-4-20250514"

_CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "agent_checkpoints.sqlite")


def _client() -> Anthropic:
    return Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int
    user_message: str
    intent: str
    slots: dict[str, Any]
    tool_output: Any
    draft_response: str
    final_response: str


def _latest_user_text(state: AgentState) -> str:
    for m in reversed(state.get("messages") or []):
        if isinstance(m, HumanMessage):
            c = m.content
            return c if isinstance(c, str) else str(c)
    return state.get("user_message") or ""


def _keyword_intent_override(text: str) -> tuple[str, dict[str, Any]] | None:
    """
    Deterministic routing for common phrases so meal/gym/weekly intents hit tools + UI cards
    even when the LLM would classify as general_chat (e.g. 'what to eat nearby?').
    """
    t = text.lower().strip()
    if re.search(
        r"\b(weekly\s+summary|week\s+in\s+review|my\s+week|summarize\s+my\s+week)\b",
        t,
    ):
        return "weekly_summary", {}
    if re.search(
        r"\b(when\s+should\s+i\s+go\s+to\s+the\s+gym|gym\s+timing|gym\s+crowd|"
        r"quiet.*\bgym|busy.*\bgym|\bskibo\b|\bcuc\b|\btepper\b|swimming\s+pool|crowd\s+at\s+the\s+gym)\b",
        t,
    ):
        return "crowd_check", {}
    if re.search(
        r"\b("
        r"what\s+to\s+eat|what\s+should\s+i\s+eat|what\s+can\s+i\s+eat|"
        r"eat\s+nearby|food\s+nearby|eating\s+nearby|nearby\s+(to\s+)?(eat|food|dining)|"
        r"where\s+to\s+eat|on\s+campus\s+(food|dining|eat)|campus\s+(dining|food)|"
        r"dining\s+(hall|today|options)|meal\s+idea|lunch\s+idea|dinner\s+idea|"
        r"\bhungry\b|macros?\s+for\s+today|food\s+options|meal\s+options"
        r")\b",
        t,
    ):
        return "meal_suggest", {}
    return None


def intent_classifier(state: AgentState) -> AgentState:
    text = _latest_user_text(state)
    kw = _keyword_intent_override(text)
    if kw:
        intent, slots = kw
        return {**state, "intent": intent, "slots": slots, "user_message": text}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {**state, "intent": "general_chat", "slots": {}, "user_message": text}
    c = _client()
    prompt = f"""You classify CMU fitness assistant messages.
Return ONLY valid JSON with keys: intent, slots.

intent must be one of:
log_workout, log_food, meal_suggest, overload_ask, crowd_check, weekly_summary, goal_update, general_chat

Slots (include only what's inferable):
- log_workout: exercise (string), sets (int), reps (int), weight_kg (float, optional — omit for cardio or unknown load)
- log_food: item_name (string)
- overload_ask: exercise (string)
- crowd_check: gym (string: CUC Gym, Tepper Gym, or Swimming pool when specified)
- meal_suggest, weekly_summary, goal_update: {{}}
- general_chat: {{}}

User message:
{text}
"""
    try:
        msg = c.messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = msg.content[0].text if msg.content else "{}"
        m = re.search(r"\{[\s\S]*\}", raw_text)
        raw = m.group(0) if m else raw_text
        data = json.loads(raw)
        intent = data.get("intent", "general_chat")
        slots = data.get("slots") or {}
    except Exception:
        intent, slots = "general_chat", {}

    return {**state, "intent": intent, "slots": slots, "user_message": text}


def tool_executor(state: AgentState) -> AgentState:
    uid = state["user_id"]
    intent = state["intent"]
    slots = state["slots"] or {}
    out: Any = {}

    db = SessionLocal()
    try:
        if intent == "log_workout":
            ex = slots.get("exercise") or "general training"
            sets = int(slots.get("sets") or 3)
            reps = int(slots.get("reps") or 8)
            raw_w = slots.get("weight_kg")
            w = None if raw_w in (None, "", False) else float(raw_w)
            out = log_workout(db, uid, ex, sets, reps, w)
        elif intent == "log_food":
            item = slots.get("item_name") or state["user_message"]
            out = log_food(db, uid, item)
        elif intent == "meal_suggest":
            out = get_meal_suggestions(db, uid)
        elif intent == "overload_ask":
            ex = slots.get("exercise") or "bench press"
            out = get_progressive_overload_suggestion(db, uid, ex)
        elif intent == "crowd_check":
            gym = slots.get("gym") or "CUC Gym"
            out = get_crowd_recommendation(db, gym, None)
        elif intent == "weekly_summary":
            out = get_weekly_summary(db, uid)
        elif intent == "goal_update":
            out = {
                "note": "Goals are suggestions only — update your profile via onboarding or ask for nutrition targets."
            }
        else:
            out = {"context": "general_chat"}
    finally:
        db.close()

    return {**state, "tool_output": out}


def response_generator(state: AgentState) -> AgentState:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        payload = {
            "intent": state["intent"],
            "tool_output": state["tool_output"],
            "user_message": state["user_message"],
        }
        draft = (
            "FitTartan needs ANTHROPIC_API_KEY on the server to generate full replies. "
            f"Here's structured context: {json.dumps(payload, default=str)[:1200]}"
        )
        return {**state, "draft_response": draft}
    c = _client()
    sys = (
        "You are FitTartan, a CMU-specific fitness and nutrition helper. "
        "Use friendly, concise tone. Never diagnose. Present workout changes as suggestions only, never as prescriptions. "
        "Prefer macro ranges over false precision. Mention CMU dining locations when relevant.\n\n"
        "Format every reply for easy scanning: use short paragraphs separated by a blank line; use markdown "
        "headings (## Like this) when you have distinct sections; use bullet lists (- item) for steps, options, or tips; "
        "use **bold** for short labels (e.g. **Pro tip:**). Avoid one huge wall of text."
    )
    card_note = ""
    if state.get("intent") == "meal_suggest":
        card_note = (
            " The app will show tappable cards for CMU combos and budget cook-at-home options — "
            "do not repeat dish names, macros, or prices from the cards. Above the cards, write 2–4 short lines: "
            "optional ## line, then a brief intro and/or a tiny bullet list (-) for habits or timing only."
        )
    elif state.get("intent") == "crowd_check":
        card_note = (
            " The app shows quiet-hour cards — do not repeat the same windows in prose. "
            "Give 2–3 lines: optional ## heading, one sentence framing, optional - bullets for tips (not times)."
        )
    elif state.get("intent") == "weekly_summary":
        card_note = (
            " The app shows summary cards — do not repeat the same numbers. "
            "Offer 2–4 lines: optional ## heading, supportive commentary, optional - bullets for next steps only."
        )
    payload = {
        "intent": state["intent"],
        "tool_output": state["tool_output"],
        "user_message": state["user_message"],
    }
    msg = c.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=sys + card_note,
        messages=[
            {
                "role": "user",
                "content": "Context JSON:\n"
                + json.dumps(payload, default=str)
                + "\n\nWrite the user-facing reply.",
            }
        ],
    )
    draft = msg.content[0].text if msg.content else "Thanks — I'm here to help with CMU meals, training, and gym timing."
    return {**state, "draft_response": draft}


def guardrails_node(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        ctx: dict[str, Any] = {}
        to = state.get("tool_output") or {}
        if isinstance(to, dict) and "calories" in to:
            ctx["target_calories"] = to.get("calories")
        final = apply_guardrails(state["draft_response"], db=db, user_id=state["user_id"], context=ctx)
    finally:
        db.close()
    return {**state, "final_response": final, "messages": [AIMessage(content=final)]}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("intent_classifier", intent_classifier)
    g.add_node("tool_executor", tool_executor)
    g.add_node("response_generator", response_generator)
    g.add_node("guardrails_node", guardrails_node)
    g.set_entry_point("intent_classifier")
    g.add_edge("intent_classifier", "tool_executor")
    g.add_edge("tool_executor", "response_generator")
    g.add_edge("response_generator", "guardrails_node")
    g.add_edge("guardrails_node", END)

    conn = sqlite3.connect(_CHECKPOINT_PATH, check_same_thread=False)
    saver = SqliteSaver(conn)
    return g.compile(checkpointer=saver)


graph = build_graph()


def run_turn_full(user_id: int, user_message: str, thread_id: str | None = None) -> dict[str, Any]:
    tid = thread_id or f"user-{user_id}"
    cfg = {"configurable": {"thread_id": tid}}
    state_in: AgentState = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "user_message": user_message,
        "intent": "general_chat",
        "slots": {},
        "tool_output": {},
        "draft_response": "",
        "final_response": "",
    }
    out = graph.invoke(state_in, cfg)
    return {
        "reply": out.get("final_response") or "",
        "intent": out.get("intent") or "general_chat",
        "tool_output": out.get("tool_output"),
    }


def run_turn(user_id: int, user_message: str, thread_id: str | None = None) -> str:
    return run_turn_full(user_id, user_message, thread_id=thread_id).get("reply") or ""


async def stream_final_text(user_id: int, user_message: str):
    """Yield SSE-sized chunks of the guarded reply (full text chunked)."""
    text = run_turn(user_id, user_message)
    for i in range(0, len(text), 32):
        yield text[i : i + 32]
