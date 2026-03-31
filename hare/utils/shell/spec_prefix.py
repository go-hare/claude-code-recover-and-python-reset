"""
Shell spec prefix utilities.

Port of: src/utils/shell/specPrefix.ts + prefix.ts
"""

from __future__ import annotations

import os


def get_shell_env_prefix(env: dict[str, str] | None = None) -> str:
    """Build an environment variable export prefix for shell commands."""
    if not env:
        return ""
    parts = []
    for key, val in env.items():
        parts.append(f"export {key}={_shell_quote(val)}")
    return " && ".join(parts) + " && " if parts else ""


def _shell_quote(s: str) -> str:
    """Simple shell quoting."""
    if not s:
        return "''"
    if all(c.isalnum() or c in "-_./:" for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"
