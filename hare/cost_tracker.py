"""
Cost and usage tracking.

Port of: src/services/api/usage.ts + cost tracking logic

Tracks API call durations, token usage, and estimated costs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from hare.services.api.logging import NonNullableUsage

# Approximate pricing per 1M tokens (as of 2025)
_PRICING: dict[str, dict[str, float]] = {
    "opus": {"input": 15.0, "output": 75.0},
    "sonnet": {"input": 3.0, "output": 15.0},
    "haiku": {"input": 0.25, "output": 1.25},
}


@dataclass
class CostTracker:
    """Tracks costs for the current session."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_creation_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_api_duration: float = 0.0
    total_cost_usd: float = 0.0
    request_count: int = 0


_tracker = CostTracker()


def add_usage(usage: NonNullableUsage) -> None:
    """Record token usage from an API call."""
    _tracker.total_input_tokens += usage.input_tokens
    _tracker.total_output_tokens += usage.output_tokens
    _tracker.total_cache_creation_tokens += usage.cache_creation_input_tokens
    _tracker.total_cache_read_tokens += usage.cache_read_input_tokens
    _tracker.request_count += 1

    # Estimate cost (default to sonnet pricing)
    pricing = _PRICING["sonnet"]
    input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
    output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
    _tracker.total_cost_usd += input_cost + output_cost


def add_api_duration(duration: float) -> None:
    """Record API call duration."""
    _tracker.total_api_duration += duration


def get_cost_summary() -> dict[str, Any]:
    """Get a summary of costs."""
    return {
        "input_tokens": _tracker.total_input_tokens,
        "output_tokens": _tracker.total_output_tokens,
        "cache_creation_tokens": _tracker.total_cache_creation_tokens,
        "cache_read_tokens": _tracker.total_cache_read_tokens,
        "total_cost_usd": round(_tracker.total_cost_usd, 4),
        "total_api_duration": round(_tracker.total_api_duration, 2),
        "request_count": _tracker.request_count,
    }


def get_model_usage() -> dict[str, int]:
    """Get model usage summary."""
    return {
        "input_tokens": _tracker.total_input_tokens,
        "output_tokens": _tracker.total_output_tokens,
    }


def get_total_api_duration() -> float:
    """Get total API call duration."""
    return _tracker.total_api_duration


def get_total_cost() -> float:
    """Get total estimated cost in USD."""
    return _tracker.total_cost_usd


def reset_cost_tracker() -> None:
    """Reset cost tracking for a new session."""
    global _tracker
    _tracker = CostTracker()
