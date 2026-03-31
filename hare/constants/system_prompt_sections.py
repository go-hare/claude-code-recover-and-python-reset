"""
System prompt section management.

Port of: src/constants/systemPromptSections.ts

Memoized system prompt sections that are computed once and cached
until /clear or /compact.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional, Union

ComputeFn = Callable[[], Union[Optional[str], Awaitable[Optional[str]]]]

_cache: dict[str, Optional[str]] = {}


class SystemPromptSection:
    def __init__(self, name: str, compute: ComputeFn, cache_break: bool = False) -> None:
        self.name = name
        self.compute = compute
        self.cache_break = cache_break


def system_prompt_section(name: str, compute: ComputeFn) -> SystemPromptSection:
    """Create a memoized system prompt section."""
    return SystemPromptSection(name, compute, cache_break=False)


def dangerous_uncached_system_prompt_section(
    name: str,
    compute: ComputeFn,
    reason: str = "",
) -> SystemPromptSection:
    """Create a volatile section that recomputes every turn (breaks prompt cache)."""
    return SystemPromptSection(name, compute, cache_break=True)


async def resolve_system_prompt_sections(
    sections: list[SystemPromptSection],
) -> list[Optional[str]]:
    """Resolve all system prompt sections."""
    import asyncio
    import inspect

    results: list[Optional[str]] = []
    for section in sections:
        if not section.cache_break and section.name in _cache:
            results.append(_cache.get(section.name))
            continue
        value = section.compute()
        if inspect.isawaitable(value):
            value = await value
        _cache[section.name] = value
        results.append(value)
    return results


def clear_system_prompt_sections() -> None:
    """Clear all cached prompt sections."""
    _cache.clear()
