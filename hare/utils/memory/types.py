"""
Memory types.

Port of: src/utils/memory/types.ts
"""

from __future__ import annotations

from typing import Literal

MemoryType = Literal[
    "user_preference",
    "project_convention",
    "decision",
    "correction",
    "technical_constraint",
    "workflow",
]

MEMORY_TYPE_VALUES: list[str] = [
    "user_preference",
    "project_convention",
    "decision",
    "correction",
    "technical_constraint",
    "workflow",
]
