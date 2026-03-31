from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from claude_code_py.engine.models import (
    AssistantMessage,
    ConversationMessage,
    TextBlock,
    ToolResultMessage,
    ToolUseBlock,
    UserMessage,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class SessionMetadata:
    session_id: str
    cwd: str
    created_at: str
    updated_at: str
    title: str


@dataclass(slots=True)
class LoadedSession:
    metadata: SessionMetadata
    messages: list[ConversationMessage]


class SessionStore:
    """Persist conversation transcripts under the app home directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.sessions_dir = self.root / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, cwd: Path, title: str | None = None) -> SessionMetadata:
        session_id = str(uuid4())
        now = _utc_now().isoformat()
        metadata = SessionMetadata(
            session_id=session_id,
            cwd=str(cwd),
            created_at=now,
            updated_at=now,
            title=title or f"Session {session_id[:8]}",
        )
        self._ensure_session_dir(session_id)
        self._write_metadata(metadata)
        self._transcript_path(session_id).write_text("", encoding="utf-8")
        return metadata

    def save_transcript(
        self,
        *,
        metadata: SessionMetadata,
        messages: list[ConversationMessage],
        title: str | None = None,
    ) -> SessionMetadata:
        updated = SessionMetadata(
            session_id=metadata.session_id,
            cwd=metadata.cwd,
            created_at=metadata.created_at,
            updated_at=_utc_now().isoformat(),
            title=title or metadata.title,
        )
        self._ensure_session_dir(updated.session_id)
        transcript = self._transcript_path(updated.session_id)
        with transcript.open("w", encoding="utf-8") as handle:
            for message in messages:
                handle.write(json.dumps(self._serialize_message(message), ensure_ascii=False))
                handle.write("\n")
        self._write_metadata(updated)
        return updated

    def load_session(self, session_id: str) -> LoadedSession:
        metadata = self._read_metadata(session_id)
        transcript_path = self._transcript_path(session_id)
        messages: list[ConversationMessage] = []
        if transcript_path.exists():
            for raw_line in transcript_path.read_text(encoding="utf-8").splitlines():
                if not raw_line.strip():
                    continue
                payload = json.loads(raw_line)
                messages.append(self._deserialize_message(payload))
        return LoadedSession(metadata=metadata, messages=messages)

    def get_session_metadata(self, session_id: str) -> SessionMetadata | None:
        metadata_path = self._metadata_path(session_id)
        if not metadata_path.exists():
            return None
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        return SessionMetadata(**payload)

    def list_sessions(self) -> list[SessionMetadata]:
        sessions: list[SessionMetadata] = []
        for session_dir in sorted(self.sessions_dir.iterdir()):
            if not session_dir.is_dir():
                continue
            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            sessions.append(SessionMetadata(**payload))
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return sessions

    def latest_session_id(self) -> str | None:
        sessions = self.list_sessions()
        return sessions[0].session_id if sessions else None

    def _ensure_session_dir(self, session_id: str) -> Path:
        path = self.sessions_dir / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _metadata_path(self, session_id: str) -> Path:
        return self.sessions_dir / session_id / "metadata.json"

    def _transcript_path(self, session_id: str) -> Path:
        return self.sessions_dir / session_id / "transcript.jsonl"

    def _write_metadata(self, metadata: SessionMetadata) -> None:
        self._metadata_path(metadata.session_id).write_text(
            json.dumps(asdict(metadata), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _read_metadata(self, session_id: str) -> SessionMetadata:
        payload = json.loads(
            self._metadata_path(session_id).read_text(encoding="utf-8")
        )
        return SessionMetadata(**payload)

    @staticmethod
    def _serialize_message(message: ConversationMessage) -> dict[str, Any]:
        if isinstance(message, UserMessage):
            return {
                "kind": "user",
                "content": message.content,
                "is_meta": message.is_meta,
            }
        if isinstance(message, ToolResultMessage):
            return {
                "kind": "tool_result",
                "tool_use_id": message.tool_use_id,
                "content": message.content,
                "is_error": message.is_error,
            }
        return {
            "kind": "assistant",
            "request_id": message.request_id,
            "blocks": [SessionStore._serialize_block(block) for block in message.blocks],
        }

    @staticmethod
    def _serialize_block(block: TextBlock | ToolUseBlock) -> dict[str, Any]:
        if isinstance(block, TextBlock):
            return {"type": "text", "text": block.text}
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }

    @staticmethod
    def _deserialize_message(payload: dict[str, Any]) -> ConversationMessage:
        kind = payload["kind"]
        if kind == "user":
            return UserMessage(
                content=str(payload["content"]),
                is_meta=bool(payload.get("is_meta", False)),
            )
        if kind == "tool_result":
            return ToolResultMessage(
                tool_use_id=str(payload["tool_use_id"]),
                content=str(payload["content"]),
                is_error=bool(payload.get("is_error", False)),
            )
        if kind != "assistant":
            raise ValueError(f"Unsupported message kind: {kind}")
        blocks: list[TextBlock | ToolUseBlock] = []
        for block in payload.get("blocks", []):
            if block["type"] == "text":
                blocks.append(TextBlock(text=str(block.get("text", ""))))
            elif block["type"] == "tool_use":
                blocks.append(
                    ToolUseBlock(
                        id=str(block.get("id", "")),
                        name=str(block.get("name", "")),
                        input=dict(block.get("input", {}) or {}),
                    )
                )
        return AssistantMessage(
            blocks=blocks,
            request_id=payload.get("request_id"),
        )
