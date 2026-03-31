"""
Settings types and schema.

Port of: src/utils/settings/types.ts

Defines the structure of Claude Code settings files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, TypedDict


class PermissionRule(TypedDict, total=False):
    type: str  # "allow" | "deny"
    tool: str
    pattern: str
    description: str


class McpServerSettingsConfig(TypedDict, total=False):
    command: str
    args: list[str]
    env: dict[str, str]
    url: str
    headers: dict[str, str]
    type: str
    enabled: bool


class SandboxSettings(TypedDict, total=False):
    enabled: bool
    excludedCommands: list[str]


class SettingsJson(TypedDict, total=False):
    """Settings JSON schema matching the TypeScript SettingsSchema."""
    permissions: list[PermissionRule]
    allowedTools: list[str]
    deniedTools: list[str]
    customInstructions: str
    mcpServers: dict[str, McpServerSettingsConfig]
    env: dict[str, str]
    model: str
    smallModel: str
    largeModel: str
    theme: str
    verbose: bool
    sandbox: SandboxSettings
    hooks: dict[str, Any]
    contextFiles: list[str]
    trust: list[str]
    disable: list[str]
    apiKeyHelper: str


def SettingsSchema() -> dict[str, Any]:
    """Return the settings schema as a dict (simplified from Zod)."""
    return {
        "type": "object",
        "properties": {
            "permissions": {"type": "array"},
            "allowedTools": {"type": "array", "items": {"type": "string"}},
            "deniedTools": {"type": "array", "items": {"type": "string"}},
            "customInstructions": {"type": "string"},
            "mcpServers": {"type": "object"},
            "env": {"type": "object"},
            "model": {"type": "string"},
            "theme": {"type": "string"},
            "verbose": {"type": "boolean"},
            "sandbox": {"type": "object"},
            "hooks": {"type": "object"},
            "contextFiles": {"type": "array"},
            "trust": {"type": "array"},
            "disable": {"type": "array"},
        },
        "additionalProperties": True,
    }
