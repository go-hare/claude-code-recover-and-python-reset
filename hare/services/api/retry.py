"""
Retry logic for API calls.

Port of: src/services/api/withRetry.ts
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0


async def with_retry(
    fn: Callable[..., Any],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_errors: Optional[tuple[type[Exception], ...]] = None,
) -> Any:
    """
    Execute a function with exponential backoff retry.

    Mirrors withRetry() from withRetry.ts.
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_error = e

            if retryable_errors and not isinstance(e, retryable_errors):
                raise

            if attempt >= max_retries:
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            await asyncio.sleep(delay + jitter)

    raise last_error  # type: ignore[misc]


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable (rate limits, server errors)."""
    msg = str(error).lower()
    retryable_patterns = [
        "rate limit",
        "overloaded",
        "529",
        "503",
        "502",
        "timeout",
        "connection",
    ]
    return any(p in msg for p in retryable_patterns)
