"""
API usage tracking.

Port of: src/services/api/usage.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UsageSnapshot:
    """A snapshot of API usage at a point in time."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    total_cost_usd: float = 0.0


_usage_history: list[UsageSnapshot] = []


def record_usage_snapshot(snapshot: UsageSnapshot) -> None:
    """Record a usage snapshot."""
    _usage_history.append(snapshot)


def get_usage_history() -> list[UsageSnapshot]:
    """Get all recorded usage snapshots."""
    return list(_usage_history)


def clear_usage_history() -> None:
    """Clear usage history."""
    _usage_history.clear()
