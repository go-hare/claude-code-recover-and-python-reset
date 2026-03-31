"""
Analytics sink - routes events to backends.

Port of: src/services/analytics/sink.ts
"""

from __future__ import annotations

from typing import Any

from hare.services.analytics.event_logger import strip_proto_fields


def create_analytics_sink(
    *,
    endpoint: str = "",
    enabled: bool = True,
) -> dict[str, Any]:
    """Create an analytics sink."""
    def log_event(event_name: str, metadata: dict[str, Any]) -> None:
        if not enabled:
            return
        clean = strip_proto_fields(metadata)
        # In production, send to Datadog / 1P endpoint
        pass

    async def log_event_async(event_name: str, metadata: dict[str, Any]) -> None:
        log_event(event_name, metadata)

    return {
        "log_event": log_event,
        "log_event_async": log_event_async,
    }
