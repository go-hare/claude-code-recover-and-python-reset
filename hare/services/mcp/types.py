"""
MCP service types.

Port of: src/services/mcp/types.ts

Defines configuration schemas and types for MCP (Model Context Protocol) servers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

ConfigScope = Literal["local", "user", "project", "dynamic", "enterprise", "claudeai", "managed"]
Transport = Literal["stdio", "sse", "sse-ide", "http", "ws", "sdk"]


@dataclass
class McpStdioServerConfig:
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    type: str = "stdio"


@dataclass
class McpSseServerConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    type: str = "sse"


@dataclass
class McpHttpServerConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    type: str = "http"


McpServerConfig = McpStdioServerConfig | McpSseServerConfig | McpHttpServerConfig


@dataclass
class ScopedMcpServerConfig:
    scope: ConfigScope
    config: McpServerConfig
    enabled: bool = True


@dataclass
class MCPServerConnection:
    name: str
    config: McpServerConfig
    scope: ConfigScope = "user"
    enabled: bool = True
    connected: bool = False
    error: Optional[str] = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ServerResource:
    uri: str
    name: str
    description: str = ""
    mime_type: str = ""


@dataclass
class MCPCliState:
    servers: list[MCPServerConnection] = field(default_factory=list)
    initialized: bool = False

    def get_server(self, name: str) -> Optional[MCPServerConnection]:
        for s in self.servers:
            if s.name == name:
                return s
        return None

    def get_enabled_servers(self) -> list[MCPServerConnection]:
        return [s for s in self.servers if s.enabled]

    def get_connected_servers(self) -> list[MCPServerConnection]:
        return [s for s in self.servers if s.connected]


@dataclass
class SerializedTool:
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    server_name: str = ""


@dataclass
class MCPProgress:
    type: str = ""
    server_name: str = ""
    tool_name: str = ""
    progress: float = 0.0
    total: float = 0.0
    message: str = ""
