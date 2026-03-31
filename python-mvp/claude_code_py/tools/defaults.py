from __future__ import annotations

from claude_code_py.tools.agent import AgentTool
from claude_code_py.tools.bash import BashTool
from claude_code_py.tools.file_edit import FileEditTool
from claude_code_py.tools.file_read import FileReadTool
from claude_code_py.tools.file_write import FileWriteTool
from claude_code_py.tools.glob_search import GlobTool
from claude_code_py.tools.grep import GrepTool
from claude_code_py.tools.registry import ToolRegistry


def build_default_tool_registry() -> ToolRegistry:
    """Build the default Claude Code toolset."""

    return ToolRegistry(
        [
            AgentTool(),
            BashTool(),
            FileEditTool(),
            FileReadTool(),
            FileWriteTool(),
            GlobTool(),
            GrepTool(),
        ]
    )
