"""
API logging and usage types.

Port of: src/services/api/logging.ts, emptyUsage.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NonNullableUsage:
    """Non-nullable usage tracking."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    server_tool_use_input_tokens: int = 0


def empty_usage() -> NonNullableUsage:
    """Create an empty usage object."""
    return NonNullableUsage()


def accumulate_usage(
    target: NonNullableUsage,
    source: NonNullableUsage,
) -> NonNullableUsage:
    """Accumulate usage from source into target."""
    target.input_tokens += source.input_tokens
    target.output_tokens += source.output_tokens
    target.cache_creation_input_tokens += source.cache_creation_input_tokens
    target.cache_read_input_tokens += source.cache_read_input_tokens
    target.server_tool_use_input_tokens += source.server_tool_use_input_tokens
    return target


def update_usage(
    target: NonNullableUsage,
    source: NonNullableUsage,
) -> NonNullableUsage:
    """Update usage (alias for accumulate_usage for compatibility)."""
    return accumulate_usage(target, source)


EMPTY_USAGE = NonNullableUsage()
