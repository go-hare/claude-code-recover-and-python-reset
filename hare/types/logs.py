"""
Log types.

Port of: src/types/logs.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

LogLevel = Literal["debug", "info", "warn", "error"]


@dataclass
class LogEntry:
    level: LogLevel
    message: str
    timestamp: float = 0.0
    source: str = ""
    metadata: dict[str, Any] | None = None
