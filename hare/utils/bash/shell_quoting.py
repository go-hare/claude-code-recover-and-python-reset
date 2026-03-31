"""
Shell quoting utilities.

Port of: src/utils/bash/shellQuoting.ts, shellQuote.ts
"""

from __future__ import annotations

import re
import shlex


def shell_quote(s: str) -> str:
    """Quote a string for shell use."""
    return shlex.quote(s)


def shell_join(args: list[str]) -> str:
    """Join arguments with proper shell quoting."""
    return " ".join(shell_quote(a) for a in args)


def needs_quoting(s: str) -> bool:
    """Check if a string needs shell quoting."""
    if not s:
        return True
    return bool(re.search(r'[^a-zA-Z0-9_\-./=:@]', s))
