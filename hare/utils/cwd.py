"""
Current working directory management.

Port of: src/utils/cwd.ts
"""

from __future__ import annotations

import os
from typing import Optional

from hare.bootstrap.state import get_cwd as _state_get_cwd, set_cwd as _state_set_cwd


def get_cwd() -> str:
    """Get the current working directory."""
    return _state_get_cwd()


def set_cwd(new_cwd: str) -> None:
    """Set the current working directory."""
    _state_set_cwd(new_cwd)


def pwd() -> str:
    """Get the actual filesystem CWD."""
    return os.getcwd()
