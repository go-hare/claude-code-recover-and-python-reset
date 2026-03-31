"""
Policy limits types.

Port of: src/services/policyLimits/types.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PolicyLimitConfig:
    max_turns_per_session: Optional[int] = None
    max_tokens_per_turn: Optional[int] = None
    max_tools_per_turn: Optional[int] = None
    allowed_tools: Optional[list[str]] = None
    disallowed_tools: Optional[list[str]] = None
    max_file_size: Optional[int] = None
    allowed_commands: Optional[list[str]] = None
    disallowed_commands: Optional[list[str]] = None
