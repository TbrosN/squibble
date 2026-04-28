"""Video-to-restyled-stop-motion pipeline."""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

from constants import Paths, StopMotion
from services.image_service import ImageService
from services.video_service import VideoService


@dataclass(frozen=True)
class StopMotionResult:
    path: str
    url: str
    stop_motion_url: str
    stylized_url: str
    frame_count: int


@dataclass(frozen=True)
class StopMotionPreviewResult:
    path: str
    url: str
    frame_count: int


@dataclass(frozen=True)
class FrameSize:
    width: int
    height: int


class StopMotionService:
    def __init__(self, image_service: ImageService, video_service: VideoService) -> None:
        self._image = image_service
        self._video = video_service

    async def create_timing_preview(
        self,
        *,
        input_path: Path,
        job_id: str,
        job_dir: Path,
        frames_per_second: float = StopMotion.DEFAULT_FRAMES_PER_SECOND,
    ) -> StopMotionPreviewResult:
        try:
            fps = self._validate_fps(frames_per_second)
            stop_motion_path = job_dir / Paths.STOP_MOTION_VIDEO_FILENAME
            extracted_dir = job_dir / StopMotion.EXTRACTED_FRAMES_DIR

            await self._reset_dir(extracted_dir)
            await self._create_stop_motion_video(input_path, stop_motion_path, fps)
            frame_paths = await self._extract_frames(stop_motion_path, extracted_dir, fps)
            if len(frame_paths) > StopMotion.MAX_FRAMES:
                raise RuntimeError(
                    f"Stop-motion clip has {len(frame_paths)} frames; "
                    f"the current limit is {StopMotion.MAX_FRAMES}. "
                    "Try a shorter video or lower frame rate."
                )

            return StopMotionPreviewResult(
                path=str(stop_motion_path),
                url=f"/stopmotion/preview/{job_id}",
                frame_count=len(frame_paths),
            )
        except Exception as e:
            raise RuntimeError(f"StopMotionService.create_timing_preview failed: {e}") from e

    async def process(
        self,
        *,
        input_path: Path,
        style_prompt: str,
        job_id: str,
        job_dir: Path,
        frames_per_second: float = StopMotion.DEFAULT_FRAMES_PER_SECOND,
    ) -> StopMotionResult:
        try:
            fps = self._validate_fps(frames_per_second)
            clean_style = style_prompt.strip()
            if not clean_style:
                raise ValueError("style prompt is required")

            stop_motion_path = job_dir / Paths.STOP_MOTION_VIDEO_FILENAME
            final_path = job_dir / Paths.RESTYLED_VIDEO_FILENAME
            extracted_dir = job_dir / StopMotion.EXTRACTED_FRAMES_DIR
            restyled_dir = job_dir / StopMotion.RESTYLED_FRAMES_DIR

            await self._reset_dir(extracted_dir)
            await self._reset_dir(restyled_dir)

            await self._create_stop_motion_video(input_path, stop_motion_path, fps)
            frame_size = await self._probe_frame_size(stop_motion_path)
            frame_paths = await self._extract_frames(stop_motion_path, extracted_dir, fps)
            if len(frame_paths) > StopMotion.MAX_FRAMES:
                raise RuntimeError(
                    f"Stop-motion clip has {len(frame_paths)} frames; "
                    f"the current limit is {StopMotion.MAX_FRAMES}. "
                    "Try a shorter video or lower frame rate."
                )

            restyled_paths = await self._restyle_frames(frame_paths, restyled_dir, clean_style)
            await self._assemble_restyled_video(
                restyled_dir,
                stop_motion_path,
                final_path,
                fps,
                frame_size,
            )

            return StopMotionResult(
                path=str(final_path),
                url=f"/stopmotion/download/{job_id}",
                stop_motion_url=f"/stopmotion/preview/{job_id}",
                stylized_url=f"/stopmotion/stylized-preview/{job_id}",
                frame_count=len(restyled_paths),
            )
        except Exception as e:
            raise RuntimeError(f"StopMotionService.process failed: {e}") from e

    async def _create_stop_motion_video(self, input_path: Path, output_path: Path, fps: float) -> None:
        await self._video._run_ffmpeg(
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            f"fps={fps},scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        )

    async def _extract_frames(self, video_path: Path, frame_dir: Path, fps: float) -> list[Path]:
        await self._video._run_ffmpeg(
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps}",
            str(frame_dir / StopMotion.FRAME_FILENAME_PATTERN),
        )

        frame_paths = sorted(frame_dir.glob(StopMotion.FRAME_GLOB))
        if not frame_paths:
            raise RuntimeError("ffmpeg did not extract any stop-motion frames")
        return frame_paths

    async def _restyle_frames(
        self,
        frame_paths: list[Path],
        output_dir: Path,
        style_prompt: str,
    ) -> list[Path]:
        restyled_paths: list[Path] = []
        for index, frame_path in enumerate(frame_paths, start=1):
            output_path = output_dir / frame_path.name
            await self._image.restyle_frame(
                frame_path=frame_path,
                output_path=output_path,
                style_prompt=style_prompt,
            )
            restyled_paths.append(output_path)
        return restyled_paths

    async def _assemble_restyled_video(
        self,
        frame_dir: Path,
        audio_source_path: Path,
        output_path: Path,
        fps: float,
        frame_size: FrameSize,
    ) -> None:
        await self._video._run_ffmpeg(
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frame_dir / StopMotion.FRAME_FILENAME_PATTERN),
            "-i",
            str(audio_source_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a?",
            "-vf",
            (
                f"scale={frame_size.width}:{frame_size.height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={frame_size.width}:{frame_size.height}:(ow-iw)/2:(oh-ih)/2:"
                "color=black,setsar=1"
            ),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        )

    @staticmethod
    async def _probe_frame_size(video_path: Path) -> FrameSize:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(video_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            output = stderr.decode(errors="ignore")[-1000:]
            raise RuntimeError(f"ffprobe exited {proc.returncode}: {output}")

        try:
            width, height = stdout.decode().strip().split("x", maxsplit=1)
            return FrameSize(width=int(width), height=int(height))
        except ValueError as e:
            raise RuntimeError("ffprobe did not return a video frame size") from e

    @staticmethod
    async def _reset_dir(path: Path) -> None:
        await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)
        await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)

    @staticmethod
    def _validate_fps(frames_per_second: float) -> float:
        if frames_per_second < 1 or frames_per_second > 12:
            raise ValueError("frames_per_second must be between 1 and 12")
        if (frames_per_second * 2) % 1 != 0:
            raise ValueError("frames_per_second must use 0.5 increments")
        return frames_per_second
