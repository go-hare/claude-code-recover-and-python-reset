"""
/diff command - view uncommitted changes.

Port of: src/commands/diff/index.ts
"""

from __future__ import annotations

from typing import Any

from hare.utils.git_diff import fetch_git_diff

COMMAND_NAME = "diff"
DESCRIPTION = "View uncommitted changes and per-turn diffs"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /diff command."""
    result = await fetch_git_diff()
    if not result:
        return {"type": "text", "value": "No git changes found (or not in a git repo)."}

    lines = [f"Git diff: {result.stats.files_changed} files changed"]
    if result.stats.insertions:
        lines.append(f"  +{result.stats.insertions} insertions")
    if result.stats.deletions:
        lines.append(f"  -{result.stats.deletions} deletions")

    if result.per_file:
        lines.append("\nChanged files:")
        for f in result.per_file:
            lines.append(f"  {f.file_path} (+{f.insertions}/-{f.deletions})")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
