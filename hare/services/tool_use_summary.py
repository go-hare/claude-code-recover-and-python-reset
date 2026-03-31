"""
Tool use summary generation.

Port of: src/services/toolUseSummary/toolUseSummaryGenerator.ts
"""

from __future__ import annotations

from typing import Any


def generate_tool_use_summary(
    tool_uses: list[dict[str, Any]],
) -> str:
    """Generate a human-readable summary of tool uses in a turn."""
    if not tool_uses:
        return "No tools used."

    lines = []
    for use in tool_uses:
        name = use.get("name", "unknown")
        status = use.get("status", "")
        if status == "error":
            lines.append(f"- {name}: failed")
        else:
            lines.append(f"- {name}: completed")

    return "Tool usage:\n" + "\n".join(lines)


def summarize_tool_results(
    messages: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Extract tool use summaries from messages."""
    summaries = []
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                summaries.append({
                    "tool": block.get("name", ""),
                    "id": block.get("id", ""),
                })
    return summaries
