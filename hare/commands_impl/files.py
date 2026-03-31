"""Port of: src/commands/files.ts"""
from __future__ import annotations
import re
from typing import Any

COMMAND_NAME = "files"
DESCRIPTION = "List files referenced in the conversation"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    files: set[str] = set()
    file_pattern = re.compile(r'[\w./\\-]+\.\w{1,10}')
    for msg in messages:
        content = msg.get("message", {}).get("content", "")
        if isinstance(content, str):
            files.update(file_pattern.findall(content))
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "") or block.get("content", "")
                    if isinstance(text, str):
                        files.update(file_pattern.findall(text))
    sorted_files = sorted(files)
    display = "\n".join(sorted_files) if sorted_files else "No files referenced."
    return {"type": "files", "files": sorted_files, "display_text": display}
