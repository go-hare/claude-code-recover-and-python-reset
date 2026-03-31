"""
Hook event definitions.

Port of: src/utils/hooks/hookEvents.ts
"""

from __future__ import annotations

from typing import Literal

HookEvent = Literal[
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "SubagentStop",
]

HOOK_EVENTS: list[HookEvent] = [
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "SubagentStop",
]
