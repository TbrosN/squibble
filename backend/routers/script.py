"""HTTP routes for the Stage 1 script studio chat."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.script import ChatRequest, ChatResponse
from services.script_service import ScriptService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/script", tags=["script"])

_script_service = ScriptService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply, script = await _script_service.chat(
            messages=request.messages,
            selected_lines=request.selected_lines,
            current_script=request.current_script,
        )
        return ChatResponse(reply=reply, script=script)
    except Exception as e:
        logger.error("Script chat failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "We couldn't reach the writing assistant. Please try again."},
        ) from e
