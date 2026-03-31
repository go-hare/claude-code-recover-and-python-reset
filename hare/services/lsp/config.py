"""
LSP configuration.

Port of: src/services/lsp/config.ts
"""

from __future__ import annotations

from typing import Any, Optional


def get_lsp_config() -> dict[str, Any]:
    """Get LSP server configuration from settings."""
    return {
        "servers": [],
        "enabled": False,
    }
