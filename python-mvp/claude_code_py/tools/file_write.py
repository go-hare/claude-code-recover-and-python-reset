from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_code_py.engine.context import ReadFileState, ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool
from claude_code_py.tools._text_files import normalize_newlines, read_text_file, write_text_file


class FileWriteTool(Tool):
    name = "Write"
    description = "Write a file to the local filesystem."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to write (must be absolute, not relative)",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["file_path", "content"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        path = context.resolve_path(str(tool_input["file_path"]))
        content = str(tool_input["content"])
        existed = path.exists()
        file_data = None

        if existed:
            stored = context.read_file_state.get(str(path))
            if stored is None or stored.is_partial_view:
                return ToolRunResult(
                    content="File has not been read yet. Read it first before writing to it.",
                    is_error=True,
                )
            file_data = read_text_file(path)
            original = file_data.content
            if path.stat().st_mtime > stored.timestamp and original != stored.content:
                return ToolRunResult(
                    content="File has been modified since read, either by the user or by a linter. Read it again before attempting to write it.",
                    is_error=True,
                )
        else:
            original = None

        if file_data is None:
            write_text_file(path, content)
        else:
            write_text_file(
                path,
                content,
                encoding=file_data.encoding,
                bom=file_data.bom,
            )
        context.read_file_state[str(path)] = ReadFileState(
            content=normalize_newlines(content),
            timestamp=path.stat().st_mtime,
            offset=None,
            limit=None,
        )

        if original is None:
            return ToolRunResult(content=f"File created successfully at: {path}")
        return ToolRunResult(content=f"The file {path} has been updated successfully.")
