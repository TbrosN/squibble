"""Job and line-status models for the generation pipeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel

from models.script import ScriptLine


class LineGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    ERROR = "error"


class JobStatus(str, Enum):
    RUNNING = "running"
    CANCELLED = "cancelled"
    COMPLETE = "complete"
    ERROR = "error"


class LineStatus(BaseModel):
    id: int
    status: LineGenerationStatus = LineGenerationStatus.PENDING
    image_url: str | None = None
    audio_url: str | None = None
    duration: float | None = None


@dataclass
class AudioResult:
    path: str
    url: str
    duration: float


@dataclass
class ImageResult:
    path: str
    url: str


@dataclass
class VideoResult:
    path: str
    url: str


@dataclass
class Job:
    id: str
    script: list[ScriptLine]
    lines: list[LineStatus]
    status: JobStatus = JobStatus.RUNNING
    final_url: str | None = None
    task: asyncio.Task | None = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    event_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
