from __future__ import annotations

from collections.abc import Iterable

from claude_code_py.engine.models import ToolSchema
from claude_code_py.tools.base import Tool


class ToolRegistry:
    """Lookup and filtering helper for tools."""

    def __init__(self, tools: Iterable[Tool]) -> None:
        self._tools: dict[str, Tool] = {}
        self._lookup: dict[str, Tool] = {}
        for tool in tools:
            self._tools[tool.name] = tool
            self._lookup[tool.name] = tool
            for alias in getattr(tool, "aliases", ()):
                self._lookup.setdefault(alias, tool)

    def get(self, name: str) -> Tool | None:
        return self._lookup.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def schemas(self) -> list[ToolSchema]:
        return [self._tools[name].schema() for name in self.names()]

    def subset(
        self,
        *,
        allowed: Iterable[str] | None = None,
        denied: Iterable[str] | None = None,
    ) -> "ToolRegistry":
        allowed_set = None
        if allowed is not None:
            allowed_set = {
                resolved.name if (resolved := self.get(name)) is not None else name
                for name in allowed
            }
        denied_set = {
            resolved.name if (resolved := self.get(name)) is not None else name
            for name in (denied or [])
        }
        tools = []
        for name in self.names():
            if allowed_set is not None and name not in allowed_set:
                continue
            if name in denied_set:
                continue
            tools.append(self._tools[name])
        return ToolRegistry(tools)
