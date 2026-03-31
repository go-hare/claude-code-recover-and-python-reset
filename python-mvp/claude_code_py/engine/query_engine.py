from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path

from claude_code_py.agents.manager import AgentTaskHandle, AgentTaskManager
from claude_code_py.api.base import ModelClient
from claude_code_py.config import AppConfig
from claude_code_py.engine.context import ReadFileState, ToolContext
from claude_code_py.engine.models import ConversationMessage, QueryResult, UserMessage
from claude_code_py.engine.query_loop import run_query_loop
from claude_code_py.permissions.policy import PermissionPolicy
from claude_code_py.sessions.storage import SessionMetadata, SessionStore
from claude_code_py.tools.registry import ToolRegistry


class QueryEngine:
    """Conversation-scoped engine that owns messages and subagent spawning."""

    def __init__(
        self,
        *,
        config: AppConfig,
        model_client: ModelClient,
        tool_registry: ToolRegistry,
        permission_policy: PermissionPolicy,
        task_manager: AgentTaskManager | None = None,
        message_history: list[ConversationMessage] | None = None,
        session_store: SessionStore | None = None,
        session_metadata: SessionMetadata | None = None,
        depth: int = 0,
    ) -> None:
        self.config = config
        self.model_client = model_client
        self.tool_registry = tool_registry
        self.permission_policy = permission_policy
        self.task_manager = task_manager or AgentTaskManager()
        self._messages = list(message_history or [])
        self._read_file_state: dict[str, ReadFileState] = {}
        self.session_store = session_store or SessionStore(self.config.resolved_config_home)
        self.session_metadata = session_metadata or self.session_store.create_session(
            self.config.cwd
        )
        self.depth = depth
        self._persist_session()

    @property
    def messages(self) -> list[ConversationMessage]:
        return list(self._messages)

    @property
    def session_id(self) -> str:
        return self.session_metadata.session_id

    def _build_context(self) -> ToolContext:
        return ToolContext(
            cwd=self.config.cwd,
            permission_policy=self.permission_policy,
            registry=self.tool_registry,
            agent_runner=self,
            task_manager=self.task_manager,
            read_file_state=self._read_file_state,
            max_output_chars=self.config.max_tool_output_chars,
        )

    def _persist_session(self, title_hint: str | None = None) -> None:
        title = self._derive_title(title_hint=title_hint)
        self.session_metadata = self.session_store.save_transcript(
            metadata=self.session_metadata,
            messages=self._messages,
            title=title,
        )

    def _derive_title(self, title_hint: str | None = None) -> str:
        current_title = self.session_metadata.title
        if current_title and not current_title.startswith("Session "):
            return current_title
        if title_hint:
            normalized_hint = " ".join(title_hint.split()).strip()
            if normalized_hint:
                return normalized_hint[:80]

        for message in self._messages:
            if not isinstance(message, UserMessage) or message.is_meta:
                continue
            title = _extract_title_from_prompt(message.content)
            if title:
                return title[:80]
        return current_title

    async def submit(self, prompt: str, *, title_hint: str | None = None) -> QueryResult:
        """Append a user prompt and run the main loop."""

        self._messages.append(UserMessage(content=prompt))
        result = await run_query_loop(
            model_client=self.model_client,
            system_prompt=self.config.system_prompt,
            messages=self._messages,
            registry=self.tool_registry,
            context=self._build_context(),
            model=self.config.model,
            max_turns=self.config.max_turns,
            max_output_tokens=self.config.max_output_tokens,
            background=False,
        )
        self._messages = result.messages
        self._persist_session(title_hint=title_hint)
        return result

    def _build_child_engine(
        self,
        *,
        description: str,
        allowed_tools: list[str] | None = None,
    ) -> "QueryEngine":
        child_registry = self.tool_registry.subset(allowed=allowed_tools)
        if self.depth + 1 >= self.config.max_agent_depth:
            child_registry = child_registry.subset(denied=["Agent"])

        child_policy = copy.deepcopy(self.permission_policy)
        child_config = replace(self.config)
        child_session = self.session_store.create_session(
            child_config.cwd,
            title=f"Agent: {description}",
        )
        return QueryEngine(
            config=child_config,
            model_client=self.model_client,
            tool_registry=child_registry,
            permission_policy=child_policy,
            task_manager=self.task_manager,
            session_store=self.session_store,
            session_metadata=child_session,
            depth=self.depth + 1,
        )

    def new_session(self, title: str | None = None) -> "QueryEngine":
        """Create a sibling engine with a fresh persistent session."""

        metadata = self.session_store.create_session(self.config.cwd, title=title)
        return QueryEngine(
            config=replace(self.config),
            model_client=self.model_client,
            tool_registry=self.tool_registry,
            permission_policy=copy.deepcopy(self.permission_policy),
            session_store=self.session_store,
            session_metadata=metadata,
        )

    def load_session(self, session_id: str) -> "QueryEngine":
        """Restore a saved session into a new engine instance."""

        loaded = self.session_store.load_session(session_id)
        restored_config = replace(self.config, cwd=Path(loaded.metadata.cwd))
        return QueryEngine(
            config=restored_config,
            model_client=self.model_client,
            tool_registry=self.tool_registry,
            permission_policy=copy.deepcopy(self.permission_policy),
            message_history=loaded.messages,
            session_store=self.session_store,
            session_metadata=loaded.metadata,
        )

    async def run_subagent(
        self,
        *,
        prompt: str,
        description: str,
        allowed_tools: list[str] | None = None,
    ) -> QueryResult:
        """Run a child agent synchronously."""

        child_engine = self._build_child_engine(
            description=description,
            allowed_tools=allowed_tools,
        )
        return await child_engine.submit(prompt, title_hint=description)

    def spawn_subagent(
        self,
        *,
        prompt: str,
        description: str,
        allowed_tools: list[str] | None = None,
    ) -> AgentTaskHandle:
        """Run a child agent in the background."""

        child_engine = self._build_child_engine(
            description=description,
            allowed_tools=allowed_tools,
        )
        return self.task_manager.start(
            description=description,
            runner=lambda: child_engine.submit(prompt, title_hint=description),
        )


def _extract_title_from_prompt(prompt: str) -> str:
    for raw_line in prompt.splitlines():
        line = " ".join(raw_line.split()).strip()
        if not line:
            continue
        if line.lower().startswith("base directory for this skill:"):
            continue
        return line
    return " ".join(prompt.split()).strip()
