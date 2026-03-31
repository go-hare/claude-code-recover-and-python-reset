"""
Agent memory - context sharing between parent and child agents.

Port of: src/tools/AgentTool/agentMemory.ts + agentMemorySnapshot.ts
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentMemorySnapshot:
    """Snapshot of an agent's memory state."""
    agent_id: str
    agent_type: str
    timestamp: float = field(default_factory=time.time)
    messages_count: int = 0
    token_count: int = 0
    files_read: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemoryStore:
    """Store for agent memory across the session."""
    _snapshots: dict[str, AgentMemorySnapshot] = field(default_factory=dict)
    _parent_context: dict[str, str] = field(default_factory=dict)

    def save_snapshot(self, snapshot: AgentMemorySnapshot) -> None:
        self._snapshots[snapshot.agent_id] = snapshot

    def get_snapshot(self, agent_id: str) -> Optional[AgentMemorySnapshot]:
        return self._snapshots.get(agent_id)

    def get_all_snapshots(self) -> list[AgentMemorySnapshot]:
        return list(self._snapshots.values())

    def set_parent_context(self, key: str, value: str) -> None:
        self._parent_context[key] = value

    def get_parent_context(self, key: str) -> Optional[str]:
        return self._parent_context.get(key)

    def clear(self) -> None:
        self._snapshots.clear()
        self._parent_context.clear()


_global_memory_store = AgentMemoryStore()


def get_agent_memory_store() -> AgentMemoryStore:
    return _global_memory_store


def save_agent_snapshot(
    agent_id: str,
    agent_type: str,
    *,
    messages_count: int = 0,
    token_count: int = 0,
    files_read: list[str] | None = None,
    files_modified: list[str] | None = None,
    summary: str = "",
) -> AgentMemorySnapshot:
    snapshot = AgentMemorySnapshot(
        agent_id=agent_id,
        agent_type=agent_type,
        messages_count=messages_count,
        token_count=token_count,
        files_read=files_read or [],
        files_modified=files_modified or [],
        summary=summary,
    )
    _global_memory_store.save_snapshot(snapshot)
    return snapshot
