"""Recover and finalize the partially generated Haman Bible story video.

This is intentionally narrow: it fills the missing assets for the known failed
job, using a safer visual prompt for the line that tripped image moderation,
then re-assembles the full video.

Usage:
    uv run python scripts/complete_haman_video.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import Generation, Paths
from models.script import ScriptLine
from services.audio_service import AudioService, GoogleTtsAudioGenerator
from services.image_service import ImageService
from services.video_service import VideoSegment, VideoService


JOB_ID = "250566934547_haman_bible_story"
SAFE_LINE_33_VISUAL = (
    "A simple hand-drawn palace scene showing a shocked proud official beside "
    "a tall plain wooden platform, with a dramatic reversal arrow and surprised "
    "crowd. No violence, no hanging, no noose, no injury, no weapons."
)


def _load_script(job_dir: Path) -> list[ScriptLine]:
    payload = json.loads((job_dir / Paths.SCRIPT_FILENAME).read_text(encoding="utf-8"))
    return [ScriptLine.model_validate(item) for item in payload]


async def _ensure_audio(
    audio_service: AudioService,
    *,
    line: ScriptLine,
    job_dir: Path,
) -> Path:
    audio_path = job_dir / Generation.AUDIO_FILENAME_TEMPLATE.format(index=line.id)
    if audio_path.exists():
        print(f"audio_{line.id:02d}: exists")
        return audio_path

    await audio_service.generate(line, job_id=JOB_ID, job_dir=job_dir)
    print(f"audio_{line.id:02d}: generated")
    return audio_path


async def _ensure_image(
    image_service: ImageService,
    *,
    line: ScriptLine,
    job_dir: Path,
) -> Path:
    image_path = job_dir / Generation.IMAGE_FILENAME_TEMPLATE.format(index=line.id)
    if image_path.exists():
        print(f"image_{line.id:02d}: exists")
        return image_path

    image_line = line
    if line.id == 33:
        image_line = ScriptLine(id=line.id, line=SAFE_LINE_33_VISUAL)

    await image_service.generate(image_line, job_id=JOB_ID, job_dir=job_dir)
    print(f"image_{line.id:02d}: generated")
    return image_path


async def main() -> None:
    job_dir = Paths.OUTPUT_DIR / JOB_ID
    if not job_dir.exists():
        raise SystemExit(f"Job directory does not exist: {job_dir}")

    script = _load_script(job_dir)
    audio_service = AudioService(generator=GoogleTtsAudioGenerator())
    image_service = ImageService()
    video_service = VideoService()

    for line in script:
        await _ensure_audio(audio_service, line=line, job_dir=job_dir)
        await _ensure_image(image_service, line=line, job_dir=job_dir)

    segments = []
    for line in script:
        audio_path = job_dir / Generation.AUDIO_FILENAME_TEMPLATE.format(index=line.id)
        image_path = job_dir / Generation.IMAGE_FILENAME_TEMPLATE.format(index=line.id)
        duration = await asyncio.to_thread(AudioService._probe_duration, audio_path)
        segments.append(
            VideoSegment(
                image_path=str(image_path),
                audio_path=str(audio_path),
                duration=duration,
            )
        )

    result = await video_service.assemble(segments, JOB_ID, job_dir)
    print(f"Final video written to: {result.path}")
    print(f"Download URL path: {result.url}")


if __name__ == "__main__":
    asyncio.run(main())
