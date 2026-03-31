"""
API provider detection.

Port of: src/utils/model/providers.ts
"""

from __future__ import annotations

import os
from typing import Literal

from hare.utils.env_utils import is_env_truthy

APIProvider = Literal["firstParty", "bedrock", "vertex", "foundry"]


def get_api_provider() -> APIProvider:
    """Detect which API provider to use based on environment variables."""
    if is_env_truthy(os.environ.get("CLAUDE_CODE_USE_BEDROCK")):
        return "bedrock"
    elif is_env_truthy(os.environ.get("CLAUDE_CODE_USE_VERTEX")):
        return "vertex"
    elif is_env_truthy(os.environ.get("CLAUDE_CODE_USE_FOUNDRY")):
        return "foundry"
    return "firstParty"


def is_first_party_anthropic_base_url() -> bool:
    """Check if ANTHROPIC_BASE_URL points to Anthropic's API."""
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not base_url:
        return True
    try:
        from urllib.parse import urlparse
        host = urlparse(base_url).hostname
        return host in ("api.anthropic.com",)
    except Exception:
        return False
