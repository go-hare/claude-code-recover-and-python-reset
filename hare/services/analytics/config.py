"""
Analytics configuration.

Port of: src/services/analytics/config.ts
"""

from __future__ import annotations

import os


def is_analytics_enabled() -> bool:
    """Check if analytics is enabled."""
    return os.environ.get("CLAUDE_ANALYTICS_DISABLED", "").lower() not in ("1", "true")


def get_analytics_endpoint() -> str:
    """Get the analytics endpoint URL."""
    return os.environ.get("CLAUDE_ANALYTICS_ENDPOINT", "")
