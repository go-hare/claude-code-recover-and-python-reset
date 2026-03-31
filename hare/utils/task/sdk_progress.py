"""
SDK progress reporting.

Port of: src/utils/task/sdkProgress.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ProgressUpdate:
    phase: str = ""
    message: str = ""
    percentage: float = 0.0
    metadata: dict[str, Any] | None = None


ProgressCallback = Callable[[ProgressUpdate], None]


class ProgressReporter:
    def __init__(self, callback: Optional[ProgressCallback] = None) -> None:
        self._callback = callback

    def report(self, update: ProgressUpdate) -> None:
        if self._callback:
            self._callback(update)

    def set_phase(self, phase: str, message: str = "") -> None:
        self.report(ProgressUpdate(phase=phase, message=message))

    def set_percentage(self, pct: float) -> None:
        self.report(ProgressUpdate(percentage=pct))
