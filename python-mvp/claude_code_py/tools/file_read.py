from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_code_py.engine.context import ReadFileState, ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool
from claude_code_py.tools._text_files import read_text_file

BLOCKED_DEVICE_PATHS = {
    "/dev/zero",
    "/dev/random",
    "/dev/urandom",
    "/dev/full",
    "/dev/stdin",
    "/dev/tty",
    "/dev/console",
    "/dev/stdout",
    "/dev/stderr",
    "/dev/fd/0",
    "/dev/fd/1",
    "/dev/fd/2",
}


class FileReadTool(Tool):
    name = "Read"
    description = "Read a file from the local filesystem."
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to read.",
            },
            "offset": {
                "type": "integer",
                "description": "The line number to start reading from. Only provide if the file is too large to read at once.",
            },
            "limit": {
                "type": "integer",
                "description": "The number of lines to read. Only provide if the file is too large to read at once.",
            },
        },
        "required": ["file_path"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        path = context.resolve_path(str(tool_input["file_path"]))
        offset = max(int(tool_input.get("offset", 1)), 0)
        limit_raw = tool_input.get("limit")
        limit = max(int(limit_raw), 1) if limit_raw is not None else None

        if _is_blocked_device_path(path.as_posix()):
            return ToolRunResult(
                content=f"Cannot read '{path}': this device file would block or produce infinite output.",
                is_error=True,
            )
        if path.is_dir():
            return ToolRunResult(
                content=f"Read can only read files, not directories. Use Bash to inspect directories: {path}",
                is_error=True,
            )
        if not path.exists():
            return ToolRunResult(
                content=f"File does not exist: {path}",
                is_error=True,
            )

        content = read_text_file(path).content
        lines = content.splitlines()
        total_lines = len(lines)
        start_index = 0 if offset == 0 else offset - 1
        selected = lines[start_index:] if limit is None else lines[start_index : start_index + limit]

        if not lines:
            rendered = (
                "<system-reminder>Warning: the file exists but the contents are empty.</system-reminder>"
            )
        elif not selected:
            rendered = (
                f"<system-reminder>Warning: the file exists but is shorter than the provided offset ({offset}). "
                f"The file has {total_lines} lines.</system-reminder>"
            )
        else:
            rendered = "\n".join(
                f"{line_number:>6}\t{line}"
                for line_number, line in enumerate(selected, start=offset)
            )

        context.read_file_state[str(path)] = ReadFileState(
            content=content,
            timestamp=path.stat().st_mtime,
            offset=offset,
            limit=limit,
        )
        return ToolRunResult(content=rendered[: context.max_output_chars])


def _is_blocked_device_path(file_path: str) -> bool:
    if file_path in BLOCKED_DEVICE_PATHS:
        return True
    if not file_path.startswith("/proc/"):
        return False
    return (
        file_path.endswith("/fd/0")
        or file_path.endswith("/fd/1")
        or file_path.endswith("/fd/2")
    )
