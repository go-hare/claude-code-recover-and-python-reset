"""
Tool progress types extracted to break import cycles.

Port of: src/types/tools.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class BashProgress:
    type: Literal["bash"] = "bash"
    command: str = ""
    stdout: str = ""
    stderr: str = ""
    interrupted: bool = False
    exit_code: Optional[int] = None


@dataclass
class AgentToolProgress:
    type: Literal["agent"] = "agent"
    agent_id: str = ""
    status: str = ""
    content: str = ""


@dataclass
class MCPProgress:
    type: Literal["mcp"] = "mcp"
    server_name: str = ""
    tool_name: str = ""
    status: str = ""


@dataclass
class SkillToolProgress:
    type: Literal["skill"] = "skill"
    skill_name: str = ""
    status: str = ""


@dataclass
class TaskOutputProgress:
    type: Literal["task_output"] = "task_output"
    task_id: str = ""
    output: str = ""


@dataclass
class WebSearchProgress:
    type: Literal["web_search"] = "web_search"
    query: str = ""
    status: str = ""


@dataclass
class REPLToolProgress:
    type: Literal["repl"] = "repl"
    tool_name: str = ""
    input_data: Any = None
    output: str = ""


ToolProgressData = (
    BashProgress
    | AgentToolProgress
    | MCPProgress
    | SkillToolProgress
    | TaskOutputProgress
    | WebSearchProgress
    | REPLToolProgress
)


@dataclass
class ToolProgress:
    tool_use_id: str = ""
    data: Optional[ToolProgressData] = None
