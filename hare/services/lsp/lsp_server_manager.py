"""
LSP server manager.

Port of: src/services/lsp/LSPServerManager.ts + manager.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from hare.services.lsp.lsp_client import LSPClient


@dataclass
class LSPServerManager:
    """Manages LSP server instances."""
    _clients: dict[str, LSPClient] = field(default_factory=dict)

    async def get_client(self, server_name: str) -> Optional[LSPClient]:
        """Get or create a client for a server."""
        if server_name in self._clients:
            return self._clients[server_name]
        return None

    async def start_server(self, server_name: str, config: dict[str, Any]) -> LSPClient:
        """Start an LSP server and create a client."""
        client = LSPClient(server_name=server_name, language=config.get("language", ""))
        await client.connect()
        self._clients[server_name] = client
        return client

    async def stop_server(self, server_name: str) -> None:
        """Stop an LSP server."""
        client = self._clients.pop(server_name, None)
        if client:
            await client.disconnect()

    async def stop_all(self) -> None:
        """Stop all LSP servers."""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()

    def list_servers(self) -> list[str]:
        """List all running server names."""
        return list(self._clients.keys())
