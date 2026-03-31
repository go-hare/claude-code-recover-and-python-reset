"""
API error handling utilities.

Port of: src/services/api/errors.ts, errorUtils.ts
"""

from __future__ import annotations


class APIError(Exception):
    """Base API error."""

    def __init__(self, message: str, status_code: int = 0, **kwargs):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = kwargs.get("error_type", "api_error")


class RateLimitError(APIError):
    """Rate limit error (429)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = 0):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class OverloadedError(APIError):
    """Server overloaded (529)."""

    def __init__(self, message: str = "API overloaded"):
        super().__init__(message, status_code=529)


class AuthenticationError(APIError):
    """Authentication failed (401)."""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)


class InsufficientCreditsError(APIError):
    """Insufficient credits."""

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(message, status_code=402)


def is_retryable_api_error(error: Exception) -> bool:
    """Check if an error should be retried."""
    if isinstance(error, RateLimitError):
        return True
    if isinstance(error, OverloadedError):
        return True
    if isinstance(error, APIError) and error.status_code in (502, 503):
        return True
    msg = str(error).lower()
    return any(kw in msg for kw in ("overloaded", "rate limit", "timeout", "connection"))


def extract_error_message(error: Exception) -> str:
    """Extract a clean error message from an exception."""
    if isinstance(error, APIError):
        return str(error)
    return str(error)
