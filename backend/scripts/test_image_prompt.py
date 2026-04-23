"""Lightweight harness for iterating on `Generation.IMAGE_STYLE_PREFIX`.

Runs `ImageService` directly against one or more sample spoken lines so you
can eyeball how prefix tweaks affect the result — no FastAPI, no frontend,
no video pipeline.

Usage:
    uv run python scripts/test_image_prompt.py "A cat napping on a keyboard"
    uv run python scripts/test_image_prompt.py -n 3 "A rocket launching"
    uv run python scripts/test_image_prompt.py \\
        --prefix "Pencil sketch, monochrome: " "A bicycle in the rain"
    uv run python scripts/test_image_prompt.py \\
        --prefix-file my_prefix.txt "A coffee shop" "A late-night commute"

Output:
    backend/output/_prompt_tests/image_YYYYMMDD_HHMMSS/
        prefix.txt                  # exact prefix used this run
        line_00_take_00.png ...     # one file per (line, take)
        manifest.txt                # line text <-> filename mapping
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import Generation, Paths
from models.script import ScriptLine
from services.image_service import ImageService


TEST_SUBDIR = "_prompt_tests"


async def _generate_one(
    service: ImageService,
    *,
    text: str,
    line_idx: int,
    take: int,
    job_id: str,
    job_dir: Path,
) -> Path:
    # ImageService derives the output filename from `line.id`, so give each
    # (line, take) a unique synthetic id to avoid collisions, then rename to
    # a human-readable form.
    synthetic = ScriptLine(id=line_idx * 1000 + take, line=text)
    result = await service.generate(synthetic, job_id=job_id, job_dir=job_dir)
    target = job_dir / f"line_{line_idx:02d}_take_{take:02d}.png"
    Path(result.path).rename(target)
    print(f"  ✓ {target.name}  —  {text}")
    return target


async def _run(lines: list[str], takes: int, prefix_override: str | None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = Paths.OUTPUT_DIR / TEST_SUBDIR / f"image_{timestamp}"
    job_dir.mkdir(parents=True, exist_ok=True)

    if prefix_override is not None:
        Generation.IMAGE_STYLE_PREFIX = prefix_override

    (job_dir / "prefix.txt").write_text(Generation.IMAGE_STYLE_PREFIX, encoding="utf-8")
    manifest_lines = [f"{i:02d}: {text}" for i, text in enumerate(lines)]
    (job_dir / "manifest.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    service = ImageService()
    tasks = [
        asyncio.create_task(
            _generate_one(
                service,
                text=text,
                line_idx=i,
                take=t,
                job_id=f"{TEST_SUBDIR}/image_{timestamp}",
                job_dir=job_dir,
            )
        )
        for i, text in enumerate(lines)
        for t in range(takes)
    ]
    await asyncio.gather(*tasks)
    return job_dir


def _resolve_prefix(args: argparse.Namespace) -> str | None:
    if args.prefix is not None and args.prefix_file is not None:
        raise SystemExit("Use either --prefix or --prefix-file, not both.")
    if args.prefix is not None:
        return args.prefix
    if args.prefix_file is not None:
        return Path(args.prefix_file).read_text(encoding="utf-8")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("lines", nargs="+", help="One or more spoken lines to illustrate.")
    parser.add_argument(
        "-n",
        "--takes",
        type=int,
        default=1,
        help="Images to generate per line (useful for seeing variance). Default: 1.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Override `IMAGE_STYLE_PREFIX` with an inline string for this run.",
    )
    parser.add_argument(
        "--prefix-file",
        default=None,
        help="Override `IMAGE_STYLE_PREFIX` with the contents of a file (handy for long prefixes).",
    )
    args = parser.parse_args()

    prefix_override = _resolve_prefix(args)
    print(f"Generating {len(args.lines)} line(s) × {args.takes} take(s)...")
    job_dir = asyncio.run(_run(args.lines, args.takes, prefix_override))
    print(f"\nDone. Open: {job_dir}")


if __name__ == "__main__":
    main()
