"""
Analytics event logger.

Port of: src/services/analytics/index.ts

Queue-based event logging with pluggable sinks.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

_event_queue: list[dict[str, Any]] = []
_sink: Optional[dict[str, Callable[..., Any]]] = None


def attach_analytics_sink(sink: dict[str, Callable[..., Any]]) -> None:
    """Attach the analytics sink (called during app startup)."""
    global _sink
    if _sink is not None:
        return
    _sink = sink
    for event in _event_queue:
        _sink["log_event"](event["event_name"], event["metadata"])
    _event_queue.clear()


def log_event(event_name: str, metadata: Optional[dict[str, Any]] = None) -> None:
    """Log an analytics event."""
    meta = metadata or {}
    if _sink:
        _sink["log_event"](event_name, meta)
    else:
        _event_queue.append({"event_name": event_name, "metadata": meta})


async def log_event_async(event_name: str, metadata: Optional[dict[str, Any]] = None) -> None:
    """Log an analytics event (async variant)."""
    meta = metadata or {}
    if _sink and "log_event_async" in _sink:
        await _sink["log_event_async"](event_name, meta)
    else:
        log_event(event_name, meta)


def strip_proto_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """Strip _PROTO_* keys from metadata for general-access storage."""
    result = None
    for key in metadata:
        if key.startswith("_PROTO_"):
            if result is None:
                result = dict(metadata)
            del result[key]
    return result if result is not None else metadata
