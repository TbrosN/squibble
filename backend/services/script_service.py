"""Claude-backed script collaboration service (Stage 1).

Uses Claude's text editor tool (`str_replace_based_edit_tool`,
version `text_editor_20250728`) so the model edits the script buffer via
targeted str_replace / insert / create operations instead of reprinting the
whole script every turn.

Per-turn flow:
  1. Resolve/create the session (keyed by `script_id`).
  2. Flush any pending canvas edits to the on-disk buffer. Silent — this is a
     filesystem write only; nothing is injected into the model's messages.
     If the model's next `str_replace` turns out to be stale, it'll fail, the
     model will `view` the file, and recover.
  3. Append the user's message to the rolling history.
  4. Run the tool-use loop: call the model, dispatch each tool_use via a
     typed pydantic command, append tool_result blocks, repeat until the
     model stops calling tools (or we hit MAX_TOOL_ITERATIONS).
  5. Parse the resulting file into `ScriptLine[]` and return.
"""

from __future__ import annotations

import logging
from typing import Any

from anthropic import AsyncAnthropic
from pydantic import TypeAdapter, ValidationError

from config import settings
from constants import Models, Script
from models.editor import (
    CreateCommand,
    EditorCommand,
    InsertCommand,
    StrReplaceCommand,
    ToolResultBlock,
    ViewCommand,
)
from models.script import ScriptLine
from services.script_buffer import (
    ScriptBuffer,
    ScriptBufferError,
    parse_script,
    serialize_script,
)
from sessions.store import ScriptSession, session_store

logger = logging.getLogger(__name__)

_command_adapter: TypeAdapter[EditorCommand] = TypeAdapter(EditorCommand)


class ScriptService:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self,
        *,
        script_id: str | None,
        message: str,
        canvas_lines: list[str],
        selected_lines: list[int],
    ) -> tuple[str, str, list[ScriptLine]]:
        session = session_store.get_or_create(script_id)

        # Silent file write: mirror the user's latest canvas into the buffer
        # so any direct edits they made between turns are what the model sees
        # when it `view`s the file. Not surfaced in any message.
        if canvas_lines:
            session.buffer.replace_content(serialize_script(canvas_lines))

        session.history.append(
            {"role": "user", "content": self._compose_user_message(message, selected_lines)}
        )

        try:
            reply = await self._run_tool_loop(session)
        except Exception as e:
            logger.error("ScriptService tool loop failed: %s", e)
            raise RuntimeError(f"ScriptService.chat failed: {e}") from e

        return session.id, reply, parse_script(session.buffer.content)

    @staticmethod
    def _compose_user_message(message: str, selected_lines: list[int]) -> str:
        """User's message plus a minimal positional hint when lines are selected.

        Deliberately does NOT include the text of those lines — the model can
        `view` the file if it needs to see them. Line numbers are 1-indexed to
        match the `view` output format.
        """
        if not selected_lines:
            return message
        nums = sorted({i + 1 for i in selected_lines if i >= 0})
        if not nums:
            return message
        label = "line" if len(nums) == 1 else "lines"
        return f"{message}\n\n[canvas: {label} {', '.join(str(n) for n in nums)} selected — focus edits there]"

    async def _run_tool_loop(self, session: ScriptSession) -> str:
        for _ in range(Script.MAX_TOOL_ITERATIONS):
            response = await self._client.messages.create(
                model=Models.SCRIPT,
                max_tokens=4096,
                system=Script.SYSTEM_PROMPT,
                tools=[Script.TEXT_EDITOR_TOOL],
                messages=session.history,
            )

            assistant_blocks = [block.model_dump() for block in response.content]
            session.history.append({"role": "assistant", "content": assistant_blocks})

            if response.stop_reason != "tool_use":
                return "".join(
                    b["text"] for b in assistant_blocks if b.get("type") == "text"
                ).strip()

            results: list[ToolResultBlock] = []
            for block in assistant_blocks:
                if block.get("type") != "tool_use":
                    continue
                results.append(
                    self._execute_tool_use(
                        tool_use_id=block["id"],
                        tool_input=block.get("input") or {},
                        buffer=session.buffer,
                    )
                )
            session.history.append(
                {"role": "user", "content": [r.to_api_dict() for r in results]}
            )

        logger.warning(
            "ScriptService hit MAX_TOOL_ITERATIONS (%d) without end_turn",
            Script.MAX_TOOL_ITERATIONS,
        )
        return (
            "I made several edits in a row and paused to keep things tidy. "
            "Take a look at the canvas and let me know what to tweak next."
        )

    @staticmethod
    def _execute_tool_use(
        *, tool_use_id: str, tool_input: dict[str, Any], buffer: ScriptBuffer
    ) -> ToolResultBlock:
        try:
            command = _command_adapter.validate_python(tool_input)
        except ValidationError as e:
            return ToolResultBlock(
                tool_use_id=tool_use_id,
                content=f"Invalid tool input: {e.errors(include_url=False)}",
                is_error=True,
            )

        try:
            if isinstance(command, ViewCommand):
                content = buffer.view(command.view_range)
            elif isinstance(command, CreateCommand):
                buffer.create(command.file_text)
                content = "File created successfully."
            elif isinstance(command, StrReplaceCommand):
                buffer.str_replace(command.old_str, command.new_str)
                content = "File edited successfully."
            elif isinstance(command, InsertCommand):
                buffer.insert(command.insert_line, command.new_str)
                content = "Text inserted successfully."
            else:
                # Should be unreachable given the discriminated union above.
                return ToolResultBlock(
                    tool_use_id=tool_use_id,
                    content=f"Unsupported command type: {type(command).__name__}",
                    is_error=True,
                )
        except ScriptBufferError as e:
            return ToolResultBlock(tool_use_id=tool_use_id, content=str(e), is_error=True)
        except Exception as e:
            logger.exception("Unexpected error executing editor command")
            return ToolResultBlock(
                tool_use_id=tool_use_id,
                content=f"Internal error: {e}",
                is_error=True,
            )

        return ToolResultBlock(tool_use_id=tool_use_id, content=content)
