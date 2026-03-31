"""
Tool implementations registry.

Port of: src/tools/

Provides access to all tool implementations.
"""

from __future__ import annotations

from typing import Any


def get_all_tool_modules() -> dict[str, Any]:
    """Get a mapping of tool name -> module for all tool implementations."""
    from hare.tools_impl.BashTool import prompt as bash_prompt
    from hare.tools_impl.MCPTool import mcp_tool
    from hare.tools_impl.NotebookEditTool import notebook_edit_tool
    from hare.tools_impl.PowerShellTool import powershell_tool
    from hare.tools_impl.AskUserQuestionTool import ask_user_question_tool
    from hare.tools_impl.TaskTools import (
        task_create_tool, task_list_tool, task_get_tool,
        task_stop_tool, task_update_tool,
    )
    from hare.tools_impl.PlanModeTool import enter_plan_mode_tool, exit_plan_mode_tool
    from hare.tools_impl.ConfigTool import config_tool
    from hare.tools_impl.SkillTool import skill_tool
    from hare.tools_impl.SendMessageTool import send_message_tool
    from hare.tools_impl.BriefTool import brief_tool
    from hare.tools_impl.WorktreeTool import enter_worktree_tool, exit_worktree_tool
    from hare.tools_impl.SleepTool import sleep_tool
    from hare.tools_impl.ToolSearchTool import tool_search_tool
    from hare.tools_impl.ListMcpResourcesTool import list_mcp_resources_tool
    from hare.tools_impl.ReadMcpResourceTool import read_mcp_resource_tool
    from hare.tools_impl.LSPTool import lsp_tool

    return {
        "Bash": bash_prompt,
        "MCPTool": mcp_tool,
        "NotebookEdit": notebook_edit_tool,
        "PowerShell": powershell_tool,
        "AskUserQuestion": ask_user_question_tool,
        "TaskCreate": task_create_tool,
        "TaskList": task_list_tool,
        "TaskGet": task_get_tool,
        "TaskStop": task_stop_tool,
        "TaskUpdate": task_update_tool,
        "EnterPlanMode": enter_plan_mode_tool,
        "ExitPlanMode": exit_plan_mode_tool,
        "Config": config_tool,
        "Skill": skill_tool,
        "SendMessage": send_message_tool,
        "Brief": brief_tool,
        "EnterWorktree": enter_worktree_tool,
        "ExitWorktree": exit_worktree_tool,
        "Sleep": sleep_tool,
        "ToolSearch": tool_search_tool,
        "ListMcpResources": list_mcp_resources_tool,
        "ReadMcpResource": read_mcp_resource_tool,
        "LSP": lsp_tool,
    }
