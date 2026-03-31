"""
Skill Tool - invoke a loaded skill.

Port of: src/tools/SkillTool/SkillTool.ts
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "Skill"
DESCRIPTION = "Invoke a skill by name"


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "skill_name": {"type": "string", "description": "Name of the skill to invoke"},
            "input": {"type": "string", "description": "Input for the skill"},
        },
        "required": ["skill_name"],
    }


async def call(skill_name: str, input: str = "", **kwargs: Any) -> dict[str, Any]:
    from hare.skills.load_skills_dir import load_all_skills
    from hare.bootstrap.state import get_original_cwd

    skills = load_all_skills(get_original_cwd())
    for skill in skills:
        if skill.name == skill_name:
            return {"skill": skill_name, "content": skill.content, "status": "loaded"}
    return {"error": f"Skill '{skill_name}' not found"}
