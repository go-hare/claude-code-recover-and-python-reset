"""
Bundled skill definitions.

Port of: src/skills/bundled/index.ts + individual skill files
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BundledSkill:
    name: str
    description: str
    content: str


_SKILLS: dict[str, BundledSkill] = {}


def register_bundled_skill(skill: BundledSkill) -> None:
    _SKILLS[skill.name] = skill


def get_bundled_skill(name: str) -> Optional[BundledSkill]:
    return _SKILLS.get(name)


def get_all_bundled_skills() -> list[BundledSkill]:
    return list(_SKILLS.values())


# Register built-in skills
_BUILTIN = [
    BundledSkill(
        name="verify",
        description="Run verification checks after making changes",
        content="After making changes, run relevant tests and linters to verify correctness.",
    ),
    BundledSkill(
        name="stuck",
        description="Try alternative approaches when stuck",
        content="If you've tried the same approach multiple times without success, step back and try a fundamentally different approach.",
    ),
    BundledSkill(
        name="simplify",
        description="Simplify complex code",
        content="Look for opportunities to simplify. Remove unnecessary abstractions. Prefer straightforward solutions.",
    ),
    BundledSkill(
        name="debug",
        description="Systematic debugging approach",
        content="When debugging: 1) Reproduce the issue 2) Read error messages carefully 3) Add logging 4) Form hypothesis 5) Test hypothesis 6) Fix root cause.",
    ),
    BundledSkill(
        name="loop",
        description="Iterative improvement loop",
        content="Make a change, test it, observe the result, adjust. Repeat until the goal is met.",
    ),
    BundledSkill(
        name="remember",
        description="Save important context to memory",
        content="When you learn something important about the project or user preferences, save it to CLAUDE.md for future sessions.",
    ),
    BundledSkill(
        name="batch",
        description="Process multiple items efficiently",
        content="When handling multiple similar items, batch them together for efficiency rather than processing one at a time.",
    ),
    BundledSkill(
        name="keybindings",
        description="Claude Code keyboard shortcuts",
        content="Key bindings: Ctrl+C to cancel, Ctrl+D to exit, Tab to accept suggestion, Up/Down for history.",
    ),
    BundledSkill(
        name="claude-api",
        description="Anthropic API usage guide",
        content="Use the Anthropic Python SDK: from anthropic import Anthropic. Create a client and call messages.create().",
    ),
    BundledSkill(
        name="skillify",
        description="Create custom skills",
        content="Create .md files in ~/.claude/skills/ with frontmatter and instructions to extend Claude's capabilities.",
    ),
    BundledSkill(
        name="update-config",
        description="Update Claude configuration",
        content="Configuration files: ~/.claude/settings.json (user), .claude/settings.json (project), CLAUDE.md (memory).",
    ),
    BundledSkill(
        name="lorem-ipsum",
        description="Generate placeholder text",
        content="Generate Lorem Ipsum placeholder text for UI development and testing.",
    ),
    BundledSkill(
        name="schedule-remote-agents",
        description="Schedule and manage remote agents",
        content="Create scheduled tasks that run agents at specified intervals.",
    ),
    BundledSkill(
        name="claude-in-chrome",
        description="Use Claude in Chrome browser",
        content="Open Claude at claude.ai in Chrome for web-based interaction.",
    ),
]

for _s in _BUILTIN:
    register_bundled_skill(_s)
