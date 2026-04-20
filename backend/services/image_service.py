"""Per-line image generation via Gemini 2.5 Flash Image (Nano Banana)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from google import genai
from google.genai import types

from config import settings
from constants import Generation, Models
from models.job import ImageResult
from models.script import ScriptLine


class ImageService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(self, line: ScriptLine, job_id: str, job_dir: Path) -> ImageResult:
        try:
            filename = Generation.IMAGE_FILENAME_TEMPLATE.format(index=line.id)
            image_path = job_dir / filename
            prompt = f"{Generation.IMAGE_STYLE_PREFIX}{line.image_prompt}"

            response = await self._client.aio.models.generate_content(
                model=Models.IMAGE,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="1:1"),
                ),
            )

            image_bytes = self._extract_image_bytes(response)
            await asyncio.to_thread(image_path.write_bytes, image_bytes)

            return ImageResult(
                path=str(image_path),
                url=f"/generate/asset/{job_id}/{filename}",
            )
        except Exception as e:
            raise RuntimeError(f"ImageService failed on line {line.id}: {e}") from e

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
