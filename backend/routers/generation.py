"""HTTP routes for the Stage 2 generation pipeline."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from constants import HTTP, Paths
from jobs.store import job_store
from models.events import SSEEvent, SSEEventType
from models.job import JobStatus
from models.script import ScriptLine
from services.audio_service import AudioService, GoogleTtsAudioGenerator
from services.generation_service import GenerationService
from services.image_service import ImageService
from services.video_service import VideoService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["generation"])

_generation_service = GenerationService(
    audio_service=AudioService(generator=GoogleTtsAudioGenerator()),
    image_service=ImageService(),
    video_service=VideoService(),
)


class StartRequest(BaseModel):
    script: list[ScriptLine]


class StartResponse(BaseModel):
    job_id: str


class OkResponse(BaseModel):
    ok: bool = True


@router.post("/start", response_model=StartResponse)
async def start(request: StartRequest) -> StartResponse:
    if not request.script:
        raise HTTPException(
            status_code=400,
            detail={"error": "Your script is empty — write something first."},
        )

    job = job_store.create(request.script)
    job.task = asyncio.create_task(_generation_service.run(job))
    return StartResponse(job_id=job.id)


@router.get("/stream/{job_id}")
async def stream(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "That generation job no longer exists."},
        )

    async def event_source():
        yield f"retry: {HTTP.SSE_RETRY_MS}\n\n"
        while True:
            try:
                event: SSEEvent = await asyncio.wait_for(job.event_queue.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                if job.status != JobStatus.RUNNING:
                    return
                continue

            yield f"data: {event.model_dump_json()}\n\n"

            if event.type in (SSEEventType.COMPLETE, SSEEventType.CANCELLED, SSEEventType.ERROR):
                return

    return StreamingResponse(event_source(), media_type=HTTP.SSE_MEDIA_TYPE)


@router.post("/cancel/{job_id}", response_model=OkResponse)
async def cancel(job_id: str) -> OkResponse:
    if not job_store.cancel(job_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "That generation job no longer exists."},
        )
    return OkResponse()


@router.get("/asset/{job_id}/{filename}")
async def asset(job_id: str, filename: str):
    file_path = _resolve_job_path(job_id, filename)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "That asset isn't ready yet."},
        )
    return FileResponse(str(file_path))


@router.get("/download/{job_id}")
async def download(job_id: str):
    file_path = _resolve_job_path(job_id, Paths.FINAL_VIDEO_FILENAME)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "Your video isn't ready yet."},
        )
    return FileResponse(
        str(file_path),
        media_type="video/mp4",
        filename=f"squibble_{job_id}.mp4",
    )


def _resolve_job_path(job_id: str, filename: str) -> Path:
    base = (Paths.OUTPUT_DIR / job_id).resolve()
    candidate = (base / filename).resolve()
    if base not in candidate.parents and candidate != base:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid asset path."},
        )
    return candidate
