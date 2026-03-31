"""
Git utilities.

Port of: src/utils/git.ts

Provides git repository detection, status, and operation helpers.
"""

from __future__ import annotations

import asyncio
import os
import re
from functools import lru_cache
from typing import Any, Optional


async def find_git_root(cwd: Optional[str] = None) -> Optional[str]:
    """Find the root of the git repository containing cwd."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode("utf-8").strip()
    except (FileNotFoundError, OSError):
        pass
    return None


async def is_git_repo(cwd: Optional[str] = None) -> bool:
    """Check if the current directory is inside a git repository."""
    root = await find_git_root(cwd)
    return root is not None


async def get_git_status(cwd: Optional[str] = None) -> str:
    """Get git status --short output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--short",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode("utf-8").strip()
    except (FileNotFoundError, OSError):
        pass
    return ""


async def get_current_branch(cwd: Optional[str] = None) -> Optional[str]:
    """Get the current git branch name."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--abbrev-ref", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode("utf-8").strip()
    except (FileNotFoundError, OSError):
        pass
    return None


async def get_git_log(
    cwd: Optional[str] = None,
    *,
    max_count: int = 10,
    format_str: str = "%h %s",
) -> list[str]:
    """Get recent git log entries."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "log", f"--max-count={max_count}", f"--format={format_str}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return [l for l in stdout.decode("utf-8").strip().split("\n") if l]
    except (FileNotFoundError, OSError):
        pass
    return []


async def get_staged_files(cwd: Optional[str] = None) -> list[str]:
    """Get list of staged files."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--cached", "--name-only",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return [f for f in stdout.decode("utf-8").strip().split("\n") if f]
    except (FileNotFoundError, OSError):
        pass
    return []


async def get_modified_files(cwd: Optional[str] = None) -> list[str]:
    """Get list of modified (unstaged) files."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return [f for f in stdout.decode("utf-8").strip().split("\n") if f]
    except (FileNotFoundError, OSError):
        pass
    return []


async def get_untracked_files(cwd: Optional[str] = None) -> list[str]:
    """Get list of untracked files."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "ls-files", "--others", "--exclude-standard",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or os.getcwd(),
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return [f for f in stdout.decode("utf-8").strip().split("\n") if f]
    except (FileNotFoundError, OSError):
        pass
    return []


def normalize_git_remote_url(url: str) -> str:
    """Normalize a git remote URL to a comparable format."""
    url = url.strip()
    url = re.sub(r'\.git$', '', url)
    # SSH to HTTPS normalization
    match = re.match(r'git@([^:]+):(.+)', url)
    if match:
        host, path = match.groups()
        url = f"https://{host}/{path}"
    url = re.sub(r'^https?://', '', url)
    url = url.lower()
    return url


async def is_in_transient_git_state(cwd: Optional[str] = None) -> bool:
    """Check if we're in a transient git state (merge, rebase, cherry-pick)."""
    root = await find_git_root(cwd)
    if not root:
        return False
    git_dir = os.path.join(root, ".git")
    transient_markers = [
        os.path.join(git_dir, "MERGE_HEAD"),
        os.path.join(git_dir, "rebase-merge"),
        os.path.join(git_dir, "rebase-apply"),
        os.path.join(git_dir, "CHERRY_PICK_HEAD"),
        os.path.join(git_dir, "BISECT_LOG"),
    ]
    return any(os.path.exists(m) for m in transient_markers)
