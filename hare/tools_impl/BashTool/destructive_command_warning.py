"""
Destructive command warnings.

Port of: src/tools/BashTool/destructiveCommandWarning.ts
"""

from __future__ import annotations

import re
from typing import Optional

DESTRUCTIVE_PATTERNS: list[tuple[str, str]] = [
    (r"git\s+push\s+.*--force", "Force push may overwrite remote history"),
    (r"git\s+push\s+-f\b", "Force push may overwrite remote history"),
    (r"git\s+reset\s+--hard", "Hard reset will discard uncommitted changes"),
    (r"git\s+clean\s+-[a-zA-Z]*f", "Git clean will permanently delete untracked files"),
    (r"rm\s+-rf\s+/", "Recursive force delete from root is extremely dangerous"),
    (r"rm\s+-rf\s+~", "Recursive force delete of home directory"),
    (r"rm\s+-rf\s+\.", "Recursive force delete of current directory"),
    (r">([\s]*)/dev/sd[a-z]", "Writing directly to disk device"),
    (r"mkfs\.", "Formatting a filesystem"),
    (r"dd\s+.*of=/dev/", "Direct disk write via dd"),
    (r"npm\s+publish", "Publishing package to npm registry"),
    (r"pip\s+upload", "Uploading package to PyPI"),
    (r"docker\s+system\s+prune\s+-a", "Removing all unused Docker data"),
]


def get_destructive_command_warning(command: str) -> Optional[str]:
    """Check if command matches destructive patterns and return warning message."""
    cmd = command.strip()
    for pattern, warning in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd):
            return warning
    return None
