"""Test stop-motion frame image generation against a single input image.

Runs the same Gemini image-restyling path used by the stop-motion video
pipeline, but only for one still frame so prompt tweaks are cheap to inspect.

Usage:
    uv run python scripts/test_stop_motion_image_generation.py
    uv run python scripts/test_stop_motion_image_generation.py "tiny pieces of felt"
    uv run python scripts/test_stop_motion_image_generation.py -n 3 "colorful modeling clay"
    uv run python scripts/test_stop_motion_image_generation.py \
        --input scripts/input.png "paper cutouts" "lego bricks"

Output:
    backend/output/_stop_motion_image_tests/restyle_YYYYMMDD_HHMMSS/
        input.png
        manifest.txt
        prompt_00_take_00.png ...
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from constants import Paths
from services.image_service import ImageService


DEFAULT_STYLE_PROMPT = "colorful modeling clay"
TEST_SUBDIR = "_stop_motion_image_tests"


async def _restyle_one(
    service: ImageService,
    *,
    input_path: Path,
    output_path: Path,
    style_prompt: str,
    prompt_idx: int,
    take: int,
) -> Path:
    await service.restyle_frame(
        frame_path=input_path,
        output_path=output_path,
        style_prompt=style_prompt,
    )
    print(f"  ✓ prompt {prompt_idx:02d}, take {take:02d}: {output_path.name}")
    return output_path


async def _run(input_path: Path, style_prompts: list[str], takes: int) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = BACKEND_DIR / Paths.OUTPUT_DIR / TEST_SUBDIR / f"restyle_{timestamp}"
    job_dir.mkdir(parents=True, exist_ok=True)

    copied_input = job_dir / input_path.name
    shutil.copy2(input_path, copied_input)

    manifest_lines = [
        f"input: {copied_input}",
        "",
        "prompts:",
        *[f"{idx:02d}: {prompt}" for idx, prompt in enumerate(style_prompts)],
    ]
    (job_dir / "manifest.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    service = ImageService()
    tasks = []
    for prompt_idx, style_prompt in enumerate(style_prompts):
        for take in range(takes):
            output_path = job_dir / f"prompt_{prompt_idx:02d}_take_{take:02d}.png"
            tasks.append(
                asyncio.create_task(
                    _restyle_one(
                        service,
                        input_path=input_path,
                        output_path=output_path,
                        style_prompt=style_prompt,
                        prompt_idx=prompt_idx,
                        take=take,
                    )
                )
            )

    await asyncio.gather(*tasks)
    return job_dir


def _resolve_input(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = BACKEND_DIR / candidate
    candidate = candidate.resolve()
    if not candidate.exists():
        raise SystemExit(f"Input image does not exist: {candidate}")
    if not candidate.is_file():
        raise SystemExit(f"Input path is not a file: {candidate}")
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "style_prompts",
        nargs="*",
        default=[DEFAULT_STYLE_PROMPT],
        help=(
            "One or more material/style prompts to apply. "
            f"Default: {DEFAULT_STYLE_PROMPT!r}."
        ),
    )
    parser.add_argument(
        "--input",
        default="scripts/input.png",
        help="Input frame image, relative to backend/ unless absolute. Default: scripts/input.png.",
    )
    parser.add_argument(
        "-n",
        "--takes",
        type=int,
        default=1,
        help="Images to generate per prompt. Default: 1.",
    )
    args = parser.parse_args()

    if args.takes < 1:
        raise SystemExit("--takes must be at least 1")

    input_path = _resolve_input(args.input)
    print(f"Restyling {input_path} with {len(args.style_prompts)} prompt(s) × {args.takes} take(s)...")
    job_dir = asyncio.run(_run(input_path, args.style_prompts, args.takes))
    print(f"\nDone. Open: {job_dir}")


if __name__ == "__main__":
    main()
