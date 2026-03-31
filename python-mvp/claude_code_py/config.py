from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True)
class AppConfig:
    """Runtime configuration for the Python port."""

    cwd: Path
    model: str = "claude-sonnet-4-5"
    system_prompt: str = (
        "You are a coding agent operating in a terminal. Use tools when needed, "
        "be concise, and explain what you changed."
    )
    max_turns: int = 8
    max_output_tokens: int = 2048
    max_tool_output_chars: int = 4000
    use_stub_model: bool = True
    max_agent_depth: int = 2
    config_home: Path | None = None

    @classmethod
    def from_env(cls, cwd: Path | None = None) -> "AppConfig":
        """Build config from environment variables."""

        resolved_cwd = cwd or Path.cwd()
        config_home_raw = os.getenv("CLAUDE_CODE_PY_HOME")
        config_home = (
            Path(config_home_raw).expanduser().resolve()
            if config_home_raw
            else Path.home().joinpath(".claude-code-py").resolve()
        )
        return cls(
            cwd=resolved_cwd,
            model=os.getenv("CLAUDE_CODE_PY_MODEL", "claude-sonnet-4-5"),
            max_turns=int(os.getenv("CLAUDE_CODE_PY_MAX_TURNS", "8")),
            max_output_tokens=int(
                os.getenv("CLAUDE_CODE_PY_MAX_OUTPUT_TOKENS", "2048")
            ),
            max_tool_output_chars=int(
                os.getenv("CLAUDE_CODE_PY_MAX_TOOL_OUTPUT_CHARS", "4000")
            ),
            use_stub_model=os.getenv("CLAUDE_CODE_PY_USE_STUB", "1") != "0",
            max_agent_depth=int(os.getenv("CLAUDE_CODE_PY_MAX_AGENT_DEPTH", "2")),
            config_home=config_home,
        )

    @property
    def resolved_config_home(self) -> Path:
        """Return the configured app home directory."""

        if self.config_home is None:
            return Path.home().joinpath(".claude-code-py").resolve()
        return self.config_home
