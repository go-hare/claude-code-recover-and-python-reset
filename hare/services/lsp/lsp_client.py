"""
LSP client for Language Server Protocol operations.

Port of: src/services/lsp/LSPClient.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LSPClient:
    """Client for communicating with LSP servers."""
    server_name: str
    language: str = ""
    connected: bool = False

    async def connect(self) -> bool:
        """Connect to the LSP server."""
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from the LSP server."""
        self.connected = False

    async def get_definition(self, file: str, line: int, col: int) -> Optional[dict[str, Any]]:
        """Get definition at position."""
        return None

    async def get_references(self, file: str, line: int, col: int) -> list[dict[str, Any]]:
        """Get references at position."""
        return []

    async def get_hover(self, file: str, line: int, col: int) -> Optional[str]:
        """Get hover info at position."""
        return None

    async def get_diagnostics(self, file: str) -> list[dict[str, Any]]:
        """Get diagnostics for a file."""
        return []

    async def get_completions(self, file: str, line: int, col: int) -> list[dict[str, Any]]:
        """Get completions at position."""
        return []
