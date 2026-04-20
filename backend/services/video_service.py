"""Assembles the per-line assets into a final .mp4 via ffmpeg."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from constants import Paths
from models.job import VideoResult


@dataclass
class VideoSegment:
    image_path: str
    audio_path: str
    duration: float


class VideoService:
    async def assemble(
        self,
        segments: list[VideoSegment],
        job_id: str,
        job_dir: Path,
    ) -> VideoResult:
        try:
            if not segments:
                raise RuntimeError("no segments to assemble")

            final_path = job_dir / Paths.FINAL_VIDEO_FILENAME
            concat_list_path = job_dir / "concat.txt"

            part_paths: list[Path] = []
            for idx, seg in enumerate(segments):
                part_path = job_dir / f"part_{idx:02d}.mp4"
                await self._render_segment(seg, part_path)
                part_paths.append(part_path)

            concat_lines = "\n".join(f"file '{p.name}'" for p in part_paths) + "\n"
            await asyncio.to_thread(concat_list_path.write_text, concat_lines)

            await self._run_ffmpeg(
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-c", "copy",
                str(final_path),
            )

            return VideoResult(
                path=str(final_path),
                url=f"/generate/download/{job_id}",
            )
        except Exception as e:
            raise RuntimeError(f"VideoService.assemble failed: {e}") from e

    @classmethod
    async def _render_segment(cls, seg: VideoSegment, out_path: Path) -> None:
        duration = max(seg.duration, 0.5)
        await cls._run_ffmpeg(
            "-y",
            "-loop", "1",
            "-i", seg.image_path,
            "-i", seg.audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1024:1024:force_original_aspect_ratio=decrease,"
                   "pad=1024:1024:(ow-iw)/2:(oh-ih)/2:color=black,"
                   "setsar=1,fps=30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-t", f"{duration:.3f}",
            str(out_path),
        )

    @staticmethod
    async def _run_ffmpeg(*args: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            tail = stderr.decode(errors="ignore")[-500:]
            raise RuntimeError(f"ffmpeg exited {proc.returncode}: {tail}")
