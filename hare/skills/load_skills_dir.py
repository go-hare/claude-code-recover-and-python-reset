"""
Skills directory loading.

Port of: src/skills/loadSkillsDir.ts

Loads skill definitions from .claude/skills/ directories.
Skills are markdown files with metadata and instructions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SkillDefinition:
    """A loaded skill definition."""
    name: str = ""
    path: str = ""
    content: str = ""
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    source: str = ""  # "project" | "user"


def load_skills_dir(skills_dir: str, source: str = "project") -> list[SkillDefinition]:
    """
    Load all skill definitions from a skills directory.

    Each skill is a directory containing a SKILL.md file.
    The SKILL.md file contains the skill description and instructions.
    """
    skills: list[SkillDefinition] = []

    if not os.path.isdir(skills_dir):
        return skills

    for entry in sorted(os.listdir(skills_dir)):
        entry_path = os.path.join(skills_dir, entry)

        # Skill can be a directory with SKILL.md inside
        skill_md = os.path.join(entry_path, "SKILL.md")
        if os.path.isdir(entry_path) and os.path.isfile(skill_md):
            skill = _load_skill_file(skill_md, entry, source)
            if skill:
                skills.append(skill)
            continue

        # Or a .md file directly
        if entry.endswith(".md") and os.path.isfile(entry_path):
            name = entry[:-3]
            skill = _load_skill_file(entry_path, name, source)
            if skill:
                skills.append(skill)

    return skills


def _load_skill_file(
    path: str,
    name: str,
    source: str,
) -> Optional[SkillDefinition]:
    """Load a single skill file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    description = ""
    triggers: list[str] = []

    # Extract metadata from frontmatter-style content
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped and not description:
            description = stripped
            break

    return SkillDefinition(
        name=name,
        path=path,
        content=content,
        description=description,
        triggers=triggers,
        source=source,
    )


def get_project_skills_dir(cwd: str) -> str:
    """Get the project-level skills directory."""
    return os.path.join(cwd, ".claude", "skills")


def get_user_skills_dir() -> str:
    """Get the user-level skills directory."""
    return os.path.join(os.path.expanduser("~"), ".claude", "skills")


def load_all_skills(cwd: str) -> list[SkillDefinition]:
    """Load skills from both project and user directories."""
    skills: list[SkillDefinition] = []

    # Project skills take priority
    project_dir = get_project_skills_dir(cwd)
    skills.extend(load_skills_dir(project_dir, "project"))

    # User-level skills
    user_dir = get_user_skills_dir()
    skills.extend(load_skills_dir(user_dir, "user"))

    return skills
