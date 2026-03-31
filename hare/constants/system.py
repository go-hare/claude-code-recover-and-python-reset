"""
System constants.

Port of: src/constants/system.ts
"""

from __future__ import annotations

import os
from typing import Literal

from hare.constants.product import VERSION
from hare.utils.model.providers import get_api_provider

DEFAULT_PREFIX = "You are Claude Code, Anthropic's official CLI for Claude."
AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX = "You are Claude Code, Anthropic's official CLI for Claude, running within the Claude Agent SDK."
AGENT_SDK_PREFIX = "You are a Claude agent, built on Anthropic's Claude Agent SDK."

CLI_SYSPROMPT_PREFIXES = frozenset({
    DEFAULT_PREFIX,
    AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX,
    AGENT_SDK_PREFIX,
})

CLISyspromptPrefix = str


def get_cli_sysprompt_prefix(
    *,
    is_non_interactive: bool = False,
    has_append_system_prompt: bool = False,
) -> CLISyspromptPrefix:
    """Get the appropriate system prompt prefix."""
    if get_api_provider() == "vertex":
        return DEFAULT_PREFIX

    if is_non_interactive:
        if has_append_system_prompt:
            return AGENT_SDK_CLAUDE_CODE_PRESET_PREFIX
        return AGENT_SDK_PREFIX

    return DEFAULT_PREFIX


def get_attribution_header(fingerprint: str) -> str:
    """Get attribution header for API requests."""
    version = f"{VERSION}.{fingerprint}"
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "unknown")
    return f"x-anthropic-billing-header: cc_version={version}; cc_entrypoint={entrypoint};"
