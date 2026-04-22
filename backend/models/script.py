"""Pydantic models for script lines and the /script/chat endpoint."""

from pydantic import BaseModel, Field


class ScriptLine(BaseModel):
    id: int
    line: str


class ChatRequest(BaseModel):
    message: str
    # Opaque handle identifying one script draft (and its rolling server-side
    # conversation history + on-disk buffer). Null on the very first turn; the
    # server mints one and returns it, and the client echoes it back on every
    # subsequent turn.
    script_id: str | None = None
    canvas_lines: list[str] = Field(default_factory=list)
    selected_lines: list[int] = Field(default_factory=list)


class ChatResponse(BaseModel):
    script_id: str
    reply: str
    script: list[ScriptLine]
