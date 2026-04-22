"""Typed pydantic models for Claude's text editor tool (`str_replace_based_edit_tool`).

Used on both sides of the tool-use loop:
  * `EditorCommand` is a discriminated union over the four commands the model
    can emit (`view` / `create` / `str_replace` / `insert`). We parse the raw
    `tool_use.input` dict into this and then dispatch on the variant.
  * `ToolResultBlock` is the reply we append to the message history. Anthropic
    expects `{"type": "tool_result", "tool_use_id": ..., "content": ...,
    "is_error"?: true}` — `to_api_dict()` omits `is_error` when false so the
    payload stays tidy.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


class ViewCommand(BaseModel):
    command: Literal["view"]
    path: str
    view_range: list[int] | None = None


class CreateCommand(BaseModel):
    command: Literal["create"]
    path: str
    file_text: str


class StrReplaceCommand(BaseModel):
    command: Literal["str_replace"]
    path: str
    old_str: str
    new_str: str


class InsertCommand(BaseModel):
    command: Literal["insert"]
    path: str
    insert_line: int
    new_str: str


EditorCommand = Annotated[
    Union[ViewCommand, CreateCommand, StrReplaceCommand, InsertCommand],
    Field(discriminator="command"),
]


class ToolResultBlock(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: bool = False

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "tool_use_id": self.tool_use_id,
            "content": self.content,
        }
        if self.is_error:
            payload["is_error"] = True
        return payload
