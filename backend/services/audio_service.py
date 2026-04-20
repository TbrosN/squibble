"""Text-to-speech per-line audio generation."""

from __future__ import annotations

import asyncio
from pathlib import Path

from mutagen.mp3 import MP3
from openai import AsyncOpenAI

from config import settings
from constants import Generation, Models
from models.job import AudioResult
from models.script import ScriptLine


class AudioService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, line: ScriptLine, job_id: str, job_dir: Path) -> AudioResult:
        try:
            filename = Generation.AUDIO_FILENAME_TEMPLATE.format(index=line.id)
            audio_path = job_dir / filename

            response = await self._client.audio.speech.create(
                model=Models.TTS,
                voice=Models.TTS_VOICE,
                input=line.line,
                response_format="mp3",
            )
            audio_bytes = await self._read_bytes(response)

            await asyncio.to_thread(audio_path.write_bytes, audio_bytes)
            duration = await asyncio.to_thread(self._probe_duration, audio_path)

            return AudioResult(
                path=str(audio_path),
                url=f"/generate/asset/{job_id}/{filename}",
                duration=duration,
            )
        except Exception as e:
            raise RuntimeError(f"AudioService failed on line {line.id}: {e}") from e

    @staticmethod
    async def _read_bytes(response) -> bytes:
        if hasattr(response, "aread"):
            return await response.aread()
        if hasattr(response, "read"):
            data = response.read()
            if asyncio.iscoroutine(data):
                return await data
            return data
        return response.content

    @staticmethod
    def _probe_duration(path: Path) -> float:
        try:
            return float(MP3(str(path)).info.length)
        except Exception:
            return 0.0
