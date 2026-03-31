"""
Shell permission rule matching utilities.

Port of: src/utils/permissions/shellRuleMatching.ts

Handles:
- Parsing permission rules (exact, prefix, wildcard)
- Matching commands against rules
- Generating permission suggestions
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Union

from hare.types.permissions import PermissionUpdate

ESCAPED_STAR_PLACEHOLDER = "\x00ESCAPED_STAR\x00"
ESCAPED_BACKSLASH_PLACEHOLDER = "\x00ESCAPED_BACKSLASH\x00"


@dataclass
class ExactRule:
    type: Literal["exact"] = "exact"
    command: str = ""


@dataclass
class PrefixRule:
    type: Literal["prefix"] = "prefix"
    prefix: str = ""


@dataclass
class WildcardRule:
    type: Literal["wildcard"] = "wildcard"
    pattern: str = ""


ShellPermissionRule = Union[ExactRule, PrefixRule, WildcardRule]


def permission_rule_extract_prefix(rule: str) -> Optional[str]:
    """Extract prefix from legacy :* syntax (e.g., 'npm:*' -> 'npm')."""
    m = re.match(r"^(.+):\*$", rule)
    return m.group(1) if m else None


def has_wildcards(pattern: str) -> bool:
    """Check if pattern contains unescaped wildcards (not legacy :* syntax)."""
    if pattern.endswith(":*"):
        return False
    i = 0
    while i < len(pattern):
        if pattern[i] == "*":
            backslash_count = 0
            j = i - 1
            while j >= 0 and pattern[j] == "\\":
                backslash_count += 1
                j -= 1
            if backslash_count % 2 == 0:
                return True
        i += 1
    return False


def match_wildcard_pattern(
    pattern: str,
    command: str,
    case_insensitive: bool = False,
) -> bool:
    """
    Match a command against a wildcard pattern.
    Wildcards (*) match any sequence of characters.
    Use \\* to match a literal asterisk.
    """
    trimmed = pattern.strip()

    processed = ""
    i = 0
    while i < len(trimmed):
        ch = trimmed[i]
        if ch == "\\" and i + 1 < len(trimmed):
            nxt = trimmed[i + 1]
            if nxt == "*":
                processed += ESCAPED_STAR_PLACEHOLDER
                i += 2
                continue
            elif nxt == "\\":
                processed += ESCAPED_BACKSLASH_PLACEHOLDER
                i += 2
                continue
        processed += ch
        i += 1

    # Count unescaped stars
    unescaped_star_count = processed.count("*")

    # Escape regex special characters except *
    escaped = re.escape(processed).replace(r"\*", ".*")

    # Restore placeholders
    regex_pattern = escaped
    regex_pattern = regex_pattern.replace(
        re.escape(ESCAPED_STAR_PLACEHOLDER), r"\*"
    )
    regex_pattern = regex_pattern.replace(
        re.escape(ESCAPED_BACKSLASH_PLACEHOLDER), r"\\"
    )

    # Make trailing ' *' optional if only one unescaped wildcard
    if regex_pattern.endswith(" .*") and unescaped_star_count == 1:
        regex_pattern = regex_pattern[:-3] + "( .*)?"

    flags = re.DOTALL
    if case_insensitive:
        flags |= re.IGNORECASE

    return bool(re.match(f"^{regex_pattern}$", command, flags))


def parse_permission_rule(rule: str) -> ShellPermissionRule:
    """Parse a permission rule string into a structured rule."""
    prefix = permission_rule_extract_prefix(rule)
    if prefix is not None:
        return PrefixRule(type="prefix", prefix=prefix)
    if has_wildcards(rule):
        return WildcardRule(type="wildcard", pattern=rule)
    return ExactRule(type="exact", command=rule)


def suggestion_for_exact_command(
    tool_name: str, command: str
) -> list[dict]:
    """Generate permission suggestion for an exact command match."""
    return [{
        "type": "addRules",
        "rules": [{"toolName": tool_name, "ruleContent": command}],
        "behavior": "allow",
        "destination": "localSettings",
    }]


def suggestion_for_prefix(
    tool_name: str, prefix: str
) -> list[dict]:
    """Generate permission suggestion for a prefix match."""
    return [{
        "type": "addRules",
        "rules": [{"toolName": tool_name, "ruleContent": f"{prefix}:*"}],
        "behavior": "allow",
        "destination": "localSettings",
    }]
