"""
Ask User Question Tool - ask the user a question and wait for response.

Port of: src/tools/AskUserQuestionTool/AskUserQuestionTool.tsx
"""

from __future__ import annotations

from typing import Any

TOOL_NAME = "AskUserQuestion"
DESCRIPTION = "Ask the user a question and wait for their response"
PROMPT = """Use this tool to ask the user a question and wait for their response.
Use this when you need clarification or a decision from the user before proceeding."""


def input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask the user",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of choices for the user",
            },
        },
        "required": ["question"],
    }


async def call(
    question: str,
    options: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Ask user a question via CLI input."""
    print(f"\n[Question] {question}")
    if options:
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
    try:
        answer = input("> ")
    except (EOFError, KeyboardInterrupt):
        answer = ""
    return {"answer": answer}
