"""
Model string resolution.

Port of: src/utils/model/modelStrings.ts

Maps model keys to provider-specific model ID strings.
"""

from __future__ import annotations

from typing import Any

from hare.utils.model.providers import get_api_provider

# Canonical model configs: key -> {firstParty, bedrock, vertex, foundry}
ALL_MODEL_CONFIGS: dict[str, dict[str, str]] = {
    "opus46": {
        "firstParty": "claude-opus-4-6-20260301",
        "bedrock": "anthropic.claude-opus-4-6-v1",
        "vertex": "claude-opus-4-6@20260301",
        "foundry": "claude-opus-4-6-20260301",
    },
    "opus45": {
        "firstParty": "claude-opus-4-5-20250514",
        "bedrock": "anthropic.claude-opus-4-5-v1",
        "vertex": "claude-opus-4-5@20250514",
        "foundry": "claude-opus-4-5-20250514",
    },
    "opus41": {
        "firstParty": "claude-opus-4-1-20250805",
        "bedrock": "anthropic.claude-opus-4-1-v1",
        "vertex": "claude-opus-4-1@20250805",
        "foundry": "claude-opus-4-1-20250805",
    },
    "opus40": {
        "firstParty": "claude-opus-4-20250514",
        "bedrock": "anthropic.claude-opus-4-v1",
        "vertex": "claude-opus-4@20250514",
        "foundry": "claude-opus-4-20250514",
    },
    "sonnet46": {
        "firstParty": "claude-sonnet-4-6-20260301",
        "bedrock": "anthropic.claude-sonnet-4-6-v1",
        "vertex": "claude-sonnet-4-6@20260301",
        "foundry": "claude-sonnet-4-6-20260301",
    },
    "sonnet45": {
        "firstParty": "claude-sonnet-4-5-20241022",
        "bedrock": "anthropic.claude-sonnet-4-5-v1",
        "vertex": "claude-sonnet-4-5@20241022",
        "foundry": "claude-sonnet-4-5-20241022",
    },
    "sonnet40": {
        "firstParty": "claude-sonnet-4-20250514",
        "bedrock": "anthropic.claude-sonnet-4-v1",
        "vertex": "claude-sonnet-4@20250514",
        "foundry": "claude-sonnet-4-20250514",
    },
    "sonnet37": {
        "firstParty": "claude-3-7-sonnet-20250219",
        "bedrock": "anthropic.claude-3-7-sonnet-20250219-v1:0",
        "vertex": "claude-3-7-sonnet@20250219",
        "foundry": "claude-3-7-sonnet-20250219",
    },
    "sonnet35": {
        "firstParty": "claude-3-5-sonnet-20241022",
        "bedrock": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "vertex": "claude-3-5-sonnet-v2@20241022",
        "foundry": "claude-3-5-sonnet-20241022",
    },
    "haiku45": {
        "firstParty": "claude-haiku-4-5-20250514",
        "bedrock": "anthropic.claude-haiku-4-5-v1",
        "vertex": "claude-haiku-4-5@20250514",
        "foundry": "claude-haiku-4-5-20250514",
    },
    "haiku35": {
        "firstParty": "claude-3-5-haiku-20241022",
        "bedrock": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "vertex": "claude-3-5-haiku@20241022",
        "foundry": "claude-3-5-haiku-20241022",
    },
}

MODEL_KEYS = list(ALL_MODEL_CONFIGS.keys())

# Reverse mapping from canonical ID to key
CANONICAL_ID_TO_KEY: dict[str, str] = {
    cfg["firstParty"]: key for key, cfg in ALL_MODEL_CONFIGS.items()
}


_cached_strings: dict[str, str] | None = None


def get_model_strings() -> dict[str, str]:
    """Get model strings for the current API provider."""
    global _cached_strings
    if _cached_strings is not None:
        return dict(_cached_strings)

    provider = get_api_provider()
    result = {}
    for key, configs in ALL_MODEL_CONFIGS.items():
        result[key] = configs.get(provider, configs["firstParty"])

    _cached_strings = result
    return dict(result)


def resolve_overridden_model(model_id: str) -> str:
    """
    Resolve an overridden model ID back to its canonical first-party ID.
    If no override matches, return unchanged.
    """
    return model_id
