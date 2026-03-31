"""
Connector text types.

Port of: src/types/connectorText.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorTextBlock:
    type: str = "connector_text"
    text: str = ""
    connector_id: str = ""


def is_connector_text_block(block: Any) -> bool:
    """Check if a block is a connector text block."""
    if isinstance(block, dict):
        return block.get("type") == "connector_text"
    if isinstance(block, ConnectorTextBlock):
        return True
    return False
