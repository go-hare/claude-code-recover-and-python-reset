"""
Platform detection.

Port of: src/utils/platform.ts
"""

from __future__ import annotations

import os
import sys
from typing import Literal

Platform = Literal["macos", "linux", "windows", "wsl"]


def get_platform() -> Platform:
    """Detect the current platform."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    # Check for WSL
    if "microsoft" in os.uname().release.lower() if hasattr(os, "uname") else False:
        return "wsl"
    return "linux"


def is_macos() -> bool:
    return get_platform() == "macos"


def is_linux() -> bool:
    return get_platform() == "linux"


def is_windows() -> bool:
    return get_platform() == "windows"


def is_wsl() -> bool:
    return get_platform() == "wsl"
