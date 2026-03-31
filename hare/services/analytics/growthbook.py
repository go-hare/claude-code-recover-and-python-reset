"""
GrowthBook feature flag integration.

Port of: src/services/analytics/growthbook.ts

Simplified implementation that uses environment variables and local
configuration instead of the GrowthBook SDK.
"""

from __future__ import annotations

import os
from typing import Any, Optional, TypeVar

T = TypeVar("T")

_feature_overrides: dict[str, Any] = {}
_initialized = False


def init_growthbook(attributes: Optional[dict[str, Any]] = None) -> None:
    """Initialize the feature flag system."""
    global _initialized
    _initialized = True


def set_feature_override(key: str, value: Any) -> None:
    """Override a feature flag value (for testing)."""
    _feature_overrides[key] = value


def get_feature_value(key: str, default: Any = None) -> Any:
    """Get a feature flag value (cached, may be stale)."""
    if key in _feature_overrides:
        return _feature_overrides[key]
    env_key = f"GROWTHBOOK_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        if env_val.lower() in ("true", "1"):
            return True
        if env_val.lower() in ("false", "0"):
            return False
        try:
            return int(env_val)
        except ValueError:
            return env_val
    return default


# Alias matching TS naming
get_feature_value_cached_may_be_stale = get_feature_value


def check_feature_gate(key: str) -> bool:
    """Check if a feature gate is enabled."""
    return bool(get_feature_value(key, False))


async def get_dynamic_config(key: str, default: Any = None) -> Any:
    """Get a dynamic config value (blocks on init)."""
    return get_feature_value(key, default)


def reset_growthbook() -> None:
    """Reset the feature flag system."""
    global _initialized
    _feature_overrides.clear()
    _initialized = False
