"""
Context providers for system prompt and user context.

Port of: src/context.ts

This context is prepended to each conversation and cached for
the duration of the conversation.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from datetime import date
from functools import lru_cache
from typing import Optional

MAX_STATUS_CHARS = 2000

# System prompt injection for cache breaking (ant-only, ephemeral debugging state)
_system_prompt_injection: Optional[str] = None


def get_system_prompt_injection() -> Optional[str]:
    return _system_prompt_injection


def set_system_prompt_injection(value: Optional[str]) -> None:
    global _system_prompt_injection
    _system_prompt_injection = value
    # Clear context caches immediately when injection changes
    get_user_context.cache_clear()
    get_system_context.cache_clear()


async def _exec_no_throw(cmd: list[str]) -> str:
    """Run a subprocess and return stdout, swallowing errors."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


async def get_git_status() -> Optional[str]:
    """
    Gather git info (branch, status, recent commits) for the system context.
    Returns None if not in a git repo or if running in tests.
    """
    if os.environ.get("NODE_ENV") == "test":
        return None

    # Check if in a git repo
    is_git = await _exec_no_throw(["git", "rev-parse", "--is-inside-work-tree"])
    if is_git != "true":
        return None

    try:
        branch_task = _exec_no_throw(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        # Heuristic for default branch
        main_branch_task = _exec_no_throw(
            ["git", "rev-parse", "--verify", "--quiet", "refs/heads/main"]
        )
        status_task = _exec_no_throw(
            ["git", "--no-optional-locks", "status", "--short"]
        )
        log_task = _exec_no_throw(
            ["git", "--no-optional-locks", "log", "--oneline", "-n", "5"]
        )
        user_name_task = _exec_no_throw(["git", "config", "user.name"])

        branch, main_check, status, log, user_name = await asyncio.gather(
            branch_task, main_branch_task, status_task, log_task, user_name_task
        )

        main_branch = "main" if main_check else "master"

        # Truncate long status
        if len(status) > MAX_STATUS_CHARS:
            status = (
                status[:MAX_STATUS_CHARS]
                + "\n... (truncated because it exceeds 2k characters. "
                "If you need more information, run 'git status' using BashTool)"
            )

        parts = [
            "This is the git status at the start of the conversation. "
            "Note that this status is a snapshot in time, and will not update during the conversation.",
            f"Current branch: {branch}",
            f"Main branch (you will usually use this for PRs): {main_branch}",
        ]
        if user_name:
            parts.append(f"Git user: {user_name}")
        parts.append(f"Status:\n{status or '(clean)'}")
        parts.append(f"Recent commits:\n{log}")

        return "\n\n".join(parts)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _get_local_iso_date() -> str:
    return date.today().isoformat()


@lru_cache(maxsize=1)
def get_system_context_sync() -> dict[str, str]:
    """Synchronous fallback for system context."""
    return {}


async def _get_system_context_async() -> dict[str, str]:
    is_remote = os.environ.get("CLAUDE_CODE_REMOTE") == "true"
    git_status = None if is_remote else await get_git_status()

    result: dict[str, str] = {}
    if git_status:
        result["gitStatus"] = git_status
    return result


@lru_cache(maxsize=1)
def get_system_context() -> dict[str, str]:
    """
    This context is prepended to each conversation, cached for the conversation duration.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return get_system_context_sync()
        return loop.run_until_complete(_get_system_context_async())
    except RuntimeError:
        return get_system_context_sync()


@lru_cache(maxsize=1)
def get_user_context() -> dict[str, str]:
    """
    User context prepended to each conversation, cached for the conversation duration.

    In the TS source, this loads CLAUDE.md files (claudeMd). For now we provide
    the date and leave memory file loading for future implementation.
    """
    return {
        "currentDate": f"Today's date is {_get_local_iso_date()}.",
    }
