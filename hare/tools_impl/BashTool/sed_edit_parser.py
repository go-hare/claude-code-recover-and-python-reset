"""
Sed edit command parser.

Port of: src/tools/BashTool/sedEditParser.ts

Parses sed commands to determine if they perform in-place edits
and extracts the edit information.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SedEditInfo:
    """Information about a sed in-place edit."""
    is_in_place: bool = False
    file_paths: list[str] | None = None
    expressions: list[str] | None = None
    backup_suffix: str = ""


def is_sed_in_place_edit(command: str) -> bool:
    """Check if a sed command performs in-place file editing."""
    parts = command.strip().split()
    if not parts or parts[0] != "sed":
        return False
    for i, part in enumerate(parts):
        if part in ("-i", "--in-place"):
            return True
        if part.startswith("-i") and len(part) > 2:
            return True
    return False


def parse_sed_edit_command(command: str) -> SedEditInfo:
    """Parse a sed command and extract edit information."""
    info = SedEditInfo()
    parts = command.strip().split()

    if not parts or parts[0] != "sed":
        return info

    i = 1
    expressions = []
    file_paths = []

    while i < len(parts):
        part = parts[i]

        if part in ("-i", "--in-place"):
            info.is_in_place = True
            # Check for backup suffix
            if i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                # Could be backup suffix or expression
                next_part = parts[i + 1]
                if next_part.startswith(".") or next_part.startswith("~"):
                    info.backup_suffix = next_part
                    i += 1
        elif part.startswith("-i"):
            info.is_in_place = True
            info.backup_suffix = part[2:]
        elif part in ("-e", "--expression"):
            if i + 1 < len(parts):
                expressions.append(parts[i + 1])
                i += 1
        elif part in ("-f", "--file"):
            i += 1  # skip script file
        elif not part.startswith("-"):
            if not expressions:
                expressions.append(part)
            else:
                file_paths.append(part)
        i += 1

    info.expressions = expressions if expressions else None
    info.file_paths = file_paths if file_paths else None
    return info


def apply_sed_substitution(text: str, pattern: str, replacement: str, flags: str = "") -> str:
    """Apply a sed-like substitution to text."""
    re_flags = 0
    count = 1
    if "g" in flags:
        count = 0
    if "i" in flags or "I" in flags:
        re_flags |= re.IGNORECASE
    return re.sub(pattern, replacement, text, count=count, flags=re_flags)
