"""
Authentication utilities.

Port of: src/utils/auth.ts

Handles API key management and subscription type detection.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

SubscriptionType = Literal["free", "pro", "max", "team_standard", "team_premium", "enterprise"]


def get_api_key() -> Optional[str]:
    """Get the Anthropic API key from environment."""
    return os.environ.get("ANTHROPIC_API_KEY")


def has_api_key() -> bool:
    """Check if an API key is available."""
    return bool(get_api_key())


def get_subscription_type() -> Optional[SubscriptionType]:
    """Get the current subscription type. Returns None if unknown."""
    return None


def is_claude_ai_subscriber() -> bool:
    return False


def is_max_subscriber() -> bool:
    return False


def is_pro_subscriber() -> bool:
    return False


def is_team_premium_subscriber() -> bool:
    return False
