"""
Windows path utilities.

Port of: src/utils/windowsPaths.ts

Handle Windows-specific path normalization, UNC paths, and drive letters.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Optional


def is_unc_path(path: str) -> bool:
    """Check if path is a UNC path (\\\\server\\share)."""
    return path.startswith("\\\\") or path.startswith("//")


def is_windows_absolute_path(path: str) -> bool:
    """Check if path is a Windows absolute path (C:\\...)."""
    if len(path) < 3:
        return False
    return bool(re.match(r'^[A-Za-z]:[/\\]', path))


def normalize_windows_path(path: str) -> str:
    """Normalize a Windows path to use forward slashes."""
    return path.replace("\\", "/")


def to_posix_path(path: str) -> str:
    """Convert Windows path to POSIX-style path."""
    normalized = normalize_windows_path(path)
    # Convert drive letter: C:/... -> /c/...
    match = re.match(r'^([A-Za-z]):(/.*)$', normalized)
    if match:
        drive = match.group(1).lower()
        rest = match.group(2)
        return f"/{drive}{rest}"
    return normalized


def from_posix_path(path: str) -> str:
    """Convert POSIX-style path back to Windows path."""
    match = re.match(r'^/([a-zA-Z])(/.*)$', path)
    if match:
        drive = match.group(1).upper()
        rest = match.group(2)
        return f"{drive}:{rest}".replace("/", "\\")
    return path.replace("/", "\\")


def ensure_trailing_separator(path: str) -> str:
    """Ensure path ends with a separator."""
    sep = "\\" if sys.platform == "win32" else "/"
    if not path.endswith(sep) and not path.endswith("/"):
        return path + sep
    return path


def get_drive_letter(path: str) -> Optional[str]:
    """Extract drive letter from a Windows path."""
    match = re.match(r'^([A-Za-z]):', path)
    if match:
        return match.group(1).upper()
    return None


def paths_on_same_drive(path1: str, path2: str) -> bool:
    """Check if two paths are on the same drive (Windows)."""
    drive1 = get_drive_letter(path1)
    drive2 = get_drive_letter(path2)
    if drive1 is None or drive2 is None:
        return True  # Non-Windows paths assumed compatible
    return drive1 == drive2


def sanitize_path_for_display(path: str) -> str:
    """Sanitize a path for safe display (prevent ANSI injection)."""
    # Remove control characters
    return re.sub(r'[\x00-\x1f\x7f]', '', path)


def is_suspicious_windows_path(path: str) -> bool:
    """Check if a Windows path has suspicious patterns (NTLM leak risk)."""
    if is_unc_path(path):
        return True
    # Check for path traversal with UNC
    normalized = os.path.normpath(path) if sys.platform == "win32" else path
    if is_unc_path(normalized):
        return True
    return False


def join_windows_path(*parts: str) -> str:
    """Join path components using Windows separators."""
    if sys.platform == "win32":
        return os.path.join(*parts)
    return "\\".join(parts)
