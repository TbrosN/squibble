"""Per-line image generation via Replicate (flux-schnell)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import replicate

from config import settings
from constants import Generation, Models
from models.job import ImageResult
from models.script import ScriptLine


class ImageService:
    def __init__(self) -> None:
        self._client = replicate.Client(api_token=settings.replicate_api_token)

    async def generate(self, line: ScriptLine, job_id: str, job_dir: Path) -> ImageResult:
        try:
            filename = Generation.IMAGE_FILENAME_TEMPLATE.format(index=line.id)
            image_path = job_dir / filename
            prompt = f"{Generation.IMAGE_STYLE_PREFIX}{line.image_prompt}"

            output = await asyncio.to_thread(
                self._client.run,
                Models.IMAGE,
                input={
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "output_format": "png",
                    "num_outputs": 1,
                },
            )

            image_bytes = await self._read_output(output)
            await asyncio.to_thread(image_path.write_bytes, image_bytes)

            return ImageResult(
                path=str(image_path),
                url=f"/generate/asset/{job_id}/{filename}",
            )
        except Exception as e:
            raise RuntimeError(f"ImageService failed on line {line.id}: {e}") from e

    @staticmethod
    async def _read_output(output) -> bytes:
        first = output[0] if isinstance(output, list) else output

        if hasattr(first, "read"):
            data = await asyncio.to_thread(first.read)
            return data if isinstance(data, bytes) else bytes(data)

        url = str(first)
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.content
