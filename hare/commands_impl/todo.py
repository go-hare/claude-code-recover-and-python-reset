"""Port of: src/commands/todo.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "todo"
DESCRIPTION = "Manage a task/todo list for the session"
ALIASES = ["tasks"]

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    return {"type": "todo", "display_text": "Todo management - pass instructions to the model to manage tasks."}
