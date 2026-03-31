"""
TodoWriteTool – manage a structured task list.

Port of: src/tools/TodoWriteTool/TodoWriteTool.ts
"""

from __future__ import annotations

from typing import Any, Optional

from hare.tool import ToolBase, ToolResult, ToolUseContext
from hare.types.permissions import PermissionAllowDecision, PermissionResult

TODO_WRITE_TOOL_NAME = "TodoWrite"


# Global todo state
_todos: list[dict[str, Any]] = []


class _TodoWriteTool(ToolBase):
    name = TODO_WRITE_TOOL_NAME
    aliases = ["todo", "todos"]
    search_hint = "manage a structured task list"
    max_result_size_chars = 100_000

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed", "cancelled"],
                            },
                        },
                        "required": ["id", "content", "status"],
                    },
                    "description": "Array of TODO items to update or create.",
                },
                "merge": {
                    "type": "boolean",
                    "description": (
                        "Whether to merge with existing todos. "
                        "If false, replaces all existing todos."
                    ),
                },
            },
            "required": ["todos"],
        }

    def is_read_only(self, input: dict[str, Any]) -> bool:
        return False

    async def prompt(self, options: dict[str, Any]) -> str:
        return "Create and manage a structured task list for your current coding session."

    async def description(self, input: dict[str, Any], options: dict[str, Any]) -> str:
        return "Update TODO list"

    def user_facing_name(self, input: Optional[dict[str, Any]] = None) -> str:
        return TODO_WRITE_TOOL_NAME

    async def call(
        self,
        args: dict[str, Any],
        context: ToolUseContext,
        can_use_tool: Any = None,
        parent_message: Any = None,
        on_progress: Any = None,
    ) -> ToolResult:
        """Update the TODO list."""
        global _todos

        new_todos = args.get("todos", [])
        merge = args.get("merge", False)

        if merge:
            existing_by_id = {t["id"]: t for t in _todos}
            for item in new_todos:
                todo_id = item.get("id", "")
                if todo_id in existing_by_id:
                    existing = existing_by_id[todo_id]
                    if "content" in item:
                        existing["content"] = item["content"]
                    if "status" in item:
                        existing["status"] = item["status"]
                else:
                    existing_by_id[todo_id] = item
            _todos = list(existing_by_id.values())
        else:
            _todos = list(new_todos)

        # Build summary
        lines = ["Successfully updated TODOs.\n"]
        for t in _todos:
            status = t.get("status", "pending").upper()
            content = t.get("content", "")
            todo_id = t.get("id", "")
            lines.append(f"- **{status}**: {content} (id: {todo_id})")

        return ToolResult(data="\n".join(lines))


def get_todos() -> list[dict[str, Any]]:
    """Get the current TODO list."""
    return list(_todos)


TodoWriteTool = _TodoWriteTool()
