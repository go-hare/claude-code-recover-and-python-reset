"""
Bash permission rule matching and command permission checks.

Port of: src/tools/BashTool/bashPermissions.ts

This module provides the core permission matching logic for shell commands,
including wildcard patterns, prefix rules, env var stripping, and wrapper stripping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Sequence

BINARY_HIJACK_VARS = frozenset({
    "PATH", "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
    "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH", "PYTHONPATH",
    "NODE_PATH", "RUBYLIB", "PERL5LIB", "CLASSPATH",
})

SAFE_WRAPPER_COMMANDS = frozenset({
    "timeout", "nice", "ionice", "nohup", "strace", "ltrace",
    "time", "env", "sudo", "doas",
})


@dataclass
class PrefixRule:
    type: Literal["prefix"] = "prefix"
    prefix: str = ""


@dataclass
class ExactRule:
    type: Literal["exact"] = "exact"
    command: str = ""


@dataclass
class WildcardRule:
    type: Literal["wildcard"] = "wildcard"
    pattern: str = ""


PermissionRule = PrefixRule | ExactRule | WildcardRule


def bash_permission_rule(pattern: str) -> PermissionRule:
    """Parse a permission pattern string into a rule object."""
    pattern = pattern.strip()
    if not pattern:
        return ExactRule(command="")
    if "*" in pattern or "?" in pattern:
        return WildcardRule(pattern=pattern)
    if pattern.endswith(":*"):
        return PrefixRule(prefix=pattern[:-2])
    return ExactRule(command=pattern)


def match_wildcard_pattern(pattern: str, command: str, case_insensitive: bool = False) -> bool:
    """Match a command against a wildcard pattern (* and ? supported)."""
    flags = re.IGNORECASE if case_insensitive else 0
    regex = "^"
    for ch in pattern:
        if ch == "*":
            regex += ".*"
        elif ch == "?":
            regex += "."
        else:
            regex += re.escape(ch)
    regex += "$"
    return bool(re.match(regex, command, flags))


def strip_all_leading_env_vars(command: str, hijack_vars: frozenset[str] = BINARY_HIJACK_VARS) -> str:
    """Strip leading environment variable assignments from a command."""
    result = command.strip()
    while True:
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(\S*)\s+(.+)$', result)
        if not match:
            break
        var_name = match.group(1)
        if var_name not in hijack_vars:
            result = match.group(3)
        else:
            break
    return result


def strip_safe_wrappers(command: str) -> str:
    """Strip known-safe wrapper commands (timeout, nice, etc.) from the front."""
    result = command.strip()
    changed = True
    while changed:
        changed = False
        parts = result.split(None, 1)
        if len(parts) < 2:
            break
        cmd_name = parts[0]
        if cmd_name in SAFE_WRAPPER_COMMANDS:
            rest = parts[1]
            # Skip flags/arguments of the wrapper
            while rest and rest[0] == '-':
                rest_parts = rest.split(None, 1)
                rest = rest_parts[1] if len(rest_parts) > 1 else ""
            if rest:
                result = rest
                changed = True
    return result


def check_bash_permission(
    command: str,
    rules: Sequence[str],
    *,
    is_allow: bool = True,
) -> dict[str, Any]:
    """
    Check if a command matches any of the given permission rules.

    Returns a dict with 'matched' bool and 'rule' if matched.
    """
    candidates = _generate_candidates(command)
    for rule_str in rules:
        rule = bash_permission_rule(rule_str)
        for candidate in candidates:
            if _matches_rule(rule, candidate):
                return {"matched": True, "rule": rule_str, "is_allow": is_allow}
    return {"matched": False}


def _generate_candidates(command: str) -> list[str]:
    """Generate command candidates by stripping env vars and wrappers."""
    trimmed = command.strip()
    candidates = [trimmed]
    seen = {trimmed}
    start = 0
    while start < len(candidates):
        end = len(candidates)
        for i in range(start, end):
            cmd = candidates[i]
            env_stripped = strip_all_leading_env_vars(cmd)
            if env_stripped not in seen:
                candidates.append(env_stripped)
                seen.add(env_stripped)
            wrapper_stripped = strip_safe_wrappers(cmd)
            if wrapper_stripped not in seen:
                candidates.append(wrapper_stripped)
                seen.add(wrapper_stripped)
        start = end
    return candidates


def _matches_rule(rule: PermissionRule, candidate: str) -> bool:
    if isinstance(rule, ExactRule):
        return candidate == rule.command
    if isinstance(rule, PrefixRule):
        return candidate == rule.prefix or candidate.startswith(rule.prefix + " ")
    if isinstance(rule, WildcardRule):
        return match_wildcard_pattern(rule.pattern, candidate)
    return False
