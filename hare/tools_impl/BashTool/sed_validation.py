"""
Sed command validation.

Port of: src/tools/BashTool/sedValidation.ts

Validates sed commands against permission rules and safety constraints.
"""

from __future__ import annotations

import re
from typing import Any, Sequence

from hare.tools_impl.BashTool.sed_edit_parser import is_sed_in_place_edit, parse_sed_edit_command


def sed_command_is_allowed_by_allowlist(
    command: str,
    allow_rules: Sequence[str],
) -> bool:
    """Check if a sed command is allowed by the permission allowlist."""
    if not is_sed_in_place_edit(command):
        return True

    info = parse_sed_edit_command(command)
    if not info.file_paths:
        return False

    from hare.tools_impl.BashTool.bash_permissions import check_bash_permission
    result = check_bash_permission(command, list(allow_rules), is_allow=True)
    return result.get("matched", False)


def check_sed_constraints(
    command: str,
    *,
    working_directory: str = "",
) -> dict[str, Any]:
    """Check safety constraints on a sed command."""
    if not is_sed_in_place_edit(command):
        return {"safe": True}

    info = parse_sed_edit_command(command)

    if _contains_dangerous_operations(command):
        return {"safe": False, "reason": "Sed command contains dangerous operations"}

    return {"safe": True}


def is_line_printing_command(command: str) -> bool:
    """Check if sed command only prints lines (not modifying)."""
    parts = command.strip().split()
    if not parts or parts[0] != "sed":
        return False
    return "-n" in parts and any("p" in p for p in parts if not p.startswith("-"))


def _contains_dangerous_operations(command: str) -> bool:
    """Check for dangerous sed operations."""
    dangerous_patterns = [
        r"sed\s+.*['\"].*[|&;`$]",  # shell injection in sed expression
        r"sed\s+.*e\b",  # execute command flag
        r"sed\s+.*w\s+/",  # write to absolute path
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return True
    return False
