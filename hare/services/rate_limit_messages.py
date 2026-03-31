"""
Rate limit message generation.

Port of: src/services/rateLimitMessages.ts
"""

from __future__ import annotations

from typing import Any, Literal, Optional

RATE_LIMIT_ERROR_PREFIXES = (
    "You've hit your",
    "You've used",
    "You're now using extra usage",
    "You're close to",
    "You're out of extra usage",
)


def is_rate_limit_error_message(text: str) -> bool:
    """Check if a message is a rate limit error."""
    return any(text.startswith(prefix) for prefix in RATE_LIMIT_ERROR_PREFIXES)


def get_rate_limit_message(
    limits: dict[str, Any],
    model: str,
) -> Optional[dict[str, Any]]:
    """
    Get rate limit message based on limit state.
    Returns None if no message should be shown.
    """
    if limits.get("isUsingOverage"):
        if limits.get("overageStatus") == "allowed_warning":
            return {
                "message": "You're close to your extra usage spending limit",
                "severity": "warning",
            }
        return None

    if limits.get("status") == "rejected":
        return {
            "message": _get_limit_reached_text(limits, model),
            "severity": "error",
        }

    if limits.get("status") == "allowed_warning":
        utilization = limits.get("utilization")
        if utilization is not None and utilization < 0.7:
            return None
        text = _get_early_warning_text(limits)
        if text:
            return {"message": text, "severity": "warning"}

    return None


def _get_limit_reached_text(limits: dict[str, Any], model: str) -> str:
    """Get error text for rate limit reached."""
    reset_time = limits.get("resetsAt", "")
    reset_msg = f" · resets {reset_time}" if reset_time else ""

    rate_type = limits.get("rateLimitType", "")

    if rate_type == "seven_day_sonnet":
        return f"You've hit your Sonnet limit{reset_msg}"
    if rate_type == "seven_day_opus":
        return f"You've hit your Opus limit{reset_msg}"
    if rate_type == "seven_day":
        return f"You've hit your weekly limit{reset_msg}"
    if rate_type == "five_hour":
        return f"You've hit your session limit{reset_msg}"

    return f"You've hit your usage limit{reset_msg}"


def _get_early_warning_text(limits: dict[str, Any]) -> Optional[str]:
    """Get warning text for approaching limits."""
    rate_type = limits.get("rateLimitType", "")

    limit_names = {
        "seven_day": "weekly limit",
        "five_hour": "session limit",
        "seven_day_opus": "Opus limit",
        "seven_day_sonnet": "Sonnet limit",
        "overage": "extra usage",
    }

    limit_name = limit_names.get(rate_type)
    if not limit_name:
        return None

    utilization = limits.get("utilization")
    used = int(utilization * 100) if utilization else None
    reset_time = limits.get("resetsAt")

    if used and reset_time:
        return f"You've used {used}% of your {limit_name} · resets {reset_time}"
    if used:
        return f"You've used {used}% of your {limit_name}"
    if reset_time:
        return f"Approaching {limit_name} · resets {reset_time}"
    return f"Approaching {limit_name}"
