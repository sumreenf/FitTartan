"""LangGraph chat endpoint."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agent import run_turn_full, stream_final_text
from database import get_db
from summaries import get_enriched_summary

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatBody(BaseModel):
    user_id: int = Field(..., ge=1)
    message: str = Field(..., min_length=1, max_length=8000)
    stream: bool = False


def _cards_payload(intent: str, tool_output: Any, user_id: int, db: Session) -> dict[str, Any]:
    """Structured UI cards for meal / gym / weekly tool results (shown beside reply text)."""
    out: dict[str, Any] = {}
    if intent == "meal_suggest" and isinstance(tool_output, dict) and "error" not in tool_output:
        out["meal_combos"] = tool_output.get("combos") or []
        cah = tool_output.get("cook_at_home") or {}
        out["cook_options"] = cah.get("options") or []
    elif intent == "crowd_check" and isinstance(tool_output, dict):
        out["gym_windows"] = tool_output.get("quiet_windows") or []
        out["gym_meta"] = {
            "gym": tool_output.get("gym"),
            "basedOn": tool_output.get("based_on_checkins"),
        }
    elif intent == "weekly_summary" and isinstance(tool_output, dict) and "error" not in tool_output:
        # Full parity with GET /summary (targets vs achieved + insights + weight series)
        out["weekly_snapshot"] = get_enriched_summary(db, user_id)
    return out


@router.post("/chat")
async def chat(body: ChatBody, db: Session = Depends(get_db)):
    if body.stream:

        async def gen():
            async for chunk in stream_final_text(body.user_id, body.message):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    full = run_turn_full(body.user_id, body.message)
    payload: dict[str, Any] = {"reply": full["reply"]}
    payload.update(_cards_payload(full["intent"], full["tool_output"], body.user_id, db))
    return payload
