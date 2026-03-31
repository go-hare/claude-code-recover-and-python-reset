"""
Permission checking and enforcement.

Port of: src/utils/permissions/permissions.ts

Handles tool permission decisions: allow, deny, ask the user.
Manages rule matching and permission state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional, Sequence

from hare.types.permissions import (
    PermissionAllowDecision,
    PermissionDenyDecision,
    PermissionMode,
    PermissionResult,
    PermissionRuleValue,
    ToolPermissionContext,
    ToolPermissionRulesBySource,
)

# Alias for clarity in this module
ToolPermissionRule = PermissionRuleValue

# Permission decision types
PermissionDecisionType = Literal["allow", "deny", "ask"]


@dataclass
class PermissionCheckResult:
    """Result of a permission check."""
    decision: PermissionDecisionType
    rule: Optional[ToolPermissionRule] = None
    message: Optional[str] = None


def check_permission(
    tool_name: str,
    input: dict[str, Any],
    context: ToolPermissionContext,
) -> PermissionCheckResult:
    """
    Check if a tool invocation is allowed by the permission rules.

    Mirrors checkPermission() in permissions.ts.
    """
    mode = context.mode

    # bypassPermissions mode allows everything
    if mode == "bypassPermissions":
        return PermissionCheckResult(decision="allow")

    # plan mode denies all non-read-only operations
    if mode == "plan":
        return PermissionCheckResult(
            decision="deny",
            message="Plan mode does not allow tool execution.",
        )

    # Check always_allow rules first
    for source, rules in context.always_allow_rules.items():
        for rule in rules:
            if _rule_matches_tool(rule, tool_name, input):
                return PermissionCheckResult(decision="allow", rule=rule)

    # Check always_deny rules
    for source, rules in context.always_deny_rules.items():
        for rule in rules:
            if _rule_matches_tool(rule, tool_name, input):
                return PermissionCheckResult(
                    decision="deny",
                    rule=rule,
                    message=f"Denied by rule from {source}",
                )

    # Default: ask the user (in interactive mode) or deny (in non-interactive)
    if mode == "dontAsk":
        return PermissionCheckResult(decision="allow")

    return PermissionCheckResult(decision="ask")


def _rule_matches_tool(
    rule: ToolPermissionRule,
    tool_name: str,
    input: dict[str, Any],
) -> bool:
    """Check if a permission rule matches a given tool + input."""
    # Rule must match tool name
    if rule.tool_name.lower() != tool_name.lower():
        return False

    # If no rule_content, it's a blanket rule for this tool
    if not rule.rule_content:
        return True

    # If rule_content is specified, it constrains the match further
    # (e.g., a specific file path pattern for FileWriteTool)
    return _input_matches_rule_content(rule.rule_content, tool_name, input)


def _input_matches_rule_content(
    rule_content: str,
    tool_name: str,
    input: dict[str, Any],
) -> bool:
    """Check if tool input matches a rule's content constraint."""
    # For Bash tool, match against command
    if tool_name.lower() in ("bash", "shell"):
        command = input.get("command", "")
        return _wildcard_match(rule_content, command)

    # For file tools, match against file path
    if tool_name.lower() in ("read", "write", "edit", "fileread", "filewrite", "fileedit"):
        file_path = input.get("file_path", "")
        return _wildcard_match(rule_content, file_path)

    return False


def _wildcard_match(pattern: str, text: str) -> bool:
    """Simple wildcard matching (supports * and **)."""
    import fnmatch
    return fnmatch.fnmatch(text, pattern)


def check_write_permission_for_tool(
    tool: Any,
    input: dict[str, Any],
    permission_context: ToolPermissionContext,
) -> PermissionResult:
    """Check write permission for a file tool."""
    result = check_permission(tool.name, input, permission_context)
    if result.decision == "allow":
        return PermissionAllowDecision(behavior="allow", updated_input=input)
    elif result.decision == "deny":
        return PermissionDenyDecision(
            behavior="deny",
            reason=result.message or "Permission denied",
        )
    else:
        return PermissionAllowDecision(behavior="allow", updated_input=input)


def check_read_permission_for_tool(
    tool: Any,
    input: dict[str, Any],
    permission_context: ToolPermissionContext,
) -> PermissionResult:
    """Check read permission for a file tool."""
    result = check_permission(tool.name, input, permission_context)
    if result.decision == "allow":
        return PermissionAllowDecision(behavior="allow", updated_input=input)
    elif result.decision == "deny":
        return PermissionDenyDecision(
            behavior="deny",
            reason=result.message or "Permission denied",
        )
    else:
        return PermissionAllowDecision(behavior="allow", updated_input=input)


def matching_rule_for_input(
    file_path: str,
    permission_context: ToolPermissionContext,
    operation: str,
    behavior: str,
) -> Optional[ToolPermissionRule]:
    """Find a matching rule for a given file path and operation."""
    rules_by_source = (
        permission_context.always_deny_rules
        if behavior == "deny"
        else permission_context.always_allow_rules
    )

    for source, rules in rules_by_source.items():
        for rule in rules:
            if rule.rule_content and _wildcard_match(rule.rule_content, file_path):
                return rule

    return None
