"""
Diff utilities.

Port of: src/utils/diff.ts

Computes and formats unified diffs for file edits.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hunk:
    """A single diff hunk."""
    old_start: int = 0
    old_lines: int = 0
    new_start: int = 0
    new_lines: int = 0
    lines: list[str] = field(default_factory=list)


def get_patch_for_display(
    *,
    file_path: str,
    file_contents: str,
    edits: list[dict[str, Any]],
) -> list[Hunk]:
    """
    Compute a structured patch from a list of edits.
    Mirrors getPatchForDisplay() in diff.ts.
    """
    old_content = file_contents
    new_content = old_content

    for edit in edits:
        old_str = edit.get("old_string", "")
        new_str = edit.get("new_string", "")
        replace_all = edit.get("replace_all", False)

        if replace_all:
            new_content = new_content.replace(old_str, new_str)
        else:
            new_content = new_content.replace(old_str, new_str, 1)

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    hunks: list[Hunk] = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    for group in matcher.get_grouped_opcodes(3):
        hunk = Hunk()
        first = group[0]
        last = group[-1]

        hunk.old_start = first[1] + 1
        hunk.new_start = first[3] + 1

        lines: list[str] = []
        old_count = 0
        new_count = 0

        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for line in old_lines[i1:i2]:
                    lines.append(f" {line.rstrip()}")
                    old_count += 1
                    new_count += 1
            elif tag == "delete":
                for line in old_lines[i1:i2]:
                    lines.append(f"-{line.rstrip()}")
                    old_count += 1
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    lines.append(f"+{line.rstrip()}")
                    new_count += 1
            elif tag == "replace":
                for line in old_lines[i1:i2]:
                    lines.append(f"-{line.rstrip()}")
                    old_count += 1
                for line in new_lines[j1:j2]:
                    lines.append(f"+{line.rstrip()}")
                    new_count += 1

        hunk.old_lines = old_count
        hunk.new_lines = new_count
        hunk.lines = lines
        hunks.append(hunk)

    return hunks


def count_lines_changed(
    hunks: list[Hunk],
    new_content: str | None = None,
) -> tuple[int, int]:
    """
    Count lines added and removed from a patch.
    Returns (lines_added, lines_removed).
    """
    added = 0
    removed = 0

    if new_content is not None and not hunks:
        # New file: all lines are additions
        added = new_content.count("\n") + (1 if not new_content.endswith("\n") else 0)
        return added, removed

    for hunk in hunks:
        for line in hunk.lines:
            if line.startswith("+"):
                added += 1
            elif line.startswith("-"):
                removed += 1

    return added, removed
