"""
MCP configuration loading.

Port of: src/services/mcp/config.ts

Loads MCP server configurations from settings files and environment.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from hare.services.mcp.types import (
    ConfigScope,
    MCPCliState,
    MCPServerConnection,
    McpHttpServerConfig,
    McpServerConfig,
    McpSseServerConfig,
    McpStdioServerConfig,
    ScopedMcpServerConfig,
)


def get_mcp_config(
    settings_dir: Optional[str] = None,
    *,
    project_dir: Optional[str] = None,
) -> MCPCliState:
    """Load MCP configuration from all sources and return the CLI state."""
    state = MCPCliState()
    servers = load_mcp_servers_from_settings(
        settings_dir=settings_dir,
        project_dir=project_dir,
    )
    state.servers = servers
    state.initialized = True
    return state


def load_mcp_servers_from_settings(
    settings_dir: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> list[MCPServerConnection]:
    """Load MCP server definitions from settings files."""
    servers: list[MCPServerConnection] = []

    sources: list[tuple[str, ConfigScope]] = []

    # User-level config
    user_home = os.path.expanduser("~")
    user_config = os.path.join(user_home, ".claude", "settings.json")
    if os.path.isfile(user_config):
        sources.append((user_config, "user"))

    # Project-level config
    if project_dir:
        project_config = os.path.join(project_dir, ".claude", "settings.json")
        if os.path.isfile(project_config):
            sources.append((project_config, "project"))

        local_config = os.path.join(project_dir, ".claude", "settings.local.json")
        if os.path.isfile(local_config):
            sources.append((local_config, "local"))

    for config_path, scope in sources:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mcp_servers = data.get("mcpServers", {})
            for name, config_data in mcp_servers.items():
                config = _parse_server_config(config_data)
                if config:
                    conn = MCPServerConnection(
                        name=name,
                        config=config,
                        scope=scope,
                        enabled=config_data.get("enabled", True) if isinstance(config_data, dict) else True,
                    )
                    servers.append(conn)
        except (json.JSONDecodeError, OSError):
            continue

    return servers


def _parse_server_config(data: Any) -> Optional[McpServerConfig]:
    """Parse a server config dict into a typed config object."""
    if not isinstance(data, dict):
        return None

    transport_type = data.get("type", "stdio")

    if transport_type == "stdio":
        command = data.get("command", "")
        if not command:
            return None
        return McpStdioServerConfig(
            command=command,
            args=data.get("args", []),
            env=data.get("env", {}),
        )
    elif transport_type == "sse":
        url = data.get("url", "")
        if not url:
            return None
        return McpSseServerConfig(
            url=url,
            headers=data.get("headers", {}),
        )
    elif transport_type in ("http", "streamable-http"):
        url = data.get("url", "")
        if not url:
            return None
        return McpHttpServerConfig(
            url=url,
            headers=data.get("headers", {}),
        )
    return None
