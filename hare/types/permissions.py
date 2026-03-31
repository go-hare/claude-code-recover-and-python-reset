"""
Pure permission type definitions extracted to break import cycles.

Port of: src/types/permissions.ts

This file contains only type definitions and constants with no runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union

# ============================================================================
# Permission Modes
# ============================================================================

ExternalPermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

EXTERNAL_PERMISSION_MODES: list[ExternalPermissionMode] = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

InternalPermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",
    "bubble",
]

PermissionMode = InternalPermissionMode

INTERNAL_PERMISSION_MODES: list[PermissionMode] = [
    *EXTERNAL_PERMISSION_MODES,
    "auto",
]

PERMISSION_MODES = INTERNAL_PERMISSION_MODES

# ============================================================================
# Permission Behaviors
# ============================================================================

PermissionBehavior = Literal["allow", "deny", "ask"]

# ============================================================================
# Permission Rules
# ============================================================================

PermissionRuleSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "cliArg",
    "command",
    "session",
]


@dataclass
class PermissionRuleValue:
    tool_name: str
    rule_content: Optional[str] = None


@dataclass
class PermissionRule:
    source: PermissionRuleSource
    rule_behavior: PermissionBehavior
    rule_value: PermissionRuleValue


# ============================================================================
# Permission Updates
# ============================================================================

PermissionUpdateDestination = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "session",
    "cliArg",
]


@dataclass
class AddRulesUpdate:
    type: Literal["addRules"] = "addRules"
    destination: PermissionUpdateDestination = "session"
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"


@dataclass
class ReplaceRulesUpdate:
    type: Literal["replaceRules"] = "replaceRules"
    destination: PermissionUpdateDestination = "session"
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"


@dataclass
class RemoveRulesUpdate:
    type: Literal["removeRules"] = "removeRules"
    destination: PermissionUpdateDestination = "session"
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"


@dataclass
class SetModeUpdate:
    type: Literal["setMode"] = "setMode"
    destination: PermissionUpdateDestination = "session"
    mode: ExternalPermissionMode = "default"


@dataclass
class AddDirectoriesUpdate:
    type: Literal["addDirectories"] = "addDirectories"
    destination: PermissionUpdateDestination = "session"
    directories: list[str] = field(default_factory=list)


@dataclass
class RemoveDirectoriesUpdate:
    type: Literal["removeDirectories"] = "removeDirectories"
    destination: PermissionUpdateDestination = "session"
    directories: list[str] = field(default_factory=list)


PermissionUpdate = Union[
    AddRulesUpdate,
    ReplaceRulesUpdate,
    RemoveRulesUpdate,
    SetModeUpdate,
    AddDirectoriesUpdate,
    RemoveDirectoriesUpdate,
]

WorkingDirectorySource = PermissionRuleSource


@dataclass
class AdditionalWorkingDirectory:
    path: str
    source: WorkingDirectorySource


# ============================================================================
# Permission Decisions & Results
# ============================================================================


@dataclass
class PermissionAllowDecision:
    behavior: Literal["allow"] = "allow"
    updated_input: Optional[dict[str, Any]] = None
    user_modified: Optional[bool] = None
    decision_reason: Optional[Any] = None
    tool_use_id: Optional[str] = None
    accept_feedback: Optional[str] = None
    content_blocks: Optional[list[Any]] = None


@dataclass
class PendingClassifierCheck:
    command: str
    cwd: str
    descriptions: list[str]


@dataclass
class PermissionAskDecision:
    behavior: Literal["ask"] = "ask"
    message: str = ""
    updated_input: Optional[dict[str, Any]] = None
    decision_reason: Optional[Any] = None
    suggestions: Optional[list[PermissionUpdate]] = None
    blocked_path: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    pending_classifier_check: Optional[PendingClassifierCheck] = None
    content_blocks: Optional[list[Any]] = None


@dataclass
class PermissionDenyDecision:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    decision_reason: Optional[Any] = None
    tool_use_id: Optional[str] = None


PermissionDecision = Union[
    PermissionAllowDecision,
    PermissionAskDecision,
    PermissionDenyDecision,
]


@dataclass
class PermissionPassthrough:
    behavior: Literal["passthrough"] = "passthrough"
    message: str = ""
    decision_reason: Optional[Any] = None
    suggestions: Optional[list[PermissionUpdate]] = None
    blocked_path: Optional[str] = None
    pending_classifier_check: Optional[PendingClassifierCheck] = None


PermissionResult = Union[PermissionDecision, PermissionPassthrough]


# ============================================================================
# Tool Permission Context
# ============================================================================

ToolPermissionRulesBySource = dict[PermissionRuleSource, list[str]]


@dataclass
class ToolPermissionContext:
    mode: PermissionMode = "default"
    additional_working_directories: dict[str, AdditionalWorkingDirectory] = field(
        default_factory=dict
    )
    always_allow_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    always_deny_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    always_ask_rules: ToolPermissionRulesBySource = field(default_factory=dict)
    is_bypass_permissions_mode_available: bool = False
    is_auto_mode_available: Optional[bool] = None
    stripped_dangerous_rules: Optional[ToolPermissionRulesBySource] = None
    should_avoid_permission_prompts: Optional[bool] = None
    await_automated_checks_before_dialog: Optional[bool] = None
    pre_plan_mode: Optional[PermissionMode] = None


# ============================================================================
# Classifier Types
# ============================================================================

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass
class ClassifierResult:
    matches: bool
    matched_description: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "low"
    reason: str = ""


@dataclass
class YoloClassifierResult:
    should_block: bool
    reason: str
    model: str
    thinking: Optional[str] = None
    unavailable: Optional[bool] = None
    transcript_too_long: Optional[bool] = None
    duration_ms: Optional[int] = None
    stage: Optional[Literal["fast", "thinking"]] = None
