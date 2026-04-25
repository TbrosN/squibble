"""Assembles the per-line assets into a final .mp4 via ffmpeg."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from constants import Generation, Paths
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
            image_concat_path = job_dir / "image_concat.txt"

            await asyncio.to_thread(
                image_concat_path.write_text,
                self._build_image_concat_file(segments),
                encoding="utf-8",
            )

            audio_args = [arg for seg in segments for arg in ("-i", seg.audio_path)]
            await self._run_ffmpeg(
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(image_concat_path),
                *audio_args,
                "-filter_complex",
                self._build_filter_complex(len(segments)),
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_path),
            )

            return VideoResult(
                path=str(final_path),
                url=f"/generate/download/{job_id}",
            )
        except Exception as e:
            raise RuntimeError(f"VideoService.assemble failed: {e}") from e

    @classmethod
    def _build_filter_complex(cls, segment_count: int) -> str:
        w, h = Generation.VIDEO_WIDTH, Generation.VIDEO_HEIGHT
        audio_inputs = "".join(f"[{idx}:a]" for idx in range(1, segment_count + 1))
        return (
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=white,"
            f"setsar=1,fps=30[v];"
            f"{audio_inputs}concat=n={segment_count}:v=0:a=1[a]"
        )

    @classmethod
    def _build_image_concat_file(cls, segments: list[VideoSegment]) -> str:
        lines: list[str] = []
        for seg in segments:
            image_path = cls._escape_concat_path(Path(seg.image_path).resolve())
            lines.append(f"file '{image_path}'")
            lines.append(f"duration {max(seg.duration, 0.5):.6f}")

        # The concat demuxer needs the final frame repeated so the last duration is honored.
        final_image_path = cls._escape_concat_path(Path(segments[-1].image_path).resolve())
        lines.append(f"file '{final_image_path}'")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _escape_concat_path(path: Path) -> str:
        return path.as_posix().replace("'", "'\\''")

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
            tail = stderr.decode(errors="ignore")[-1000:]
            raise RuntimeError(f"ffmpeg exited {proc.returncode}: {tail}")
