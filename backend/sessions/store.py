"""In-memory registry of script-chat sessions.

A session identifies one in-progress script draft. It owns:
  * the on-disk script buffer (Claude edits via the text editor tool) at
    `output/<script_id>/script.txt`, and
  * the rolling Anthropic message history for that draft, including
    `tool_use` / `tool_result` blocks.

The frontend treats the returned `script_id` as an opaque handle and echoes
it on every subsequent chat request. The server restart story is "best
effort": if a known id shows up after a restart we rehydrate an empty
history against the existing file on disk, so the user can keep editing
(the model just re-views the file to catch up).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from constants import Paths
from services.script_buffer import ScriptBuffer


@dataclass
class ScriptSession:
    id: str
    buffer: ScriptBuffer
    # Raw Anthropic message dicts, alternating user/assistant. Tool_use blocks
    # live inside assistant messages; tool_result blocks live inside user
    # messages. We append to this across turns so the model has full context.
    history: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ScriptSession] = {}

    def get_or_create(self, script_id: str | None) -> ScriptSession:
        if script_id and script_id in self._sessions:
            return self._sessions[script_id]

        new_id = script_id or uuid.uuid4().hex[:12]
        path = Paths.OUTPUT_DIR / new_id / Paths.CHAT_SCRIPT_FILENAME
        session = ScriptSession(id=new_id, buffer=ScriptBuffer(path))
        self._sessions[new_id] = session
        return session

    def get(self, script_id: str) -> ScriptSession | None:
        return self._sessions.get(script_id)


session_store = SessionStore()
