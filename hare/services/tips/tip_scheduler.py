"""
Tip scheduler - determines when and which tips to show.

Port of: src/services/tips/tipScheduler.ts
"""

from __future__ import annotations

from typing import Optional

from hare.services.tips.tip_history import TipHistory
from hare.services.tips.tip_registry import Tip, TipRegistry, get_tip_registry


class TipScheduler:
    def __init__(
        self,
        registry: Optional[TipRegistry] = None,
        history: Optional[TipHistory] = None,
    ) -> None:
        self._registry = registry or get_tip_registry()
        self._history = history or TipHistory()
        self._turn_count = 0

    def on_turn(self) -> None:
        self._turn_count += 1

    def get_next_tip(self) -> Optional[Tip]:
        """Get the next tip to show, if any."""
        if self._turn_count < 3:
            return None

        for tip in self._registry.get_all():
            if tip.show_once and self._history.has_shown(tip.id):
                continue
            self._history.mark_shown(tip.id)
            return tip
        return None
