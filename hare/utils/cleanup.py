"""
Cleanup utilities.

Port of: src/utils/cleanup.ts

Handles cleanup of old session files, logs, caches, etc.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from hare.utils.debug import log_for_debugging
from hare.utils.log import log_error_msg

DEFAULT_CLEANUP_PERIOD_DAYS = 30


@dataclass
class CleanupResult:
    messages: int = 0
    errors: int = 0


def add_cleanup_results(a: CleanupResult, b: CleanupResult) -> CleanupResult:
    return CleanupResult(
        messages=a.messages + b.messages,
        errors=a.errors + b.errors,
    )


def _get_cutoff_date(cleanup_period_days: int = DEFAULT_CLEANUP_PERIOD_DAYS) -> float:
    """Get cutoff timestamp for cleanup."""
    return time.time() - (cleanup_period_days * 24 * 60 * 60)


async def cleanup_old_files_in_directory(
    dir_path: str,
    cutoff_timestamp: float,
) -> CleanupResult:
    """Remove files older than cutoff in a directory."""
    result = CleanupResult()

    if not os.path.isdir(dir_path):
        return result

    try:
        for entry in os.listdir(dir_path):
            entry_path = os.path.join(dir_path, entry)
            try:
                if os.path.isfile(entry_path):
                    mtime = os.path.getmtime(entry_path)
                    if mtime < cutoff_timestamp:
                        os.unlink(entry_path)
                        result.messages += 1
            except OSError:
                result.errors += 1
    except OSError:
        pass

    return result


async def cleanup_old_session_files(
    projects_dir: str,
    cleanup_period_days: int = DEFAULT_CLEANUP_PERIOD_DAYS,
) -> CleanupResult:
    """Clean up old session files."""
    cutoff = _get_cutoff_date(cleanup_period_days)
    result = CleanupResult()

    if not os.path.isdir(projects_dir):
        return result

    try:
        for project in os.listdir(projects_dir):
            project_dir = os.path.join(projects_dir, project)
            if not os.path.isdir(project_dir):
                continue

            for entry in os.listdir(project_dir):
                entry_path = os.path.join(project_dir, entry)
                try:
                    if os.path.isfile(entry_path):
                        if entry.endswith((".jsonl", ".cast")):
                            mtime = os.path.getmtime(entry_path)
                            if mtime < cutoff:
                                os.unlink(entry_path)
                                result.messages += 1
                except OSError:
                    result.errors += 1

            # Try to remove empty project dirs
            try:
                os.rmdir(project_dir)
            except OSError:
                pass
    except OSError:
        pass

    return result


async def cleanup_old_message_files_in_background() -> None:
    """Run all cleanup tasks."""
    from hare.utils.config_full import GLOBAL_CONFIG_DIR

    cutoff = _get_cutoff_date()

    # Clean errors
    errors_dir = os.path.join(GLOBAL_CONFIG_DIR, "errors")
    await cleanup_old_files_in_directory(errors_dir, cutoff)

    # Clean sessions
    projects_dir = os.path.join(GLOBAL_CONFIG_DIR, "projects")
    await cleanup_old_session_files(projects_dir)

    # Clean plans
    plans_dir = os.path.join(GLOBAL_CONFIG_DIR, "plans")
    await cleanup_old_files_in_directory(plans_dir, cutoff)

    # Clean debug logs
    debug_dir = os.path.join(GLOBAL_CONFIG_DIR, "debug")
    await cleanup_old_files_in_directory(debug_dir, cutoff)

    log_for_debugging("Background cleanup completed")
