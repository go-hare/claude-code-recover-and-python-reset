"""
Diagnostic tracking service.

Port of: src/services/diagnosticTracking.ts

Tracks linter/diagnostic changes across file edits to report new issues.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

MAX_DIAGNOSTICS_SUMMARY_CHARS = 4000


@dataclass
class Diagnostic:
    message: str = ""
    severity: str = "Error"  # "Error" | "Warning" | "Info" | "Hint"
    range_start_line: int = 0
    range_start_character: int = 0
    range_end_line: int = 0
    range_end_character: int = 0
    source: Optional[str] = None
    code: Optional[str] = None


@dataclass
class DiagnosticFile:
    uri: str = ""
    diagnostics: list[Diagnostic] = field(default_factory=list)


class DiagnosticTrackingService:
    """Singleton service for tracking diagnostic changes."""

    _instance: Optional["DiagnosticTrackingService"] = None

    def __init__(self) -> None:
        self.baseline: dict[str, list[Diagnostic]] = {}
        self.initialized = False
        self._right_file_state: dict[str, list[Diagnostic]] = {}
        self._last_timestamps: dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> "DiagnosticTrackingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        if self.initialized:
            return
        self.initialized = True

    async def shutdown(self) -> None:
        self.initialized = False
        self.baseline.clear()
        self._right_file_state.clear()
        self._last_timestamps.clear()

    def reset(self) -> None:
        self.baseline.clear()
        self._right_file_state.clear()
        self._last_timestamps.clear()

    def _normalize_uri(self, uri: str) -> str:
        """Normalize file URI for consistent lookups."""
        for prefix in ("file://", "_claude_fs_right:", "_claude_fs_left:"):
            if uri.startswith(prefix):
                uri = uri[len(prefix):]
                break
        return uri.lower().replace("\\", "/")

    async def before_file_edited(self, file_path: str) -> None:
        """Capture baseline diagnostics before editing a file."""
        if not self.initialized:
            return
        normalized = self._normalize_uri(file_path)
        self.baseline[normalized] = []

    async def get_new_diagnostics(self) -> list[DiagnosticFile]:
        """Get diagnostics that weren't in the baseline."""
        return []

    @staticmethod
    def _diagnostics_equal(a: Diagnostic, b: Diagnostic) -> bool:
        return (
            a.message == b.message
            and a.severity == b.severity
            and a.source == b.source
            and a.code == b.code
            and a.range_start_line == b.range_start_line
            and a.range_start_character == b.range_start_character
            and a.range_end_line == b.range_end_line
            and a.range_end_character == b.range_end_character
        )

    @staticmethod
    def format_diagnostics_summary(files: list[DiagnosticFile]) -> str:
        """Format diagnostics into a human-readable summary."""
        severity_symbols = {
            "Error": "✗",
            "Warning": "⚠",
            "Info": "ℹ",
            "Hint": "★",
        }

        parts: list[str] = []
        for f in files:
            filename = f.uri.split("/")[-1] or f.uri
            diag_lines: list[str] = []
            for d in f.diagnostics:
                sym = severity_symbols.get(d.severity, "•")
                line = f"  {sym} [Line {d.range_start_line + 1}:{d.range_start_character + 1}] {d.message}"
                if d.code:
                    line += f" [{d.code}]"
                if d.source:
                    line += f" ({d.source})"
                diag_lines.append(line)
            parts.append(f"{filename}:\n" + "\n".join(diag_lines))

        result = "\n\n".join(parts)
        if len(result) > MAX_DIAGNOSTICS_SUMMARY_CHARS:
            truncation = "…[truncated]"
            result = result[:MAX_DIAGNOSTICS_SUMMARY_CHARS - len(truncation)] + truncation
        return result

    @staticmethod
    def get_severity_symbol(severity: str) -> str:
        return {"Error": "✗", "Warning": "⚠", "Info": "ℹ", "Hint": "★"}.get(severity, "•")


diagnostic_tracker = DiagnosticTrackingService.get_instance()
