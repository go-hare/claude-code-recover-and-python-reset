"""
File reading with metadata.

Port of: src/utils/fileRead.ts

Provides readFileSync with encoding detection and line ending detection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

from hare.utils.debug import log_for_debugging

LineEndingType = Literal["CRLF", "LF"]


def detect_encoding_for_file(file_path: str) -> str:
    """
    Detect encoding for a file by examining the first bytes.
    Returns Python encoding string.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(4096)
    except OSError:
        return "utf-8"

    if not header:
        return "utf-8"

    # Check BOM markers
    if len(header) >= 2 and header[0] == 0xFF and header[1] == 0xFE:
        return "utf-16-le"
    if len(header) >= 3 and header[0] == 0xEF and header[1] == 0xBB and header[2] == 0xBF:
        return "utf-8-sig"

    return "utf-8"


def detect_line_endings(content: str) -> LineEndingType:
    """Detect the predominant line ending style in content."""
    crlf_count = 0
    lf_count = 0

    i = 0
    while i < len(content):
        if content[i] == "\n":
            if i > 0 and content[i - 1] == "\r":
                crlf_count += 1
            else:
                lf_count += 1
        i += 1

    return "CRLF" if crlf_count > lf_count else "LF"


@dataclass
class FileReadResult:
    """Result of reading a file with metadata."""
    content: str
    encoding: str
    line_endings: LineEndingType


def read_file_sync_with_metadata(file_path: str) -> FileReadResult:
    """
    Read a file synchronously with encoding and line ending detection.
    Normalizes CRLF to LF in the returned content.
    """
    resolved = os.path.realpath(file_path)

    if resolved != os.path.normpath(file_path):
        log_for_debugging(f"Reading through symlink: {file_path} -> {resolved}")

    encoding = detect_encoding_for_file(resolved)
    with open(resolved, "r", encoding=encoding, errors="replace") as f:
        raw = f.read()

    line_endings = detect_line_endings(raw[:4096])

    # Normalize CRLF -> LF
    content = raw.replace("\r\n", "\n")

    return FileReadResult(
        content=content,
        encoding=encoding,
        line_endings=line_endings,
    )


def read_file_sync(file_path: str) -> str:
    """Read a file synchronously, normalizing line endings."""
    return read_file_sync_with_metadata(file_path).content
