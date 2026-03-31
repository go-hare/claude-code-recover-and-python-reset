"""
Message grouping for compaction.

Port of: src/services/compact/grouping.ts
"""

from __future__ import annotations

from typing import Any


def group_messages_by_api_round(
    messages: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Group messages into API request/response rounds."""
    groups: list[list[dict[str, Any]]] = []
    current_group: list[dict[str, Any]] = []

    for msg in messages:
        msg_type = msg.get("type", "")
        if msg_type == "user" and current_group:
            groups.append(current_group)
            current_group = []
        current_group.append(msg)

    if current_group:
        groups.append(current_group)

    return groups
