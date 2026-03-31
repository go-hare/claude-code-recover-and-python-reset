"""
BashTool – execute shell commands.

Port of: src/tools/BashTool/BashTool.tsx

Executes bash/shell commands in the user's working directory.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Any, Optional

from hare.tool import ToolBase, ToolResult, ToolUseContext
from hare.types.permissions import PermissionAllowDecision, PermissionResult

BASH_TOOL_NAME = "Bash"


class _BashTool(ToolBase):
    name = BASH_TOOL_NAME
    aliases = ["bash", "shell"]
    search_hint = "execute terminal shell commands"
    max_result_size_chars = 100_000

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute. Can be a simple command or a complex shell expression.",
                },
                "description": {
                    "type": "string",
                    "description": "A short human-readable description of what the command does (5-10 words).",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Optional timeout in milliseconds. Default: 120000 (2 minutes).",
                },
            },
            "required": ["command"],
        }

    def is_read_only(self, input: dict[str, Any]) -> bool:
        return False

    def is_concurrency_safe(self, input: dict[str, Any]) -> bool:
        return False

    async def check_permissions(
        self, input: dict[str, Any], context: ToolUseContext
    ) -> PermissionResult:
        return PermissionAllowDecision(behavior="allow", updated_input=input)

    async def prompt(self, options: dict[str, Any]) -> str:
        return (
            "Execute a bash command on the user's system. "
            "Use this for file operations, running scripts, installing packages, etc. "
            "Commands run in the user's current working directory."
        )

    async def description(self, input: dict[str, Any], options: dict[str, Any]) -> str:
        return input.get("description", "Execute a bash command")

    def user_facing_name(self, input: Optional[dict[str, Any]] = None) -> str:
        return BASH_TOOL_NAME

    def to_auto_classifier_input(self, input: dict[str, Any]) -> Any:
        return input.get("command", "")

    async def call(
        self,
        args: dict[str, Any],
        context: ToolUseContext,
        can_use_tool: Any = None,
        parent_message: Any = None,
        on_progress: Any = None,
    ) -> ToolResult:
        """Execute a bash command."""
        command = args.get("command", "")
        timeout_ms = args.get("timeout", 120_000)
        timeout_s = timeout_ms / 1000

        from hare.utils.cwd import get_cwd
        cwd = get_cwd()

        try:
            # Choose shell based on platform
            if os.name == "nt":
                shell_cmd = ["powershell", "-Command", command]
            else:
                shell_cmd = ["bash", "-c", command]

            proc = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_s
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    data=f"Command timed out after {timeout_s}s"
                )

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = proc.returncode

            # Build output matching TS format
            parts: list[str] = []
            if stdout:
                parts.append(stdout)
            if stderr:
                parts.append(f"stderr:\n{stderr}")
            if exit_code != 0:
                parts.append(f"Exit code: {exit_code}")

            output = "\n".join(parts) if parts else "(no output)"

            # Truncate if needed
            if len(output) > self.max_result_size_chars:
                output = output[: self.max_result_size_chars] + "\n... (truncated)"

            return ToolResult(data=output)

        except Exception as e:
            return ToolResult(data=f"Error executing command: {e}")


BashTool = _BashTool()
