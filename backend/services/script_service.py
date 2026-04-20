"""Claude-backed script collaboration service for Stage 1."""

from __future__ import annotations

import json

from anthropic import AsyncAnthropic

from config import settings
from constants import Models, Script
from models.script import ChatMessage, ScriptLine


class ScriptService:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self,
        messages: list[ChatMessage],
        selected_lines: list[int],
        current_script: list[ScriptLine],
    ) -> tuple[str, list[ScriptLine]]:
        try:
            context_message = self._build_context_message(selected_lines, current_script)
            anthropic_messages = [
                {"role": m.role, "content": m.content} for m in messages
            ]
            anthropic_messages.append({"role": "user", "content": context_message})

            response = await self._client.messages.create(
                model=Models.SCRIPT,
                max_tokens=4096,
                system=Script.SYSTEM_PROMPT,
                messages=anthropic_messages,
            )

            raw = "".join(block.text for block in response.content if block.type == "text")
            return self._parse_response(raw)
        except Exception as e:
            raise RuntimeError(f"ScriptService.chat failed: {e}") from e

    @staticmethod
    def _build_context_message(
        selected_lines: list[int],
        current_script: list[ScriptLine],
    ) -> str:
        payload = {
            "current_script": [line.model_dump() for line in current_script],
            "selected_lines": selected_lines,
        }
        return (
            "[Canvas state snapshot — treat `current_script` as ground truth and preserve "
            "unrelated lines verbatim. If `selected_lines` is non-empty, focus edits there.]\n"
            f"{json.dumps(payload)}"
        )

    @staticmethod
    def _parse_response(raw: str) -> tuple[str, list[ScriptLine]]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("ScriptService: model did not return JSON object")

        data = json.loads(cleaned[start : end + 1])
        reply = str(data.get("reply", "")).strip()
        raw_script = data.get("script", [])

        script: list[ScriptLine] = []
        for idx, item in enumerate(raw_script):
            line_id = item.get("id", idx)
            script.append(
                ScriptLine(
                    id=int(line_id),
                    line=str(item.get("line", "")).strip(),
                    image_prompt=str(item.get("image_prompt", "")).strip(),
                )
            )
        return reply, script
