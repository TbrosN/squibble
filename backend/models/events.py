"""Typed Server-Sent Event payloads emitted during generation."""

from enum import Enum

from pydantic import BaseModel

from models.job import LineGenerationStatus


class SSEEventType(str, Enum):
    LINE_UPDATE = "line_update"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"


class SSEEvent(BaseModel):
    type: SSEEventType


class LineUpdateEvent(SSEEvent):
    type: SSEEventType = SSEEventType.LINE_UPDATE
    line_id: int
    status: LineGenerationStatus
    image_url: str | None = None
    audio_url: str | None = None
    duration: float | None = None


class CompleteEvent(SSEEvent):
    type: SSEEventType = SSEEventType.COMPLETE
    final_url: str


class CancelledEvent(SSEEvent):
    type: SSEEventType = SSEEventType.CANCELLED


class ErrorEvent(SSEEvent):
    type: SSEEventType = SSEEventType.ERROR
    line_id: int | None = None
    message: str
