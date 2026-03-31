"""
Process user input.

Port of: src/utils/processUserInput/processUserInput.ts

Entry point for processing all user input: text prompts, slash commands,
file attachments, image pastes, etc.
"""

from __future__ import annotations

from typing import Any, Optional

from hare.utils.process_user_input.process_text_prompt import process_text_prompt


async def process_user_input(
    *,
    input_text: str | list[dict[str, Any]],
    mode: str = "prompt",
    messages: list[dict[str, Any]] | None = None,
    context: Any = None,
    skip_slash_commands: bool = False,
) -> dict[str, Any]:
    """
    Process user input and return messages + flags.

    Returns:
        dict with 'messages', 'should_query', 'allowed_tools',
        'model', 'effort', 'result_text', 'next_input'
    """
    input_str = input_text if isinstance(input_text, str) else ""

    # Check for slash commands
    if input_str.startswith("/") and not skip_slash_commands:
        return await _process_slash_command(input_str, messages=messages, context=context)

    return await process_text_prompt(
        input_text=input_str,
        mode=mode,
        messages=messages,
        context=context,
    )


async def _process_slash_command(
    input_str: str,
    *,
    messages: list[dict[str, Any]] | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """Process a slash command."""
    parts = input_str.split(maxsplit=1)
    command = parts[0][1:]
    args = parts[1] if len(parts) > 1 else ""

    from hare.commands_impl import find_command
    cmd = find_command(command)
    if cmd:
        try:
            result = await cmd["call"](args, messages or [], **(context or {}))
            return {
                "messages": [],
                "should_query": False,
                "result_text": result.get("display_text", ""),
            }
        except Exception as e:
            return {
                "messages": [],
                "should_query": False,
                "result_text": f"Error: {e}",
            }

    return {
        "messages": [_create_user_message(input_str)],
        "should_query": True,
    }


def _create_user_message(text: str) -> dict[str, Any]:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": text,
        },
    }
