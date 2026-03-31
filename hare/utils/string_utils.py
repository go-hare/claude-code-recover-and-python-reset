"""
String utilities.

Port of: src/utils/stringUtils.ts
"""

from __future__ import annotations


def capitalize(s: str) -> str:
    """Capitalize the first letter of a string."""
    if not s:
        return s
    return s[0].upper() + s[1:]


def truncate(s: str, max_len: int, suffix: str = "...") -> str:
    """Truncate a string to a max length with suffix."""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Pluralize a word based on count."""
    if count == 1:
        return singular
    return plural if plural else singular + "s"
