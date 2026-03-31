"""
Policy limits enforcement.

Port of: src/services/policyLimits/index.ts
"""

from __future__ import annotations

from typing import Any, Optional

from hare.services.policy_limits.types import PolicyLimitConfig


class PolicyLimits:
    def __init__(self, config: Optional[PolicyLimitConfig] = None) -> None:
        self._config = config or PolicyLimitConfig()
        self._turn_count = 0

    @property
    def config(self) -> PolicyLimitConfig:
        return self._config

    def on_turn(self) -> None:
        self._turn_count += 1

    def is_turn_limit_reached(self) -> bool:
        if self._config.max_turns_per_session is None:
            return False
        return self._turn_count >= self._config.max_turns_per_session

    def is_tool_allowed(self, tool_name: str) -> bool:
        if self._config.disallowed_tools and tool_name in self._config.disallowed_tools:
            return False
        if self._config.allowed_tools is not None:
            return tool_name in self._config.allowed_tools
        return True

    def is_command_allowed(self, command: str) -> bool:
        if self._config.disallowed_commands and command in self._config.disallowed_commands:
            return False
        if self._config.allowed_commands is not None:
            return command in self._config.allowed_commands
        return True


_global_limits: Optional[PolicyLimits] = None


def get_policy_limits() -> PolicyLimits:
    global _global_limits
    if _global_limits is None:
        _global_limits = PolicyLimits()
    return _global_limits


def check_policy_limit(limit_type: str, value: Any = None) -> bool:
    """Check if a specific policy limit is satisfied."""
    limits = get_policy_limits()
    if limit_type == "turns":
        return not limits.is_turn_limit_reached()
    if limit_type == "tool":
        return limits.is_tool_allowed(str(value))
    if limit_type == "command":
        return limits.is_command_allowed(str(value))
    return True
