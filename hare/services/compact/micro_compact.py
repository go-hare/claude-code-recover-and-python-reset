"""
Micro-compact - lightweight compaction of tool results.

Port of: src/services/compact/microCompact.ts

Reduces token usage by truncating large tool results (file reads,
grep output, etc.) in older messages that are unlikely to be referenced.
"""

from __future__ import annotations

from typing import Any

from hare.services.token_estimation import estimate_tokens

TIME_BASED_MC_CLEARED_MESSAGE = "[Old tool result content cleared]"
IMAGE_MAX_TOKEN_SIZE = 2000

COMPACTABLE_TOOLS = frozenset({
    "FileRead", "Bash", "PowerShell",
    "Grep", "Glob", "WebSearch", "WebFetch",
    "FileEdit", "FileWrite",
})


async def microcompact_messages(
    messages: list[dict[str, Any]],
    context: Any = None,
    *,
    threshold_tokens: int = 1000,
) -> dict[str, Any]:
    """
    Apply micro-compaction to messages by truncating large tool results.

    Returns dict with 'messages' and 'tokens_saved'.
    """
    new_messages = []
    tokens_saved = 0

    for i, msg in enumerate(messages):
        # Only compact older messages (keep last few intact)
        if i >= len(messages) - 4:
            new_messages.append(msg)
            continue

        if msg.get("type") != "user":
            new_messages.append(msg)
            continue

        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            new_messages.append(msg)
            continue

        new_content = []
        modified = False
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                new_content.append(block)
                continue

            result_content = block.get("content", "")
            if isinstance(result_content, str):
                token_count = estimate_tokens(result_content)
                if token_count > threshold_tokens:
                    truncated = result_content[:500] + f"\n\n[... truncated {token_count} tokens ...]"
                    new_content.append({**block, "content": truncated})
                    tokens_saved += token_count - estimate_tokens(truncated)
                    modified = True
                else:
                    new_content.append(block)
            else:
                new_content.append(block)

        if modified:
            new_msg = {**msg, "message": {**msg["message"], "content": new_content}}
            new_messages.append(new_msg)
        else:
            new_messages.append(msg)

    return {"messages": new_messages, "tokens_saved": tokens_saved}


def estimate_message_tokens(messages: list[dict[str, Any]]) -> int:
    """Estimate total token count for messages."""
    total = 0
    for msg in messages:
        if msg.get("type") not in ("user", "assistant"):
            continue
        content = msg.get("message", {}).get("content", [])
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        total += estimate_tokens(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        rc = block.get("content", "")
                        if isinstance(rc, str):
                            total += estimate_tokens(rc)
                    elif block.get("type") in ("image", "document"):
                        total += IMAGE_MAX_TOKEN_SIZE
                    elif block.get("type") == "thinking":
                        total += estimate_tokens(block.get("thinking", ""))
                    elif block.get("type") == "tool_use":
                        total += estimate_tokens(str(block.get("input", {})))
    return total
