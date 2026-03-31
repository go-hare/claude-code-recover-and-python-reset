"""
LSP Diagnostic Registry.

Port of: src/services/lsp/LSPDiagnosticRegistry.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Diagnostic:
    file: str
    line: int
    col: int
    message: str
    severity: str = "error"
    source: str = ""


@dataclass
class LSPDiagnosticRegistry:
    """Registry for collecting and querying LSP diagnostics."""
    _diagnostics: dict[str, list[Diagnostic]] = field(default_factory=dict)

    def set_diagnostics(self, file: str, diagnostics: list[Diagnostic]) -> None:
        self._diagnostics[file] = diagnostics

    def get_diagnostics(self, file: str) -> list[Diagnostic]:
        return self._diagnostics.get(file, [])

    def get_all_diagnostics(self) -> dict[str, list[Diagnostic]]:
        return dict(self._diagnostics)

    def clear(self, file: str = "") -> None:
        if file:
            self._diagnostics.pop(file, None)
        else:
            self._diagnostics.clear()

    def get_error_count(self) -> int:
        return sum(
            1 for diags in self._diagnostics.values()
            for d in diags if d.severity == "error"
        )
