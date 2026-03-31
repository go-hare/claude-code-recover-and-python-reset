"""
Tip registry - collection of tips to show users.

Port of: src/services/tips/tipRegistry.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tip:
    id: str
    text: str
    category: str = "general"
    priority: int = 0
    show_once: bool = False


@dataclass
class TipRegistry:
    _tips: dict[str, Tip] = field(default_factory=dict)

    def register(self, tip: Tip) -> None:
        self._tips[tip.id] = tip

    def get(self, tip_id: str) -> Optional[Tip]:
        return self._tips.get(tip_id)

    def get_all(self) -> list[Tip]:
        return sorted(self._tips.values(), key=lambda t: -t.priority)

    def get_by_category(self, category: str) -> list[Tip]:
        return [t for t in self._tips.values() if t.category == category]


_global_registry = TipRegistry()


def get_tip_registry() -> TipRegistry:
    return _global_registry
