"""Lightweight harness for iterating on `Script.SYSTEM_PROMPT`.

Runs a chat turn (or an interactive loop) through `ScriptService` so you can
see how the model drafts and edits a script against your current system
prompt — without spinning up FastAPI or the frontend.

Usage:
    # One-shot: give a topic, see the drafted script + Claude's reply.
    uv run python scripts/test_script_prompt.py "why cats knock things off tables"

    # Interactive: keep the session open to try follow-up edits.
    uv run python scripts/test_script_prompt.py --interactive

    # Try a tweaked system prompt from a file without touching constants.py.
    uv run python scripts/test_script_prompt.py \\
        --system-file my_system_prompt.txt \\
        "explain the Fermi paradox"

    # Resume a draft created by an earlier run.
    uv run python scripts/test_script_prompt.py \\
        --script-id abc123def456 "make line 4 funnier"

Output:
    Numbered script lines printed to stdout.
    The assistant's textual reply printed after.
    The full buffer is left at backend/output/<script_id>/script.txt for inspection.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from constants import Script
from models.script import ScriptLine
from services.script_service import ScriptService


def _print_result(script_id: str, reply: str, lines: list[ScriptLine]) -> None:
    print(f"\n=== script  (id={script_id}, {len(lines)} line{'s' if len(lines) != 1 else ''}) ===")
    if not lines:
        print("  (empty)")
    for line in lines:
        print(f"  {line.id + 1:>3}  {line.line}")
    print("\n=== reply ===")
    print(reply or "(no textual reply)")


async def _one_shot(service: ScriptService, message: str, script_id: str | None) -> None:
    sid, reply, lines = await service.chat(
        script_id=script_id,
        message=message,
        canvas_lines=[],
        selected_lines=[],
    )
    _print_result(sid, reply, lines)


async def _interactive(service: ScriptService, script_id: str | None) -> None:
    print("Interactive mode. Enter a message, then Enter. Ctrl-D or Ctrl-C to quit.")
    sid = script_id
    while True:
        try:
            message = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not message:
            continue
        sid, reply, lines = await service.chat(
            script_id=sid,
            message=message,
            canvas_lines=[],
            selected_lines=[],
        )
        _print_result(sid, reply, lines)


def _resolve_system_prompt(args: argparse.Namespace) -> str | None:
    if args.system is not None and args.system_file is not None:
        raise SystemExit("Use either --system or --system-file, not both.")
    if args.system is not None:
        return args.system
    if args.system_file is not None:
        return Path(args.system_file).read_text(encoding="utf-8")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="User message (topic, edit request, etc.). Omit with --interactive.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Loop for follow-up turns using the same session.",
    )
    parser.add_argument(
        "--script-id",
        default=None,
        help="Resume an existing draft by id (matches a folder in backend/output/).",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Override `Script.SYSTEM_PROMPT` with an inline string for this run.",
    )
    parser.add_argument(
        "--system-file",
        default=None,
        help="Override `Script.SYSTEM_PROMPT` with the contents of a file.",
    )
    args = parser.parse_args()

    system_override = _resolve_system_prompt(args)
    if system_override is not None:
        Script.SYSTEM_PROMPT = system_override

    service = ScriptService()

    if args.interactive:
        asyncio.run(_interactive(service, args.script_id))
        return

    if not args.message:
        parser.error("message is required unless --interactive is set")
    asyncio.run(_one_shot(service, args.message, args.script_id))


if __name__ == "__main__":
    main()
