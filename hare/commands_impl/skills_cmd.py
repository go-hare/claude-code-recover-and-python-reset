"""
/skills command - list loaded skills.

Port of: src/commands/skills/index.ts
"""

from __future__ import annotations

import os
from typing import Any

from hare.skills.load_skills_dir import load_all_skills

COMMAND_NAME = "skills"
DESCRIPTION = "List loaded skills"


async def call(args: str, **context: Any) -> dict[str, Any]:
    project_dir = context.get("project_dir", os.getcwd())
    skills = load_all_skills(project_dir)

    if not skills:
        return {"type": "text", "value": "No skills loaded."}

    lines = ["Loaded skills:"]
    for skill in skills:
        lines.append(f"  - {skill.name}: {skill.description or '(no description)'}")
    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
