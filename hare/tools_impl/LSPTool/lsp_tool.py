"""
LSP Tool - Language Server Protocol operations.

Port of: src/tools/LSPTool/LSPTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "LSP"
DESCRIPTION = "Query the Language Server Protocol for code intelligence"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["definition", "references", "hover", "completion", "diagnostics"],
                "description": "LSP action",
            },
            "file_path": {"type": "string", "description": "Path to the file"},
            "line": {"type": "integer", "description": "Line number (0-based)"},
            "character": {"type": "integer", "description": "Character position (0-based)"},
        },
        "required": ["action", "file_path"],
    }


async def call(
    action: str,
    file_path: str,
    line: int = 0,
    character: int = 0,
    **kwargs: Any,
) -> dict[str, Any]:
    return {
        "action": action,
        "file_path": file_path,
        "status": "not_available",
        "message": "LSP server not connected",
    }
