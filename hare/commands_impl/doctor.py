"""
/doctor command - diagnose and verify installation.

Port of: src/commands/doctor/index.ts
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Any

COMMAND_NAME = "doctor"
DESCRIPTION = "Diagnose and verify your Claude Code installation and settings"


async def call(args: str, **context: Any) -> dict[str, Any]:
    """Execute the /doctor command."""
    checks: list[dict[str, Any]] = []

    # Python version
    py_ver = sys.version
    checks.append({
        "name": "Python version",
        "status": "ok" if sys.version_info >= (3, 11) else "warn",
        "detail": py_ver,
    })

    # Git available
    git_path = shutil.which("git")
    checks.append({
        "name": "Git",
        "status": "ok" if git_path else "error",
        "detail": git_path or "not found",
    })

    # API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    checks.append({
        "name": "API key",
        "status": "ok" if api_key else "error",
        "detail": f"{'set' if api_key else 'not set'} (ANTHROPIC_API_KEY)",
    })

    # Settings files
    home = os.path.expanduser("~")
    user_settings = os.path.join(home, ".claude", "settings.json")
    checks.append({
        "name": "User settings",
        "status": "ok" if os.path.isfile(user_settings) else "info",
        "detail": user_settings,
    })

    # Memory file
    user_memory = os.path.join(home, ".claude", "CLAUDE.md")
    checks.append({
        "name": "User memory",
        "status": "ok" if os.path.isfile(user_memory) else "info",
        "detail": user_memory,
    })

    lines = ["Doctor Report:"]
    for check in checks:
        icon = {"ok": "✓", "warn": "⚠", "error": "✗", "info": "ℹ"}[check["status"]]
        lines.append(f"  {icon} {check['name']}: {check['detail']}")

    errors = [c for c in checks if c["status"] == "error"]
    if errors:
        lines.append(f"\n{len(errors)} issue(s) found.")
    else:
        lines.append("\nAll checks passed.")

    return {"type": "text", "value": "\n".join(lines)}


def get_command_definition() -> dict[str, Any]:
    return {
        "type": "local",
        "name": COMMAND_NAME,
        "description": DESCRIPTION,
        "call": call,
    }
