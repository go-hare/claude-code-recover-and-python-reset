"""
Path validation for bash commands.

Port of: src/tools/BashTool/pathValidation.ts

Validates file paths referenced in commands to ensure they don't
escape the working directory or access sensitive locations.
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional, Sequence

SENSITIVE_PATHS = frozenset({
    "/etc/passwd", "/etc/shadow", "/etc/sudoers",
    "/etc/ssh", "/root/.ssh", "~/.ssh",
    "/etc/hosts", "/etc/resolv.conf",
})

SENSITIVE_DIRECTORIES = frozenset({
    "/", "/etc", "/usr", "/bin", "/sbin",
    "/var", "/tmp", "/root", "/boot", "/dev", "/proc", "/sys",
})


def check_path_constraints(
    command: str,
    *,
    working_directory: str = "",
    allowed_directories: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """
    Check if paths in a command are within allowed boundaries.

    Returns dict with 'safe' bool and optional 'reason' and 'paths'.
    """
    paths = extract_paths_from_command(command)
    if not paths:
        return {"safe": True, "paths": []}

    violations = []
    for path in paths:
        resolved = _resolve_path(path, working_directory)

        # Check sensitive paths
        if resolved in SENSITIVE_PATHS or any(resolved.startswith(s + "/") for s in SENSITIVE_PATHS):
            violations.append(f"Accesses sensitive path: {path}")
            continue

        # Check if path escapes working directory
        if working_directory and allowed_directories is not None:
            all_allowed = [working_directory] + list(allowed_directories)
            if not any(resolved.startswith(d) for d in all_allowed):
                violations.append(f"Path {path} is outside allowed directories")

    if violations:
        return {"safe": False, "reason": "; ".join(violations), "paths": paths}
    return {"safe": True, "paths": paths}


def extract_paths_from_command(command: str) -> list[str]:
    """Extract file paths from a command string."""
    paths = []
    # Match quoted paths
    for m in re.finditer(r'["\']([^"\']+)["\']', command):
        candidate = m.group(1)
        if "/" in candidate or "\\" in candidate:
            paths.append(candidate)

    # Match unquoted absolute paths
    for m in re.finditer(r'(?<!\w)(/[\w./-]+)', command):
        paths.append(m.group(1))

    # Match ~ paths
    for m in re.finditer(r'(?<!\w)(~[\w./-]*)', command):
        paths.append(m.group(1))

    return paths


def _resolve_path(path: str, working_directory: str) -> str:
    """Resolve a path relative to the working directory."""
    if path.startswith("~"):
        path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(working_directory or os.getcwd(), path)
    return os.path.normpath(path)
