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
        script_id, reply, script = await _script_service.chat(
            script_id=request.script_id,
            message=request.message,
            canvas_lines=request.canvas_lines,
            selected_lines=request.selected_lines,
        )
        return ChatResponse(script_id=script_id, reply=reply, script=script)
    except Exception as e:
        logger.error("Script chat failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "We couldn't reach the writing assistant. Please try again."},
        ) from e
