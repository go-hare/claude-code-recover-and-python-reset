"""
Command semantics for interpreting exit codes.

Port of: src/tools/BashTool/commandSemantics.ts

Many commands use exit codes to convey information other than success/failure.
For example, grep returns 1 when no matches are found, which is not an error.
"""

from __future__ import annotations

from typing import Optional

from hare.utils.bash.commands import split_command

COMMAND_SEMANTICS: dict[str, tuple[int, Optional[str]]] = {
    "grep": (2, "No matches found"),
    "rg": (2, "No matches found"),
    "find": (2, "Some directories were inaccessible"),
    "diff": (2, "Files differ"),
    "test": (2, "Condition is false"),
    "[": (2, "Condition is false"),
}


def interpret_command_result(
    command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> dict[str, object]:
    """Interpret command result based on semantic rules."""
    base_command = _heuristically_extract_base_command(command)

    if base_command in COMMAND_SEMANTICS:
        error_threshold, info_message = COMMAND_SEMANTICS[base_command]
        is_error = exit_code >= error_threshold
        message = info_message if exit_code == 1 else None
        return {"is_error": is_error, "message": message}

    return {
        "is_error": exit_code != 0,
        "message": f"Command failed with exit code {exit_code}" if exit_code != 0 else None,
    }


def _heuristically_extract_base_command(command: str) -> str:
    """Extract the last command name from a potentially piped/chained command."""
    try:
        segments = split_command(command)
        last = segments[-1] if segments else command
    except Exception:
        last = command
    return last.strip().split()[0] if last.strip() else ""
