"""
Process text prompt.

Port of: src/utils/processUserInput/processTextPrompt.ts
"""

from __future__ import annotations

from typing import Any, Optional


async def process_text_prompt(
    *,
    input_text: str,
    mode: str = "prompt",
    messages: list[dict[str, Any]] | None = None,
    context: Any = None,
) -> dict[str, Any]:
    """Process a plain text prompt into messages."""
    user_message = {
        "type": "user",
        "message": {
            "role": "user",
            "content": input_text,
        },
    }
    return {
        "messages": [user_message],
        "should_query": True,
    }
