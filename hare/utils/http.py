"""
HTTP utilities.

Port of: src/utils/http.ts

HTTP request helpers with proxy support and retry logic.
"""

from __future__ import annotations

import os
import urllib.request
import urllib.error
import json
from typing import Any, Optional


def get_proxy_url() -> Optional[str]:
    """Get proxy URL from environment."""
    return (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )


def build_proxy_handler() -> Optional[urllib.request.ProxyHandler]:
    """Build a urllib proxy handler if proxy is configured."""
    proxy = get_proxy_url()
    if proxy:
        return urllib.request.ProxyHandler({
            "http": proxy,
            "https": proxy,
        })
    return None


async def fetch_json(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 30.0,
) -> Any:
    """Fetch JSON from a URL."""
    import asyncio

    def _fetch():
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        req.add_header("Accept", "application/json")

        handlers = []
        proxy_handler = build_proxy_handler()
        if proxy_handler:
            handlers.append(proxy_handler)

        opener = urllib.request.build_opener(*handlers)
        resp = opener.open(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch)


async def fetch_text(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 30.0,
) -> str:
    """Fetch text content from a URL."""
    import asyncio

    def _fetch():
        req = urllib.request.Request(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        handlers = []
        proxy_handler = build_proxy_handler()
        if proxy_handler:
            handlers.append(proxy_handler)

        opener = urllib.request.build_opener(*handlers)
        resp = opener.open(req, timeout=timeout)
        return resp.read().decode("utf-8")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch)


def is_url(s: str) -> bool:
    """Check if string is a URL."""
    return s.startswith("http://") or s.startswith("https://")
