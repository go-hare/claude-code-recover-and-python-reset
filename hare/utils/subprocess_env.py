"""
Subprocess environment management.

Port of: src/utils/subprocessEnv.ts

Builds the environment dict for child processes.
"""

from __future__ import annotations

import os
from typing import Optional

from hare.bootstrap.state import get_original_cwd


def subprocess_env(
    extra: Optional[dict[str, str]] = None,
    cwd: Optional[str] = None,
) -> dict[str, str]:
    """
    Build environment dict for subprocess execution.
    Includes current environment plus any extras.
    """
    env = dict(os.environ)

    # Set HOME if not present (Windows)
    if "HOME" not in env:
        env["HOME"] = os.path.expanduser("~")

    # Set PWD to the effective working directory
    effective_cwd = cwd or get_original_cwd()
    env["PWD"] = effective_cwd

    # Remove potentially harmful env vars
    for key in ("NODE_OPTIONS", "NODE_REPL_HISTORY"):
        env.pop(key, None)

    if extra:
        env.update(extra)

    return env
