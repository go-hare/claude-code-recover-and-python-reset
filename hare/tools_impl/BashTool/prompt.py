"""
Bash tool prompt generation.

Port of: src/tools/BashTool/prompt.ts
"""

from __future__ import annotations

import sys
from typing import Optional

BASH_TOOL_NAME = "Bash"
DEFAULT_TIMEOUT_MS = 120_000
MAX_TIMEOUT_MS = 600_000

SIMPLE_PROMPT = """Runs a bash command in a shell session with optional timeout.

Important guidelines:
- Use this tool for system commands, file operations, and running scripts
- Commands run in a persistent shell session (environment variables persist)
- Working directory is tracked and persists between calls
- For long-running commands, consider using timeout
- Avoid interactive commands that require user input
- Use proper quoting for arguments with spaces
- Prefer built-in tools (FileRead, FileEdit, Glob, Grep) for file operations when available"""

SANDBOX_SECTION = """
Sandbox mode:
- When sandbox is enabled, commands run in an isolated environment
- Network access may be restricted
- File system writes are limited to the working directory"""

COMMIT_INSTRUCTIONS = """
Git commit and PR instructions:
- Always use descriptive commit messages
- Follow conventional commit format when possible
- Never force push to main/master branches
- Use 'git status' and 'git diff' to review changes before committing
- Create feature branches for significant changes"""


def get_bash_prompt(
    *,
    sandbox_enabled: bool = False,
    include_commit_instructions: bool = True,
    platform: Optional[str] = None,
) -> str:
    """Build the full bash tool prompt."""
    parts = [SIMPLE_PROMPT]

    if sandbox_enabled:
        parts.append(SANDBOX_SECTION)

    if include_commit_instructions:
        parts.append(COMMIT_INSTRUCTIONS)

    p = platform or sys.platform
    if p == "win32":
        parts.append("\nNote: Running on Windows. Use PowerShell-compatible commands or specify bash explicitly.")
    elif p == "darwin":
        parts.append("\nNote: Running on macOS. BSD variants of commands may differ from GNU/Linux.")

    return "\n".join(parts)


def get_default_timeout_ms() -> int:
    return DEFAULT_TIMEOUT_MS


def get_max_timeout_ms() -> int:
    return MAX_TIMEOUT_MS
