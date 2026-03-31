"""
Environment variable utilities.

Port of: src/utils/envUtils.ts
"""

from __future__ import annotations

import os


def is_env_truthy(value: str | None) -> bool:
    """Check if an environment variable value is truthy."""
    if value is None:
        return False
    return value.lower() in ("1", "true", "yes")


def is_bare_mode() -> bool:
    """Check if running in bare/simple mode."""
    return is_env_truthy(os.environ.get("CLAUDE_CODE_SIMPLE"))
