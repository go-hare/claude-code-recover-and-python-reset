"""
GitHub CLI auth status check.

Port of: src/utils/github/ghAuthStatus.ts
"""

from __future__ import annotations

import asyncio
import shutil
from typing import Any


async def check_gh_auth_status() -> dict[str, Any]:
    """Check GitHub CLI authentication status."""
    gh = shutil.which("gh")
    if not gh:
        return {"authenticated": False, "error": "gh CLI not found"}

    try:
        proc = await asyncio.create_subprocess_exec(
            gh, "auth", "status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = (stdout or stderr).decode("utf-8", errors="replace")
        success = proc.returncode == 0
        return {
            "authenticated": success,
            "output": output.strip(),
        }
    except Exception as e:
        return {"authenticated": False, "error": str(e)}


async def is_gh_authenticated() -> bool:
    """Check if gh CLI is authenticated."""
    result = await check_gh_auth_status()
    return result.get("authenticated", False)
