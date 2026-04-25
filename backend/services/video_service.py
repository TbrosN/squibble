"""Assembles the per-line assets into a final .mp4 via ffmpeg."""

from __future__ import annotations

import asyncio
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from constants import Generation, Paths
from models.job import VideoResult


@dataclass
class VideoSegment:
    image_path: str
    audio_path: str
    duration: float


@dataclass(frozen=True)
class Crop:
    width: int
    height: int
    x: int
    y: int

    def is_full_frame(self, source: "ImageSize") -> bool:
        return (
            self.width == source.width
            and self.height == source.height
            and self.x == 0
            and self.y == 0
        )


@dataclass(frozen=True)
class ImageSize:
    width: int
    height: int


class VideoService:
    _CROP_RE = re.compile(r"crop=(?P<w>\d+):(?P<h>\d+):(?P<x>\d+):(?P<y>\d+)")
    _INPUT_SIZE_RE = re.compile(r"Video:.*?, (?P<w>\d+)x(?P<h>\d+)[,\s]")

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
            normalized_dir = job_dir / "normalized_frames"
            normalized_segments = await self._normalize_segments(segments, normalized_dir)

            await asyncio.to_thread(
                image_concat_path.write_text,
                self._build_image_concat_file(normalized_segments),
                encoding="utf-8",
            )

            audio_args = [arg for seg in normalized_segments for arg in ("-i", seg.audio_path)]
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
                self._build_filter_complex(len(normalized_segments)),
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

    async def _normalize_segments(
        self,
        segments: list[VideoSegment],
        normalized_dir: Path,
    ) -> list[VideoSegment]:
        await asyncio.to_thread(shutil.rmtree, normalized_dir, ignore_errors=True)
        await asyncio.to_thread(normalized_dir.mkdir, parents=True, exist_ok=True)

        normalized: list[VideoSegment] = []
        for idx, segment in enumerate(segments):
            image_path = Path(segment.image_path)
            crop, source_size = await self._detect_black_border_crop(image_path)
            if crop is None or source_size is None or crop.is_full_frame(source_size):
                normalized.append(segment)
                continue

            normalized_path = normalized_dir / f"frame_{idx:03d}.png"
            await self._normalize_image(image_path, normalized_path, crop, source_size)
            normalized.append(
                VideoSegment(
                    image_path=str(normalized_path),
                    audio_path=segment.audio_path,
                    duration=segment.duration,
                )
            )
        return normalized

    async def _normalize_image(
        self,
        image_path: Path,
        normalized_path: Path,
        crop: Crop,
        source_size: ImageSize,
    ) -> None:
        filters = [
            f"crop={crop.width}:{crop.height}:{crop.x}:{crop.y}",
            # Keep the concat input dimensions stable while replacing black bars with white.
            f"scale={source_size.width}:{source_size.height}:force_original_aspect_ratio=decrease",
            f"pad={source_size.width}:{source_size.height}:(ow-iw)/2:(oh-ih)/2:color=white",
            "setsar=1",
        ]

        await self._run_ffmpeg(
            "-y",
            "-i",
            str(image_path),
            "-vf",
            ",".join(filters),
            "-frames:v",
            "1",
            str(normalized_path),
        )

    async def _detect_black_border_crop(self, image_path: Path) -> tuple[Crop | None, ImageSize | None]:
        stderr = await self._run_ffmpeg_capture(
            "-hide_banner",
            "-v",
            "info",
            "-loop",
            "1",
            "-t",
            "0.2",
            "-i",
            str(image_path),
            "-vf",
            "cropdetect=limit=24:round=2:reset=0",
            "-frames:v",
            "3",
            "-f",
            "null",
            "-",
        )

        source_size = self._parse_input_size(stderr)
        crop = self._parse_last_crop(stderr)
        return crop, source_size

    @classmethod
    def _parse_last_crop(cls, ffmpeg_output: str) -> Crop | None:
        matches = list(cls._CROP_RE.finditer(ffmpeg_output))
        if not matches:
            return None

        match = matches[-1]
        return Crop(
            width=int(match.group("w")),
            height=int(match.group("h")),
            x=int(match.group("x")),
            y=int(match.group("y")),
        )

    @classmethod
    def _parse_input_size(cls, ffmpeg_output: str) -> ImageSize | None:
        match = cls._INPUT_SIZE_RE.search(ffmpeg_output)
        if match is None:
            return None
        return ImageSize(width=int(match.group("w")), height=int(match.group("h")))

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
        await VideoService._run_ffmpeg_capture(*args)

    @staticmethod
    async def _run_ffmpeg_capture(*args: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        output = stderr.decode(errors="ignore")
        if proc.returncode != 0:
            tail = output[-1000:]
            raise RuntimeError(f"ffmpeg exited {proc.returncode}: {tail}")
        return output
