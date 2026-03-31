"""
Session types.

Port of: src/assistant/sessionHistory
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SessionInfo:
    session_id: str
    created_at: float = 0.0
    updated_at: float = 0.0
    model: str = ""
    message_count: int = 0
    title: str = ""
    project_dir: str = ""


@dataclass
class SessionHistory:
    sessions: list[SessionInfo] = field(default_factory=list)

    def add_session(self, session: SessionInfo) -> None:
        self.sessions.insert(0, session)

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        for s in self.sessions:
            if s.session_id == session_id:
                return s
        return None

    def list_recent(self, limit: int = 20) -> list[SessionInfo]:
        return self.sessions[:limit]
