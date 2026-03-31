"""
Sandbox decision logic.

Port of: src/tools/BashTool/shouldUseSandbox.ts
"""

from __future__ import annotations

from typing import Any

from hare.tools_impl.BashTool.bash_permissions import (
    bash_permission_rule,
    match_wildcard_pattern,
    strip_all_leading_env_vars,
    strip_safe_wrappers,
    BINARY_HIJACK_VARS,
)
from hare.utils.bash.commands import split_command


def should_use_sandbox(
    command: str | None = None,
    *,
    sandbox_enabled: bool = False,
    dangerously_disable_sandbox: bool = False,
    excluded_commands: list[str] | None = None,
) -> bool:
    """Determine whether a command should run in a sandbox."""
    if not sandbox_enabled:
        return False

    if dangerously_disable_sandbox:
        return False

    if not command:
        return False

    if excluded_commands and _contains_excluded_command(command, excluded_commands):
        return False

    return True


def _contains_excluded_command(command: str, excluded_commands: list[str]) -> bool:
    """Check if any subcommand matches an excluded pattern."""
    try:
        subcommands = split_command(command)
    except Exception:
        subcommands = [command]

    for subcmd in subcommands:
        trimmed = subcmd.strip()
        candidates = _generate_fixed_point_candidates(trimmed)

        for pattern in excluded_commands:
            rule = bash_permission_rule(pattern)
            for cand in candidates:
                if rule.type == "prefix":
                    if cand == rule.prefix or cand.startswith(rule.prefix + " "):
                        return True
                elif rule.type == "exact":
                    if cand == rule.command:
                        return True
                elif rule.type == "wildcard":
                    if match_wildcard_pattern(rule.pattern, cand):
                        return True
    return False


def _generate_fixed_point_candidates(command: str) -> list[str]:
    """Generate all stripped variants of a command."""
    candidates = [command]
    seen = {command}
    start = 0
    while start < len(candidates):
        end = len(candidates)
        for i in range(start, end):
            cmd = candidates[i]
            env_stripped = strip_all_leading_env_vars(cmd, BINARY_HIJACK_VARS)
            if env_stripped not in seen:
                candidates.append(env_stripped)
                seen.add(env_stripped)
            wrapper_stripped = strip_safe_wrappers(cmd)
            if wrapper_stripped not in seen:
                candidates.append(wrapper_stripped)
                seen.add(wrapper_stripped)
        start = end
    return candidates
