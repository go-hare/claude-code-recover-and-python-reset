from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MCPServer:
    name: str
    transport: str


class MCPClientManager:
    """Placeholder for future MCP integration."""

    def list_servers(self) -> list[MCPServer]:
        return []
