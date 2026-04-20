"""Text-to-speech per-line audio generation via ElevenLabs."""

from __future__ import annotations

import asyncio
from pathlib import Path

from elevenlabs.client import AsyncElevenLabs
from mutagen.mp3 import MP3

from config import settings
from constants import Generation, Models
from models.job import AudioResult
from models.script import ScriptLine


class AudioService:
    def __init__(self) -> None:
        self._client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)

    async def generate(self, line: ScriptLine, job_id: str, job_dir: Path) -> AudioResult:
        try:
            filename = Generation.AUDIO_FILENAME_TEMPLATE.format(index=line.id)
            audio_path = job_dir / filename

            audio_stream = self._client.text_to_speech.convert(
                voice_id=Models.TTS_VOICE_ID,
                model_id=Models.TTS,
                text=line.line,
                output_format=Models.TTS_OUTPUT_FORMAT,
            )

            chunks: list[bytes] = []
            async for chunk in audio_stream:
                if chunk:
                    chunks.append(chunk)
            audio_bytes = b"".join(chunks)

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
    def _probe_duration(path: Path) -> float:
        try:
            return float(MP3(str(path)).info.length)
        except Exception:
            return 0.0
