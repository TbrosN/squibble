"""Per-line image generation via Gemini 2.5 Flash Image (Nano Banana)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from google import genai
from google.genai import types

from config import settings
from constants import Generation, Models, StopMotion
from models.job import ImageResult
from models.script import ScriptLine


class ImageService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, line: ScriptLine, job_id: str, job_dir: Path) -> ImageResult:
        try:
            filename = Generation.IMAGE_FILENAME_TEMPLATE.format(index=line.id)
            image_path = job_dir / filename
            prompt = f"{Generation.IMAGE_STYLE_PREFIX}{line.line}"

            response = await self._client.aio.models.generate_content(
                model=Models.IMAGE,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=Generation.IMAGE_ASPECT_RATIO),
                ),
            )

            image_bytes = self._extract_image_bytes(response)
            await self._write_image(image_path, image_bytes)

            return ImageResult(
                path=str(image_path),
                url=f"/generate/asset/{job_id}/{filename}",
            )
        except Exception as e:
            raise RuntimeError(f"ImageService failed on line {line.id}: {e}") from e

    async def restyle_frame(
        self,
        *,
        frame_path: Path,
        output_path: Path,
        style_prompt: str,
    ) -> None:
        try:
            prompt = StopMotion.RESTYLE_PROMPT_TEMPLATE.format(
                style_prompt=style_prompt.strip(),
            )
            frame_bytes = await asyncio.to_thread(frame_path.read_bytes)

            response = await self._client.aio.models.generate_content(
                model=Models.STOP_MOTION_IMAGE,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=frame_bytes, mime_type="image/png"),
                ],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )

            image_bytes = self._extract_image_bytes(response)
            await self._write_image(output_path, image_bytes)
        except Exception as e:
            raise RuntimeError(f"ImageService failed restyling {frame_path.name}: {e}") from e

    @staticmethod
    def _extract_image_bytes(response) -> bytes:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None) if inline else None
                if data:
                    return data if isinstance(data, bytes) else bytes(data)
        raise RuntimeError("Gemini response contained no image data")

    @classmethod
    async def _write_image(cls, output_path: Path, image_bytes: bytes) -> None:
        if output_path.suffix.lower() != ".png" or cls._is_png(image_bytes):
            await asyncio.to_thread(output_path.write_bytes, image_bytes)
            return

        await cls._transcode_to_png(output_path, image_bytes)

    @staticmethod
    def _is_png(image_bytes: bytes) -> bool:
        return image_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    @classmethod
    async def _transcode_to_png(cls, output_path: Path, image_bytes: bytes) -> None:
        source_path = output_path.with_name(
            f".{output_path.stem}.{uuid4().hex}{cls._source_suffix(image_bytes)}"
        )
        try:
            await asyncio.to_thread(source_path.write_bytes, image_bytes)
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-y",
                "-i",
                str(source_path),
                "-frames:v",
                "1",
                str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                output = stderr.decode(errors="ignore")[-1000:]
                raise RuntimeError(f"ffmpeg could not normalize generated image to PNG: {output}")
        finally:
            await asyncio.to_thread(source_path.unlink, missing_ok=True)

    @staticmethod
    def _source_suffix(image_bytes: bytes) -> str:
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            return ".webp"
        return ".img"
