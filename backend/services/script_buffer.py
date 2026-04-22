"""File-backed text buffer that implements Claude's text editor tool commands.

The buffer is a single plain-text file on disk (canonical location:
`output/<script_id>/script.txt`). Each spoken line is a physical line
terminated by a semicolon (`;`). Parsing into `ScriptLine[]` is a straight
`split(";")` + strip + filter-empty — see `parse_script`.

`ScriptBuffer` implements exactly the four commands Claude's
`str_replace_based_edit_tool` (version `text_editor_20250728`) can emit:
`view`, `create`, `str_replace`, `insert`. All file I/O is synchronous —
scripts are tiny (a few hundred bytes) and tool calls are bounded by
LLM latency anyway, so async I/O buys us nothing here.
"""

from __future__ import annotations

from pathlib import Path

from constants import Script
from models.script import ScriptLine


class ScriptBufferError(Exception):
    """Raised for invalid text-editor commands against the buffer."""


class ScriptBuffer:
    def __init__(self, path: Path) -> None:
        self._path = path
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

    @property
    def path(self) -> Path:
        return self._path

    @property
    def content(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def replace_content(self, new_content: str) -> None:
        """Force-set the file contents. Used to flush the canvas to disk
        before handing control to the model — not emitted into any message."""
        self._path.write_text(new_content, encoding="utf-8")

    def view(self, view_range: list[int] | None = None) -> str:
        content = self.content
        if not content:
            return "(empty file)"

        lines = content.split("\n")
        if view_range is None:
            start_idx, end_idx, offset = 0, len(lines), 0
        else:
            if len(view_range) != 2:
                raise ScriptBufferError("view_range must have exactly two entries.")
            start, end = view_range
            if start < 1 or start > len(lines):
                raise ScriptBufferError(
                    f"view_range start {start} is out of bounds (file has {len(lines)} lines)."
                )
            start_idx = start - 1
            end_idx = len(lines) if end == -1 else min(len(lines), end)
            if end_idx < start_idx:
                raise ScriptBufferError("view_range end must be >= start.")
            offset = start_idx
            lines = lines[start_idx:end_idx]

        return "\n".join(f"{offset + i + 1}: {line}" for i, line in enumerate(lines))

    def create(self, file_text: str) -> None:
        self._path.write_text(file_text, encoding="utf-8")

    def str_replace(self, old_str: str, new_str: str) -> None:
        if not old_str:
            raise ScriptBufferError("old_str must be non-empty.")

        content = self.content
        count = content.count(old_str)
        if count == 0:
            raise ScriptBufferError(
                "No match found for old_str. Call `view` to see the current file, "
                "then try again with exact text from the buffer."
            )
        if count > 1:
            raise ScriptBufferError(
                f"old_str matched {count} places. Extend it with a neighboring line "
                "so the match is unique."
            )
        self._path.write_text(content.replace(old_str, new_str, 1), encoding="utf-8")

    def insert(self, insert_line: int, new_str: str) -> None:
        content = self.content
        lines = content.split("\n") if content else []
        if insert_line < 0 or insert_line > len(lines):
            raise ScriptBufferError(
                f"insert_line {insert_line} is out of range (file has {len(lines)} lines); "
                "use 0 to insert at the top, N to insert after line N."
            )

        combined = lines[:insert_line] + new_str.split("\n") + lines[insert_line:]
        self._path.write_text("\n".join(combined), encoding="utf-8")


def parse_script(buffer_content: str) -> list[ScriptLine]:
    """Split the buffer into `ScriptLine`s on the terminator.

    IDs are positional — assigned at parse time, not stable across edits.
    """
    parts = [s.strip() for s in buffer_content.split(Script.LINE_TERMINATOR)]
    return [ScriptLine(id=i, line=text) for i, text in enumerate(p for p in parts if p)]


def serialize_script(lines: list[str]) -> str:
    """Format plain line strings into the canonical buffer shape.

    One script line per physical line, each terminated by `;`.
    """
    cleaned = [l.strip() for l in lines if l and l.strip()]
    if not cleaned:
        return ""
    return "\n".join(
        f"{l.rstrip(Script.LINE_TERMINATOR).rstrip()}{Script.LINE_TERMINATOR}"
        for l in cleaned
    )
