from __future__ import annotations

import asyncio
from collections.abc import Mapping
import os
import re
from typing import Any

from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import QueryResult, ToolRunResult
from claude_code_py.tools.base import Tool

DEFAULT_TIMEOUT_MS = 120_000
MAX_TIMEOUT_MS = 600_000
SILENT_COMMANDS = {
    "mv",
    "cp",
    "rm",
    "mkdir",
    "rmdir",
    "chmod",
    "chown",
    "chgrp",
    "touch",
    "ln",
    "cd",
    "export",
    "unset",
    "wait",
}
SEMANTIC_NEUTRAL_COMMANDS = {"echo", "printf", "true", "false", ":"}
SLEEP_PATTERN = re.compile(r"^\s*sleep\s+(\d+)\s*(?:$|(?:&&|;)\s*(.+))", re.DOTALL)


class BashTool(Tool):
    name = "Bash"
    description = "Run shell command"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": f"Optional timeout in milliseconds (max {MAX_TIMEOUT_MS}).",
            },
            "description": {
                "type": "string",
                "description": "Clear, concise description of what this command does in active voice.",
            },
            "run_in_background": {
                "type": "boolean",
                "description": "Set to true to run this command in the background. Use Read to read the output later.",
            },
            "dangerouslyDisableSandbox": {
                "type": "boolean",
                "description": "Set this to true to dangerously override sandbox mode and run commands without sandboxing.",
            },
        },
        "required": ["command"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        command = str(tool_input["command"])
        timeout_ms = _coerce_timeout_ms(tool_input.get("timeout"))
        description = str(tool_input.get("description") or command).strip() or command
        run_in_background = bool(tool_input.get("run_in_background", False))

        sleep_pattern = _detect_blocked_sleep_pattern(command)
        if sleep_pattern is not None and not run_in_background:
            return ToolRunResult(
                content=(
                    f"Blocked: {sleep_pattern}. Run blocking commands in the background with run_in_background: true "
                    "and you'll get a completion notification when done. If you genuinely need a delay "
                    "(rate limiting, deliberate pacing), keep it under 2 seconds."
                ),
                is_error=True,
            )

        if run_in_background:
            handle = context.task_manager.start(
                description=description,
                runner=lambda: _run_background_command(
                    command=command,
                    cwd=context.cwd,
                    timeout_ms=timeout_ms,
                    max_output_chars=context.max_output_chars,
                ),
            )
            return ToolRunResult(
                content=f"Command running in background with ID: {handle.task_id}."
            )

        return await _run_foreground_command(
            command=command,
            cwd=context.cwd,
            timeout_ms=timeout_ms,
            max_output_chars=context.max_output_chars,
        )


def _coerce_timeout_ms(raw: object) -> int | None:
    if raw is None:
        return _get_default_timeout_ms()
    return max(1, min(int(raw), _get_max_timeout_ms()))


async def _run_background_command(
    *,
    command: str,
    cwd,
    timeout_ms: int | None,
    max_output_chars: int,
) -> QueryResult:
    result = await _run_foreground_command(
        command=command,
        cwd=cwd,
        timeout_ms=timeout_ms,
        max_output_chars=max_output_chars,
    )
    return QueryResult(
        output_text=result.content,
        messages=[],
        turns=0,
    )


async def _run_foreground_command(
    *,
    command: str,
    cwd,
    timeout_ms: int | None,
    max_output_chars: int,
) -> ToolRunResult:
    timeout_seconds = None if timeout_ms is None else timeout_ms / 1000
    process = await asyncio.create_subprocess_shell(
        command,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        return ToolRunResult(
            content=f"Command timed out after {timeout_ms}ms",
            is_error=True,
        )

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")
    combined = stdout_text
    if stderr_text:
        combined = f"{combined}\n[stderr]\n{stderr_text}".strip()
    trimmed = combined[:max_output_chars].strip()
    if not trimmed:
        trimmed = "Done" if _is_silent_bash_command(command) else "(no output)"
    if process.returncode == 0:
        return ToolRunResult(content=trimmed)
    return ToolRunResult(
        content=f"Exit code {process.returncode}\n{trimmed}",
        is_error=True,
    )


def _get_default_timeout_ms() -> int:
    value = os.getenv("BASH_DEFAULT_TIMEOUT_MS")
    if value:
        try:
            parsed = int(value)
        except ValueError:
            parsed = 0
        if parsed > 0:
            return parsed
    return DEFAULT_TIMEOUT_MS


def _get_max_timeout_ms() -> int:
    value = os.getenv("BASH_MAX_TIMEOUT_MS")
    if value:
        try:
            parsed = int(value)
        except ValueError:
            parsed = 0
        if parsed > 0:
            return max(parsed, _get_default_timeout_ms())
    return max(MAX_TIMEOUT_MS, _get_default_timeout_ms())


def _detect_blocked_sleep_pattern(command: str) -> str | None:
    match = SLEEP_PATTERN.match(command)
    if match is None:
        return None
    seconds = int(match.group(1))
    if seconds < 2:
        return None
    rest = (match.group(2) or "").strip()
    if rest:
        return f"sleep {seconds} followed by: {rest}"
    return f"standalone sleep {seconds}"


def _is_silent_bash_command(command: str) -> bool:
    parts = re.split(r"(\|\||&&|\||;|>|>>|>&)", command)
    if not parts:
        return False

    has_non_fallback_command = False
    last_operator: str | None = None
    skip_next_as_redirect_target = False
    for part in parts:
        token = part.strip()
        if not token:
            continue
        if skip_next_as_redirect_target:
            skip_next_as_redirect_target = False
            continue
        if token in {">", ">>", ">&"}:
            skip_next_as_redirect_target = True
            continue
        if token in {"||", "&&", "|", ";"}:
            last_operator = token
            continue

        base_command = token.split()[0]
        if last_operator == "||" and base_command in SEMANTIC_NEUTRAL_COMMANDS:
            continue
        has_non_fallback_command = True
        if base_command not in SILENT_COMMANDS:
            return False
        last_operator = None
    return has_non_fallback_command
