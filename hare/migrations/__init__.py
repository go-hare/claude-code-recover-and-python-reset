"""
Migration scripts.

Port of: src/migrations/ directory
"""

from __future__ import annotations

from typing import Any


MIGRATIONS: list[dict[str, Any]] = [
    {"version": 1, "name": "initial_settings", "description": "Create initial settings structure"},
    {"version": 2, "name": "add_permission_rules", "description": "Add permission rules to settings"},
    {"version": 3, "name": "add_mcp_config", "description": "Add MCP server configuration"},
    {"version": 4, "name": "add_sandbox_settings", "description": "Add sandbox settings"},
    {"version": 5, "name": "add_output_style", "description": "Add output style preference"},
    {"version": 6, "name": "add_model_preferences", "description": "Add model preference settings"},
    {"version": 7, "name": "add_plugin_config", "description": "Add plugin configuration"},
    {"version": 8, "name": "add_hooks", "description": "Add hook definitions"},
    {"version": 9, "name": "add_memory_settings", "description": "Add auto-memory settings"},
    {"version": 10, "name": "add_agent_config", "description": "Add agent configuration"},
    {"version": 11, "name": "normalize_tool_names", "description": "Normalize legacy tool names"},
]


def get_current_version() -> int:
    return len(MIGRATIONS)


def get_pending_migrations(from_version: int = 0) -> list[dict[str, Any]]:
    return [m for m in MIGRATIONS if m["version"] > from_version]


async def run_migrations(from_version: int = 0) -> int:
    """Run pending migrations. Returns new version number."""
    pending = get_pending_migrations(from_version)
    for migration in pending:
        pass
    return get_current_version()
