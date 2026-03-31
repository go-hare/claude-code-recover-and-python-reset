"""
Filesystem permission checks.

Port of: src/utils/permissions/filesystem.ts

Handles:
- Dangerous file/directory detection
- Path safety checks for auto-editing
- Read/write permission for file tools
- Working directory path validation
- Rule matching with gitignore-style patterns
"""

from __future__ import annotations

import fnmatch
import os
import posixpath
import re
from typing import Any, Optional, Sequence

from hare.types.permissions import (
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionDenyDecision,
    PermissionResult,
    ToolPermissionContext,
)
from hare.utils.path import expand_path

DANGEROUS_FILES = (
    ".gitconfig",
    ".gitmodules",
    ".bashrc",
    ".bash_profile",
    ".zshrc",
    ".zprofile",
    ".profile",
    ".ripgreprc",
    ".mcp.json",
    ".claude.json",
)

DANGEROUS_DIRECTORIES = (
    ".git",
    ".vscode",
    ".idea",
    ".claude",
)


def normalize_case_for_comparison(path: str) -> str:
    """Normalize path case for safe comparison."""
    return path.lower()


def check_path_safety_for_auto_edit(
    path: str,
    precomputed_paths: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """
    Check if a path is safe for auto-editing.
    Returns {"safe": True} or {"safe": False, "message": str, "classifierApprovable": bool}
    """
    paths_to_check = precomputed_paths or [expand_path(path)]

    # Check for suspicious Windows patterns
    for p in paths_to_check:
        if _has_suspicious_windows_pattern(p):
            return {
                "safe": False,
                "message": f"Path {path} contains a suspicious Windows path pattern.",
                "classifierApprovable": False,
            }

    # Check for Claude config files
    for p in paths_to_check:
        if _is_claude_config_file_path(p):
            return {
                "safe": False,
                "message": f"Claude requested permissions to write to {path}, but you haven't granted it yet.",
                "classifierApprovable": True,
            }

    # Check for dangerous files
    for p in paths_to_check:
        if _is_dangerous_file_path(p):
            return {
                "safe": False,
                "message": f"Claude requested permissions to edit {path} which is a sensitive file.",
                "classifierApprovable": True,
            }

    return {"safe": True}


def _has_suspicious_windows_pattern(path: str) -> bool:
    """Detect suspicious Windows path patterns."""
    if os.name == "nt":
        colon_idx = path.find(":", 2)
        if colon_idx != -1:
            return True

    if re.search(r"~\d", path):
        return True
    if path.startswith("\\\\?\\") or path.startswith("\\\\.\\"):
        return True
    if path.startswith("//?/") or path.startswith("//./"):
        return True
    if re.search(r"[.\s]+$", path):
        return True
    if re.search(r"\.(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", path, re.IGNORECASE):
        return True
    if re.search(r"(^|/|\\)\.{3,}(/|\\|$)", path):
        return True
    if path.startswith("\\\\") or path.startswith("//"):
        return True

    return False


def _is_claude_config_file_path(path: str) -> bool:
    """Check if a path is a Claude config file."""
    expanded = expand_path(path)
    normalized = normalize_case_for_comparison(expanded)
    sep = os.sep

    if (normalized.endswith(f"{sep}.claude{sep}settings.json") or
            normalized.endswith(f"{sep}.claude{sep}settings.local.json")):
        return True

    return False


def _is_dangerous_file_path(path: str) -> bool:
    """Check if a path is dangerous to auto-edit."""
    expanded = expand_path(path)
    segments = expanded.replace("\\", "/").split("/")
    filename = segments[-1] if segments else ""

    # Check UNC paths
    if path.startswith("\\\\") or path.startswith("//"):
        return True

    # Check dangerous directories
    for seg in segments:
        norm_seg = normalize_case_for_comparison(seg)
        for d in DANGEROUS_DIRECTORIES:
            if norm_seg == normalize_case_for_comparison(d):
                return True

    # Check dangerous files
    if filename:
        norm_name = normalize_case_for_comparison(filename)
        for df in DANGEROUS_FILES:
            if normalize_case_for_comparison(df) == norm_name:
                return True

    return False


def path_in_working_path(path: str, working_path: str) -> bool:
    """Check if path is within working_path."""
    abs_path = expand_path(path)
    abs_working = expand_path(working_path)

    # macOS symlink normalization
    for prefix in ["/private/var/", "/private/tmp"]:
        short = prefix.replace("/private", "")
        abs_path = abs_path.replace(prefix, short)
        abs_working = abs_working.replace(prefix, short)

    norm_path = normalize_case_for_comparison(abs_path)
    norm_working = normalize_case_for_comparison(abs_working)

    try:
        rel = os.path.relpath(norm_path, norm_working)
    except ValueError:
        return False

    if rel == "" or rel == ".":
        return True
    if rel.startswith(".."):
        return False
    return not os.path.isabs(rel)


def path_in_allowed_working_path(
    path: str,
    context: ToolPermissionContext,
    precomputed: Optional[Sequence[str]] = None,
) -> bool:
    """Check if path is within any allowed working directory."""
    from hare.bootstrap.state import get_original_cwd

    paths_to_check = list(precomputed) if precomputed else [expand_path(path)]
    working_dirs = [get_original_cwd()]
    working_dirs.extend(context.additional_working_directories.keys())

    return all(
        any(path_in_working_path(p, wd) for wd in working_dirs)
        for p in paths_to_check
    )


def matching_rule_for_input(
    path: str,
    context: ToolPermissionContext,
    tool_type: str,
    behavior: str,
) -> Optional[dict]:
    """Find a matching rule for a given path."""
    rules_by_source = (
        context.always_deny_rules if behavior == "deny"
        else context.always_allow_rules if behavior == "allow"
        else context.always_ask_rules
    )

    expanded = expand_path(path)

    for source, rules in rules_by_source.items():
        for rule_content in rules:
            if isinstance(rule_content, str):
                if fnmatch.fnmatch(expanded, rule_content):
                    return {"source": source, "ruleContent": rule_content}
                # Also try matching just the filename
                basename = os.path.basename(expanded)
                if fnmatch.fnmatch(basename, rule_content):
                    return {"source": source, "ruleContent": rule_content}

    return None


def check_read_permission_for_tool(
    tool: Any,
    input: dict[str, Any],
    context: ToolPermissionContext,
) -> dict[str, Any]:
    """Check read permission for a file tool."""
    get_path = getattr(tool, "get_path", None)
    if not callable(get_path):
        return {
            "behavior": "ask",
            "message": f"Claude requested permissions to use {tool.name}, but you haven't granted it yet.",
        }

    path = get_path(input)
    expanded = expand_path(path)

    # Check deny rules
    deny = matching_rule_for_input(path, context, "read", "deny")
    if deny:
        return {"behavior": "deny", "message": f"Permission to read {path} has been denied."}

    # Check ask rules
    ask = matching_rule_for_input(path, context, "read", "ask")
    if ask:
        return {"behavior": "ask", "message": f"Claude requested permissions to read from {path}."}

    # Allow reads in working directories
    if path_in_allowed_working_path(path, context):
        return {"behavior": "allow", "updatedInput": input}

    # Check allow rules
    allow = matching_rule_for_input(path, context, "read", "allow")
    if allow:
        return {"behavior": "allow", "updatedInput": input}

    return {
        "behavior": "ask",
        "message": f"Claude requested permissions to read from {path}.",
        "suggestions": generate_suggestions(path, "read", context),
    }


def check_write_permission_for_tool(
    tool: Any,
    input: dict[str, Any],
    context: ToolPermissionContext,
    precomputed: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Check write permission for a file tool."""
    get_path = getattr(tool, "get_path", None)
    if not callable(get_path):
        return {
            "behavior": "ask",
            "message": f"Claude requested permissions to use {tool.name}.",
        }

    path = get_path(input)
    paths_to_check = list(precomputed) if precomputed else [expand_path(path)]

    # Check deny rules
    for p in paths_to_check:
        deny = matching_rule_for_input(p, context, "edit", "deny")
        if deny:
            return {"behavior": "deny", "message": f"Permission to edit {path} has been denied."}

    # Safety checks
    safety = check_path_safety_for_auto_edit(path, paths_to_check)
    if not safety.get("safe"):
        return {
            "behavior": "ask",
            "message": safety.get("message", ""),
            "suggestions": generate_suggestions(path, "write", context, paths_to_check),
        }

    # Check ask rules
    for p in paths_to_check:
        ask = matching_rule_for_input(p, context, "edit", "ask")
        if ask:
            return {"behavior": "ask", "message": f"Claude requested permissions to write to {path}."}

    # acceptEdits mode in working dir
    is_in_wd = path_in_allowed_working_path(path, context, paths_to_check)
    if context.mode == "acceptEdits" and is_in_wd:
        return {"behavior": "allow", "updatedInput": input}

    # Check allow rules
    allow = matching_rule_for_input(path, context, "edit", "allow")
    if allow:
        return {"behavior": "allow", "updatedInput": input}

    return {
        "behavior": "ask",
        "message": f"Claude requested permissions to write to {path}.",
        "suggestions": generate_suggestions(path, "write", context, paths_to_check),
    }


def generate_suggestions(
    file_path: str,
    operation_type: str,
    context: ToolPermissionContext,
    precomputed: Optional[Sequence[str]] = None,
) -> list[dict[str, Any]]:
    """Generate permission update suggestions."""
    is_outside_wd = not path_in_allowed_working_path(file_path, context, precomputed)

    if operation_type == "read" and is_outside_wd:
        dir_path = os.path.dirname(expand_path(file_path))
        return [{
            "type": "addRules",
            "rules": [{"toolName": "Read", "ruleContent": dir_path + "/**"}],
            "behavior": "allow",
            "destination": "session",
        }]

    should_suggest = context.mode in ("default", "plan")

    if operation_type in ("write", "create"):
        suggestions: list[dict[str, Any]] = []
        if should_suggest:
            suggestions.append({
                "type": "setMode",
                "mode": "acceptEdits",
                "destination": "session",
            })
        if is_outside_wd:
            dir_path = os.path.dirname(expand_path(file_path))
            suggestions.append({
                "type": "addDirectories",
                "directories": [dir_path],
                "destination": "session",
            })
        return suggestions

    if should_suggest:
        return [{"type": "setMode", "mode": "acceptEdits", "destination": "session"}]
    return []
