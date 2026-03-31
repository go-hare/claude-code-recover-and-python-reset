"""
PowerShell detection.

Port of: src/utils/shell/powershellDetection.ts
"""

from __future__ import annotations

import os
import shutil
import sys


def is_powershell_available() -> bool:
    """Check if PowerShell is available on the system."""
    if sys.platform == "win32":
        return True
    return shutil.which("pwsh") is not None or shutil.which("powershell") is not None


def get_powershell_path() -> str:
    """Get the path to the PowerShell executable."""
    if sys.platform == "win32":
        ps_path = shutil.which("pwsh") or shutil.which("powershell")
        return ps_path or "powershell"
    return shutil.which("pwsh") or ""
