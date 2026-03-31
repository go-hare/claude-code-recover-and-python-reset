"""
Brief Tool - send a brief/attachment to the user.

Port of: src/tools/BriefTool/BriefTool.ts
"""

from __future__ import annotations

import os
from typing import Any

TOOL_NAME = "Brief"
DESCRIPTION = "Upload or attach a file to the conversation"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to attach"},
            "description": {"type": "string", "description": "Description of the file"},
        },
        "required": ["file_path"],
    }


async def call(file_path: str, description: str = "", **kwargs: Any) -> dict[str, Any]:
    full_path = os.path.abspath(file_path)
    if not os.path.isfile(full_path):
        return {"error": f"File not found: {full_path}"}
    size = os.path.getsize(full_path)
    return {
        "path": full_path,
        "size": size,
        "description": description,
        "status": "attached",
    }
