"""
/memory command - edit Claude memory files.

Port of: src/commands/memory/index.ts
"""

from __future__ import annotations

import os
from typing import Any

from hare.services.session_memory import MEMORY_FILE_NAME

COMMAND_NAME = "memory"
DESCRIPTION = "Edit Claude memory files"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /memory command."""
    project_dir = context.get("project_dir", os.getcwd())

    project_memory = os.path.join(project_dir, MEMORY_FILE_NAME)
    user_memory = os.path.join(os.path.expanduser("~"), ".claude", MEMORY_FILE_NAME)

    lines = ["Memory files:"]

    # User memory
    if os.path.isfile(user_memory):
        with open(user_memory, "r", encoding="utf-8") as f:
            content = f.read()
        lines.append(f"\n[User] {user_memory} ({len(content)} chars)")
    else:
        lines.append(f"\n[User] {user_memory} (not created)")

    # Project memory
    if os.path.isfile(project_memory):
        with open(project_memory, "r", encoding="utf-8") as f:
            content = f.read()
        lines.append(f"[Project] {project_memory} ({len(content)} chars)")
    else:
        lines.append(f"[Project] {project_memory} (not created)")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
