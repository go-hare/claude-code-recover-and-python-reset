"""
Bash security - classify command risk levels.

Port of: src/tools/BashTool/bashSecurity.ts

This module determines risk levels for shell commands, identifying
dangerous patterns like rm -rf, force pushes, etc.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

RiskLevel = Literal["safe", "low", "medium", "high", "critical"]

CRITICAL_PATTERNS = [
    r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+[/~]",
    r"rm\s+-rf\s+/",
    r"mkfs\.",
    r"dd\s+.*of=/dev/",
    r":()\{\s*:\|:\s*&\s*\};:",  # fork bomb
    r"chmod\s+-R\s+777\s+/",
    r">\s*/dev/sd[a-z]",
]

HIGH_RISK_PATTERNS = [
    r"git\s+push\s+.*--force",
    r"git\s+push\s+-f\b",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-[a-zA-Z]*f",
    r"rm\s+-rf\b",
    r"sudo\s+rm\b",
    r"curl\s+.*\|\s*(ba)?sh",
    r"wget\s+.*\|\s*(ba)?sh",
    r"eval\s+.*\$\(",
    r"chmod\s+777\b",
]

MEDIUM_RISK_PATTERNS = [
    r"git\s+checkout\s+--",
    r"git\s+stash\s+drop",
    r"rm\s+-[a-zA-Z]*[rf]",
    r"mv\s+.*\s+/dev/null",
    r"kill\s+-9\b",
    r"pkill\b",
    r"pip\s+install\b",
    r"npm\s+install\s+-g",
    r"apt\s+(install|remove|purge)",
    r"brew\s+(install|uninstall|remove)",
]

LOW_RISK_COMMANDS = frozenset({
    "ls", "cat", "head", "tail", "grep", "rg", "find", "echo",
    "pwd", "whoami", "date", "wc", "sort", "uniq", "diff",
    "file", "which", "type", "git status", "git log", "git diff",
    "git branch", "python --version", "node --version",
})


def classify_command_risk(command: str) -> RiskLevel:
    """Classify the risk level of a shell command."""
    cmd = command.strip()

    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, cmd):
            return "critical"

    for pattern in HIGH_RISK_PATTERNS:
        if re.search(pattern, cmd):
            return "high"

    for pattern in MEDIUM_RISK_PATTERNS:
        if re.search(pattern, cmd):
            return "medium"

    first_word = cmd.split()[0] if cmd.split() else ""
    if first_word in LOW_RISK_COMMANDS or cmd in LOW_RISK_COMMANDS:
        return "safe"

    return "low"


def is_command_safe_for_auto_approve(
    command: str,
    allow_rules: list[str],
    deny_rules: list[str],
) -> bool:
    """Check if a command is safe for automatic approval."""
    from hare.tools_impl.BashTool.bash_permissions import check_bash_permission

    deny_result = check_bash_permission(command, deny_rules, is_allow=False)
    if deny_result["matched"]:
        return False

    allow_result = check_bash_permission(command, allow_rules, is_allow=True)
    if allow_result["matched"]:
        return True

    risk = classify_command_risk(command)
    return risk in ("safe",)
