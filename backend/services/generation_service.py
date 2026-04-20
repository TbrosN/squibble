"""Orchestrates per-line audio+image generation and final video assembly."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from constants import Paths
from models.events import (
    CancelledEvent,
    CompleteEvent,
    ErrorEvent,
    LineUpdateEvent,
    SSEEvent,
)
from models.job import (
    AudioResult,
    ImageResult,
    Job,
    JobStatus,
    LineGenerationStatus,
)
from services.audio_service import AudioService
from services.image_service import ImageService
from services.video_service import VideoSegment, VideoService

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(
        self,
        audio_service: AudioService,
        image_service: ImageService,
        video_service: VideoService,
    ) -> None:
        self._audio = audio_service
        self._image = image_service
        self._video = video_service

    async def run(self, job: Job) -> None:
        job_dir = Paths.OUTPUT_DIR / job.id
        job_dir.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            (job_dir / Paths.SCRIPT_FILENAME).write_text,
            json.dumps([line.model_dump() for line in job.script], indent=2),
        )

        current_line_id: int | None = None
        try:
            segments: list[VideoSegment] = []

            for line, line_status in zip(job.script, job.lines):
                current_line_id = line.id

                if job.cancel_event.is_set():
                    await self._emit(job, CancelledEvent())
                    job.status = JobStatus.CANCELLED
                    return

                line_status.status = LineGenerationStatus.GENERATING
                await self._emit(
                    job,
                    LineUpdateEvent(
                        line_id=line.id,
                        status=LineGenerationStatus.GENERATING,
                    ),
                )

                audio_result, image_result = await asyncio.gather(
                    self._audio.generate(line, job.id, job_dir),
                    self._image.generate(line, job.id, job_dir),
                )
                assert isinstance(audio_result, AudioResult)
                assert isinstance(image_result, ImageResult)

                line_status.status = LineGenerationStatus.DONE
                line_status.image_url = image_result.url
                line_status.audio_url = audio_result.url
                line_status.duration = audio_result.duration

                await self._emit(
                    job,
                    LineUpdateEvent(
                        line_id=line.id,
                        status=LineGenerationStatus.DONE,
                        image_url=image_result.url,
                        audio_url=audio_result.url,
                        duration=audio_result.duration,
                    ),
                )

                segments.append(
                    VideoSegment(
                        image_path=image_result.path,
                        audio_path=audio_result.path,
                        duration=audio_result.duration,
                    )
                )

            if job.cancel_event.is_set():
                await self._emit(job, CancelledEvent())
                job.status = JobStatus.CANCELLED
                return

            final = await self._video.assemble(segments, job.id, job_dir)
            job.final_url = final.url
            job.status = JobStatus.COMPLETE
            await self._emit(job, CompleteEvent(final_url=final.url))

        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            await self._emit(job, CancelledEvent())
            raise
        except Exception as e:
            logger.error("Generation job %s failed: %s", job.id, e)
            job.status = JobStatus.ERROR
            await self._emit(
                job,
                ErrorEvent(
                    line_id=current_line_id,
                    message="Something went wrong generating this slide.",
                ),
            )

    @staticmethod
    async def _emit(job: Job, event: SSEEvent) -> None:
        await job.event_queue.put(event)
