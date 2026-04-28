"""HTTP routes for uploaded-video stop-motion restyling."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from constants import Paths, StopMotion
from services.image_service import ImageService
from services.stop_motion_service import StopMotionService
from services.video_service import VideoService

router = APIRouter(prefix="/stopmotion", tags=["stopmotion"])

_stop_motion_service = StopMotionService(
    image_service=ImageService(),
    video_service=VideoService(),
)


class StopMotionResponse(BaseModel):
    job_id: str
    download_url: str
    preview_url: str
    stylized_preview_url: str
    frame_count: int


@router.post("/create", response_model=StopMotionResponse)
async def create(
    file: UploadFile = File(...),
    style_prompt: str = Form(...),
    frames_per_second: int = Form(StopMotion.DEFAULT_FRAMES_PER_SECOND),
) -> StopMotionResponse:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail={"error": "Upload a video file to make a stop-motion restyle."},
        )

    job_id = uuid.uuid4().hex
    job_dir = Paths.OUTPUT_DIR / "stopmotion" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / _input_filename(file.filename)
    try:
        await _write_upload(file, input_path)
        result = await _stop_motion_service.process(
            input_path=input_path,
            style_prompt=style_prompt,
            job_id=job_id,
            job_dir=job_dir,
            frames_per_second=frames_per_second,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": f"Could not restyle the video: {e}"},
        ) from e

    return StopMotionResponse(
        job_id=job_id,
        download_url=result.url,
        preview_url=result.stop_motion_url,
        stylized_preview_url=result.stylized_url,
        frame_count=result.frame_count,
    )


@router.get("/preview/{job_id}")
async def preview(job_id: str):
    file_path = _resolve_job_path(job_id, Paths.STOP_MOTION_VIDEO_FILENAME)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "That stop-motion preview is not ready."},
        )
    return FileResponse(str(file_path), media_type="video/mp4")


@router.get("/download/{job_id}")
async def download(job_id: str):
    file_path = _resolve_job_path(job_id, Paths.RESTYLED_VIDEO_FILENAME)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "That restyled video is not ready."},
        )
    return FileResponse(
        str(file_path),
        media_type="video/mp4",
        filename=f"squibble_stopmotion_{job_id}.mp4",
    )


@router.get("/stylized-preview/{job_id}")
async def stylized_preview(job_id: str):
    file_path = _resolve_job_path(job_id, Paths.RESTYLED_VIDEO_FILENAME)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "That stylized video preview is not ready."},
        )
    return FileResponse(str(file_path), media_type="video/mp4")


async def _write_upload(file: UploadFile, destination: Path) -> None:
    with destination.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            out.write(chunk)


def _input_filename(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if not suffix:
        suffix = ".mp4"
    return f"{StopMotion.INPUT_VIDEO_FILENAME}{suffix}"


def _resolve_job_path(job_id: str, filename: str) -> Path:
    base = (Paths.OUTPUT_DIR / "stopmotion" / job_id).resolve()
    candidate = (base / filename).resolve()
    if base not in candidate.parents and candidate != base:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid stop-motion asset path."},
        )
    return candidate
