"""
ID types used throughout the system.

Port of: src/types/ids.ts
"""

from __future__ import annotations

from typing import NewType

AgentId = NewType("AgentId", str)
SessionId = NewType("SessionId", str)


def as_agent_id(value: str) -> AgentId:
    return AgentId(value)


def as_session_id(value: str) -> SessionId:
    return SessionId(value)
