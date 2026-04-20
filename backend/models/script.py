"""Pydantic models for script lines and chat history."""

from typing import Literal

from pydantic import BaseModel, Field


class ScriptLine(BaseModel):
    id: int
    line: str
    image_prompt: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    selected_lines: list[int] = Field(default_factory=list)
    current_script: list[ScriptLine] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    script: list[ScriptLine]
