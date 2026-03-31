"""
Tip history - tracks which tips have been shown.

Port of: src/services/tips/tipHistory.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TipHistory:
    _shown: set[str] = field(default_factory=set)
    _file_path: str = ""

    def __post_init__(self) -> None:
        if not self._file_path:
            self._file_path = os.path.join(
                os.path.expanduser("~"), ".claude", "tip_history.json",
            )
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r") as f:
                    data = json.load(f)
                self._shown = set(data.get("shown", []))
            except Exception:
                pass

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        try:
            with open(self._file_path, "w") as f:
                json.dump({"shown": sorted(self._shown)}, f)
        except Exception:
            pass

    def has_shown(self, tip_id: str) -> bool:
        return tip_id in self._shown

    def mark_shown(self, tip_id: str) -> None:
        self._shown.add(tip_id)
        self._save()

    def reset(self) -> None:
        self._shown.clear()
        self._save()
