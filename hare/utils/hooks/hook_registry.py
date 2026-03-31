"""
Async hook registry.

Port of: src/utils/hooks/AsyncHookRegistry.ts

Manages hook subscriptions and execution for tool lifecycle events.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from hare.utils.hooks.hook_events import HookEvent
from hare.utils.debug import log_for_debugging


@dataclass
class HookHandler:
    """A registered hook handler."""
    event: HookEvent
    name: str
    handler: Callable[..., Any]
    source: str = ""  # "settings" | "skill" | "frontmatter"


class AsyncHookRegistry:
    """Registry for async hooks."""

    def __init__(self) -> None:
        self._handlers: dict[HookEvent, list[HookHandler]] = {}

    def register(
        self,
        event: HookEvent,
        name: str,
        handler: Callable[..., Any],
        source: str = "",
    ) -> None:
        """Register a hook handler for an event."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(
            HookHandler(event=event, name=name, handler=handler, source=source)
        )

    def unregister(self, event: HookEvent, name: str) -> None:
        """Unregister a hook handler by name."""
        if event in self._handlers:
            self._handlers[event] = [
                h for h in self._handlers[event] if h.name != name
            ]

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()

    async def emit(
        self,
        event: HookEvent,
        context: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Emit an event and run all registered handlers.
        Returns list of results from handlers.
        """
        handlers = self._handlers.get(event, [])
        if not handlers:
            return []

        results: list[dict[str, Any]] = []
        for handler in handlers:
            try:
                result = handler.handler(context or {})
                if asyncio.iscoroutine(result):
                    result = await result
                if result is not None:
                    results.append({"name": handler.name, "result": result})
            except Exception as e:
                log_for_debugging(f"Hook {handler.name} failed: {e}")
                results.append({"name": handler.name, "error": str(e)})

        return results

    def get_handlers(self, event: HookEvent) -> list[HookHandler]:
        """Get all handlers for an event."""
        return list(self._handlers.get(event, []))

    def has_handlers(self, event: HookEvent) -> bool:
        """Check if an event has any handlers."""
        return bool(self._handlers.get(event))


_registry: Optional[AsyncHookRegistry] = None


def get_hook_registry() -> AsyncHookRegistry:
    """Get the global hook registry singleton."""
    global _registry
    if _registry is None:
        _registry = AsyncHookRegistry()
    return _registry
