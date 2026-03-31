"""
Formatting utilities.

Port of: src/utils/format.ts

Text formatting, truncation, number formatting utilities.
"""

from __future__ import annotations

import re
from typing import Optional


def truncate_text(text: str, max_length: int, *, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def truncate_lines(text: str, max_lines: int, *, suffix: str = "\n... (truncated)") -> str:
    """Truncate text to max_lines."""
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + suffix


def format_number(n: int | float) -> str:
    """Format a number with comma separators."""
    if isinstance(n, float):
        return f"{n:,.2f}"
    return f"{n:,}"


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"


def format_duration(ms: float) -> str:
    """Format duration in milliseconds to human-readable string."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def format_tokens(count: int) -> str:
    """Format token count to human-readable string."""
    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    return f"{count / 1_000_000:.2f}M"


def format_cost(cost: float) -> str:
    """Format cost in dollars."""
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"


def indent_text(text: str, spaces: int = 2) -> str:
    """Indent each line of text."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split("\n"))


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def wrap_text(text: str, width: int = 80) -> str:
    """Wrap text to specified width."""
    import textwrap
    return textwrap.fill(text, width=width)


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Pluralize a word based on count."""
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"


def relative_path(path: str, base: str) -> str:
    """Get relative path from base."""
    import os
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return path


def is_output_line_truncated(output: str) -> bool:
    """Check if output appears to have been truncated."""
    return output.endswith("...") or output.endswith("[truncated]")
