"""
Git diff computation.

Port of: src/utils/gitDiff.ts

Fetches and parses git diff stats and hunks comparing working tree to HEAD.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Optional

GIT_TIMEOUT_MS = 5000
MAX_FILES = 50
MAX_DIFF_SIZE_BYTES = 1_000_000  # 1 MB
MAX_LINES_PER_FILE = 400
MAX_FILES_FOR_DETAILS = 500


@dataclass
class GitDiffStats:
    files_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class PerFileStats:
    added: int = 0
    removed: int = 0
    is_binary: bool = False
    is_untracked: bool = False


@dataclass
class StructuredPatchHunk:
    old_start: int = 0
    old_lines: int = 0
    new_start: int = 0
    new_lines: int = 0
    lines: list[str] = field(default_factory=list)


@dataclass
class GitDiffResult:
    stats: GitDiffStats = field(default_factory=GitDiffStats)
    per_file_stats: dict[str, PerFileStats] = field(default_factory=dict)
    hunks: dict[str, list[StructuredPatchHunk]] = field(default_factory=dict)


@dataclass
class ToolUseDiff:
    filename: str = ""
    status: str = "modified"
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str = ""
    repository: Optional[str] = None


def _git_exe() -> str:
    return os.environ.get("GIT_EXECUTABLE", "git")


async def _exec_git(
    args: list[str],
    cwd: Optional[str] = None,
    timeout: float = GIT_TIMEOUT_MS / 1000,
) -> tuple[str, int]:
    """Execute a git command and return (stdout, returncode)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            _git_exe(),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode("utf-8", errors="replace"), proc.returncode or 0
    except (asyncio.TimeoutError, FileNotFoundError, OSError):
        return "", 1


async def is_in_transient_git_state(cwd: Optional[str] = None) -> bool:
    """Check if we're in a merge/rebase/cherry-pick/revert state."""
    git_dir_stdout, code = await _exec_git(
        ["--no-optional-locks", "rev-parse", "--git-dir"],
        cwd=cwd,
    )
    if code != 0:
        return False

    git_dir = git_dir_stdout.strip()
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(cwd or os.getcwd(), git_dir)

    for marker in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
        if os.path.exists(os.path.join(git_dir, marker)):
            return True
    return False


async def fetch_git_diff(cwd: Optional[str] = None) -> Optional[GitDiffResult]:
    """
    Fetch git diff stats and hunks comparing working tree to HEAD.
    Returns None if not in a git repo or during transient git states.
    """
    effective_cwd = cwd or os.getcwd()

    # Check if git repo
    _, code = await _exec_git(
        ["--no-optional-locks", "rev-parse", "--is-inside-work-tree"],
        cwd=effective_cwd,
    )
    if code != 0:
        return None

    if await is_in_transient_git_state(effective_cwd):
        return None

    # Quick probe with --shortstat
    shortstat_out, shortstat_code = await _exec_git(
        ["--no-optional-locks", "diff", "HEAD", "--shortstat"],
        cwd=effective_cwd,
    )
    if shortstat_code == 0:
        quick_stats = parse_shortstat(shortstat_out)
        if quick_stats and quick_stats.files_count > MAX_FILES_FOR_DETAILS:
            return GitDiffResult(stats=quick_stats)

    # Full numstat
    numstat_out, numstat_code = await _exec_git(
        ["--no-optional-locks", "diff", "HEAD", "--numstat"],
        cwd=effective_cwd,
    )
    if numstat_code != 0:
        return None

    stats, per_file = parse_git_numstat(numstat_out)

    # Untracked files
    remaining = MAX_FILES - len(per_file)
    if remaining > 0:
        untracked = await _fetch_untracked_files(effective_cwd, remaining)
        if untracked:
            stats.files_count += len(untracked)
            per_file.update(untracked)

    return GitDiffResult(stats=stats, per_file_stats=per_file)


async def _fetch_untracked_files(
    cwd: str, max_files: int
) -> dict[str, PerFileStats]:
    """Fetch untracked file names."""
    stdout, code = await _exec_git(
        ["--no-optional-locks", "ls-files", "--others", "--exclude-standard"],
        cwd=cwd,
    )
    if code != 0 or not stdout.strip():
        return {}

    result = {}
    for path in stdout.strip().split("\n")[:max_files]:
        if path:
            result[path] = PerFileStats(is_untracked=True)
    return result


def parse_shortstat(stdout: str) -> Optional[GitDiffStats]:
    """Parse git diff --shortstat output."""
    m = re.search(
        r"(\d+)\s+files?\s+changed"
        r"(?:,\s+(\d+)\s+insertions?\(\+\))?"
        r"(?:,\s+(\d+)\s+deletions?\(-\))?",
        stdout,
    )
    if not m:
        return None
    return GitDiffStats(
        files_count=int(m.group(1) or 0),
        lines_added=int(m.group(2) or 0),
        lines_removed=int(m.group(3) or 0),
    )


def parse_git_numstat(stdout: str) -> tuple[GitDiffStats, dict[str, PerFileStats]]:
    """Parse git diff --numstat output."""
    lines = [l for l in stdout.strip().split("\n") if l]
    added = 0
    removed = 0
    count = 0
    per_file: dict[str, PerFileStats] = {}

    for line in lines:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        count += 1
        add_str, rem_str = parts[0], parts[1]
        file_path = "\t".join(parts[2:])
        is_binary = add_str == "-" or rem_str == "-"
        file_added = 0 if is_binary else int(add_str or 0)
        file_removed = 0 if is_binary else int(rem_str or 0)
        added += file_added
        removed += file_removed
        if len(per_file) < MAX_FILES:
            per_file[file_path] = PerFileStats(
                added=file_added, removed=file_removed, is_binary=is_binary
            )

    return GitDiffStats(files_count=count, lines_added=added, lines_removed=removed), per_file


def parse_git_diff(stdout: str) -> dict[str, list[StructuredPatchHunk]]:
    """Parse unified diff output into per-file hunks."""
    result: dict[str, list[StructuredPatchHunk]] = {}
    if not stdout.strip():
        return result

    file_diffs = re.split(r"^diff --git ", stdout, flags=re.MULTILINE)

    for file_diff in file_diffs:
        if not file_diff:
            continue
        if len(result) >= MAX_FILES:
            break
        if len(file_diff) > MAX_DIFF_SIZE_BYTES:
            continue

        lines = file_diff.split("\n")
        header_match = re.match(r"^a/(.+?) b/(.+)$", lines[0]) if lines else None
        if not header_match:
            continue
        file_path = header_match.group(2) or header_match.group(1)

        file_hunks: list[StructuredPatchHunk] = []
        current_hunk: Optional[StructuredPatchHunk] = None
        line_count = 0

        for i in range(1, len(lines)):
            line = lines[i]
            hunk_match = re.match(
                r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line
            )
            if hunk_match:
                if current_hunk:
                    file_hunks.append(current_hunk)
                current_hunk = StructuredPatchHunk(
                    old_start=int(hunk_match.group(1) or 0),
                    old_lines=int(hunk_match.group(2) or 1),
                    new_start=int(hunk_match.group(3) or 0),
                    new_lines=int(hunk_match.group(4) or 1),
                )
                continue

            if line.startswith(("index ", "---", "+++", "new file", "deleted file",
                               "old mode", "new mode", "Binary files")):
                continue

            if current_hunk and (
                line.startswith(("+", "-", " ")) or line == ""
            ):
                if line_count >= MAX_LINES_PER_FILE:
                    continue
                current_hunk.lines.append(line)
                line_count += 1

        if current_hunk:
            file_hunks.append(current_hunk)
        if file_hunks:
            result[file_path] = file_hunks

    return result
