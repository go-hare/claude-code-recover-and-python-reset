from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool


class GlobTool(Tool):
    name = "Glob"
    description = "Find files by glob pattern."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match."},
            "path": {
                "type": "string",
                "description": "Optional base directory. Defaults to the current working directory.",
            },
        },
        "required": ["pattern"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        pattern = str(tool_input["pattern"])
        base_path = context.resolve_path(str(tool_input.get("path", ".")))
        matches = [
            path
            for path in base_path.glob(pattern)
            if path.is_file()
        ]
        if not matches:
            return ToolRunResult(content="No files found")
        matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        relative_matches = [path.relative_to(base_path).as_posix() for path in matches]
        return ToolRunResult(
            content="\n".join(relative_matches)[: context.max_output_chars]
        )
