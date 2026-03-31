"""
Tool registry and tool pool assembly.

Port of: src/tools.ts

This is the central registry for all built-in tools. It maps exactly
to getAllBaseTools() / getTools() / assembleToolPool() in the TS source.
"""

from __future__ import annotations

from typing import Any, Sequence

from hare.tool import Tool, Tools, tool_matches_name
from hare.types.permissions import ToolPermissionContext, ToolPermissionRulesBySource
from hare.utils.env_utils import is_env_truthy

import os

# Re-exports matching TS
ALL_AGENT_DISALLOWED_TOOLS: list[str] = []
CUSTOM_AGENT_DISALLOWED_TOOLS: list[str] = []
ASYNC_AGENT_ALLOWED_TOOLS: list[str] = []
COORDINATOR_MODE_ALLOWED_TOOLS: list[str] = []

# Predefined tool presets that can be used with --tools flag
TOOL_PRESETS = ("default",)


def parse_tool_preset(preset: str) -> str | None:
    lower = preset.lower()
    if lower in TOOL_PRESETS:
        return lower
    return None


def get_tools_for_default_preset() -> list[str]:
    """Get the list of tool names for the default preset, filtering disabled tools."""
    tools = get_all_base_tools()
    return [t.name for t in tools if t.is_enabled()]


def get_all_base_tools() -> list[Tool]:
    """
    Get the complete exhaustive list of all tools that could be available
    in the current environment. This is the source of truth for ALL tools.

    NOTE: Mirrors getAllBaseTools() in tools.ts. Tool imports are lazy to match
    the conditional-require pattern in the TS source.
    """
    from hare.tools_impl.BashTool.bash_tool import BashTool
    from hare.tools_impl.FileReadTool.file_read_tool import FileReadTool
    from hare.tools_impl.FileEditTool.file_edit_tool import FileEditTool
    from hare.tools_impl.FileWriteTool.file_write_tool import FileWriteTool
    from hare.tools_impl.GlobTool.glob_tool import GlobTool
    from hare.tools_impl.GrepTool.grep_tool import GrepTool
    from hare.tools_impl.AgentTool.agent_tool import AgentTool
    from hare.tools_impl.WebFetchTool.web_fetch_tool import WebFetchTool
    from hare.tools_impl.WebSearchTool.web_search_tool import WebSearchTool
    from hare.tools_impl.TodoWriteTool.todo_write_tool import TodoWriteTool

    tools: list[Tool] = [
        AgentTool,
        BashTool,
        GlobTool,
        GrepTool,
        FileReadTool,
        FileEditTool,
        FileWriteTool,
        WebFetchTool,
        TodoWriteTool,
        WebSearchTool,
    ]
    return tools


def _get_deny_rule_for_tool(
    permission_context: ToolPermissionContext, tool: Any
) -> bool:
    """Check if a tool is blanket-denied by the permission context."""
    deny_rules = permission_context.always_deny_rules
    for _source, rules in deny_rules.items():
        for rule in rules:
            if tool_matches_name(tool, rule):
                return True
    return False


def filter_tools_by_deny_rules(
    tools: Sequence[Tool], permission_context: ToolPermissionContext
) -> list[Tool]:
    """
    Filters out tools that are blanket-denied by the permission context.
    A tool is filtered out if there's a deny rule matching its name with no
    ruleContent (i.e., a blanket deny for that tool).
    """
    return [t for t in tools if not _get_deny_rule_for_tool(permission_context, t)]


def get_tools(permission_context: ToolPermissionContext) -> list[Tool]:
    """
    Get tools filtered for the given permission context.

    Simple mode (CLAUDE_CODE_SIMPLE): only Bash, Read, and Edit tools.
    """
    if is_env_truthy(os.environ.get("CLAUDE_CODE_SIMPLE")):
        from hare.tools_impl.BashTool.bash_tool import BashTool
        from hare.tools_impl.FileReadTool.file_read_tool import FileReadTool
        from hare.tools_impl.FileEditTool.file_edit_tool import FileEditTool

        return filter_tools_by_deny_rules(
            [BashTool, FileReadTool, FileEditTool], permission_context
        )

    all_tools = get_all_base_tools()
    allowed = filter_tools_by_deny_rules(all_tools, permission_context)
    return [t for t in allowed if t.is_enabled()]


def assemble_tool_pool(
    permission_context: ToolPermissionContext,
    mcp_tools: list[Tool] | None = None,
) -> list[Tool]:
    """
    Assemble the full tool pool for a given permission context and MCP tools.

    This is the single source of truth for combining built-in tools with MCP tools.
    """
    built_in = get_tools(permission_context)
    if not mcp_tools:
        return sorted(built_in, key=lambda t: t.name)

    allowed_mcp = filter_tools_by_deny_rules(mcp_tools, permission_context)
    # Built-in tools take precedence over MCP tools by name
    built_in_names = {t.name for t in built_in}
    deduped_mcp = [t for t in allowed_mcp if t.name not in built_in_names]

    return sorted(built_in, key=lambda t: t.name) + sorted(
        deduped_mcp, key=lambda t: t.name
    )


def get_merged_tools(
    permission_context: ToolPermissionContext,
    mcp_tools: list[Tool] | None = None,
) -> list[Tool]:
    """Get all tools including both built-in tools and MCP tools."""
    built_in = get_tools(permission_context)
    if not mcp_tools:
        return built_in
    return [*built_in, *mcp_tools]
