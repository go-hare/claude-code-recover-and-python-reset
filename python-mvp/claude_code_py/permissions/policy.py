from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class PermissionMode(StrEnum):
    DEFAULT = "default"
    PLAN = "plan"
    ACCEPT_EDITS = "accept_edits"
    BYPASS = "bypass"


@dataclass(slots=True)
class PermissionDecision:
    allowed: bool
    reason: str


@dataclass(slots=True)
class PermissionPolicy:
    """Minimal permission system for the Python port."""

    mode: PermissionMode = PermissionMode.DEFAULT
    allow_tools: set[str] = field(default_factory=set)
    deny_tools: set[str] = field(default_factory=set)
    deny_background_tools: set[str] = field(default_factory=set)

    def authorize(self, *, tool_name: str, background: bool) -> PermissionDecision:
        if tool_name in self.deny_tools:
            return PermissionDecision(False, "tool is explicitly denied")
        if background and tool_name in self.deny_background_tools:
            return PermissionDecision(False, "tool is denied in background mode")
        if self.allow_tools and tool_name not in self.allow_tools:
            return PermissionDecision(False, "tool is outside the allowlist")
        return PermissionDecision(True, "allowed")
