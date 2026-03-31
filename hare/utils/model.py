"""
Model selection and resolution.

Port of: src/utils/model/model.ts

Handles model name resolution, alias expansion, default model selection,
and model display name formatting.
"""

from __future__ import annotations

import os
import re
from typing import Literal, Optional

ModelShortName = str
ModelName = str
ModelAlias = Literal["opus", "sonnet", "haiku", "best", "opusplan"]
ModelSetting = ModelName | None

# Model strings – mirrors getModelStrings() in TS
_MODEL_STRINGS = {
    "opus46": "claude-opus-4-6-20260301",
    "opus45": "claude-opus-4-5-20250514",
    "opus41": "claude-opus-4-1-20250805",
    "opus40": "claude-opus-4-20250514",
    "sonnet46": "claude-sonnet-4-6-20260301",
    "sonnet45": "claude-sonnet-4-5-20241022",
    "sonnet40": "claude-sonnet-4-20250514",
    "sonnet37": "claude-3-7-sonnet-20250219",
    "sonnet35": "claude-3-5-sonnet-20241022",
    "haiku45": "claude-haiku-4-5-20250514",
    "haiku35": "claude-3-5-haiku-20241022",
}


def get_model_strings() -> dict[str, str]:
    """Get the model string constants."""
    return dict(_MODEL_STRINGS)


def get_small_fast_model() -> ModelName:
    """Get the small fast model (Haiku)."""
    return os.environ.get("ANTHROPIC_SMALL_FAST_MODEL", get_default_haiku_model())


def get_default_opus_model() -> ModelName:
    override = os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
    if override:
        return override
    return _MODEL_STRINGS["opus46"]


def get_default_sonnet_model() -> ModelName:
    override = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
    if override:
        return override
    return _MODEL_STRINGS["sonnet46"]


def get_default_haiku_model() -> ModelName:
    override = os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL")
    if override:
        return override
    return _MODEL_STRINGS["haiku45"]


def get_best_model() -> ModelName:
    return get_default_opus_model()


def get_user_specified_model_setting() -> ModelSetting | None:
    """
    Get the user-specified model from environment or settings.

    Priority:
    1. ANTHROPIC_MODEL environment variable
    2. Settings (from user's saved settings)
    """
    model = os.environ.get("ANTHROPIC_MODEL")
    if model:
        return model

    from hare.utils.config import get_global_config
    # Config doesn't have a model field in our simplified port
    return None


def get_main_loop_model() -> ModelName:
    """
    Get the main loop model to use for the current session.

    Priority:
    1. User-specified model
    2. Built-in default
    """
    model = get_user_specified_model_setting()
    if model is not None:
        return parse_user_specified_model(model)
    return get_default_main_loop_model()


def get_default_main_loop_model_setting() -> ModelName:
    """Get the default model setting."""
    return get_default_sonnet_model()


def get_default_main_loop_model() -> ModelName:
    """Get the default model (bypassing user preferences)."""
    return parse_user_specified_model(get_default_main_loop_model_setting())


_MODEL_ALIASES = {"opus", "sonnet", "haiku", "best", "opusplan"}


def is_model_alias(value: str) -> bool:
    return value.lower() in _MODEL_ALIASES


def parse_user_specified_model(model_input: str) -> ModelName:
    """
    Resolve a model alias or name to a full model name.

    Supports [1m] suffix for 1M context window.
    """
    trimmed = model_input.strip()
    normalized = trimmed.lower()

    has_1m = normalized.endswith("[1m]")
    base = normalized[:-4].strip() if has_1m else normalized
    suffix = "[1m]" if has_1m else ""

    if is_model_alias(base):
        if base == "opusplan":
            return get_default_sonnet_model() + suffix
        elif base == "sonnet":
            return get_default_sonnet_model() + suffix
        elif base == "haiku":
            return get_default_haiku_model() + suffix
        elif base == "opus":
            return get_default_opus_model() + suffix
        elif base == "best":
            return get_best_model()

    # Preserve original case for custom model names
    if has_1m:
        return trimmed[:-4].strip() + "[1m]"
    return trimmed


def first_party_name_to_canonical(name: ModelName) -> ModelShortName:
    """
    Maps a first-party model name to its canonical short form.
    E.g., 'claude-opus-4-6-20260301' -> 'claude-opus-4-6'
    """
    lower = name.lower()

    checks = [
        ("claude-opus-4-6", "claude-opus-4-6"),
        ("claude-opus-4-5", "claude-opus-4-5"),
        ("claude-opus-4-1", "claude-opus-4-1"),
        ("claude-opus-4", "claude-opus-4"),
        ("claude-sonnet-4-6", "claude-sonnet-4-6"),
        ("claude-sonnet-4-5", "claude-sonnet-4-5"),
        ("claude-sonnet-4", "claude-sonnet-4"),
        ("claude-haiku-4-5", "claude-haiku-4-5"),
        ("claude-3-7-sonnet", "claude-3-7-sonnet"),
        ("claude-3-5-sonnet", "claude-3-5-sonnet"),
        ("claude-3-5-haiku", "claude-3-5-haiku"),
        ("claude-3-opus", "claude-3-opus"),
        ("claude-3-sonnet", "claude-3-sonnet"),
        ("claude-3-haiku", "claude-3-haiku"),
    ]

    for check_str, canonical in checks:
        if check_str in lower:
            return canonical

    match = re.match(r"(claude-(?:\d+-\d+-)?\w+)", lower)
    if match:
        return match.group(1)

    return name


def get_canonical_name(full_model_name: ModelName) -> ModelShortName:
    """Get the canonical short name for any model."""
    return first_party_name_to_canonical(full_model_name)


def get_public_model_display_name(model: ModelName) -> Optional[str]:
    """Returns a human-readable display name for known public models."""
    ms = _MODEL_STRINGS

    display_map = {
        ms["opus46"]: "Opus 4.6",
        ms["opus46"] + "[1m]": "Opus 4.6 (1M context)",
        ms["opus45"]: "Opus 4.5",
        ms["opus41"]: "Opus 4.1",
        ms["opus40"]: "Opus 4",
        ms["sonnet46"] + "[1m]": "Sonnet 4.6 (1M context)",
        ms["sonnet46"]: "Sonnet 4.6",
        ms["sonnet45"] + "[1m]": "Sonnet 4.5 (1M context)",
        ms["sonnet45"]: "Sonnet 4.5",
        ms["sonnet40"]: "Sonnet 4",
        ms["sonnet40"] + "[1m]": "Sonnet 4 (1M context)",
        ms["sonnet37"]: "Sonnet 3.7",
        ms["sonnet35"]: "Sonnet 3.5",
        ms["haiku45"]: "Haiku 4.5",
        ms["haiku35"]: "Haiku 3.5",
    }

    return display_map.get(model)


def render_model_name(model: ModelName) -> str:
    """Render a model name for display."""
    public = get_public_model_display_name(model)
    if public:
        return public
    return model


def get_public_model_name(model: ModelName) -> str:
    """Returns a safe author name for public display (e.g. git commit trailers)."""
    public = get_public_model_display_name(model)
    if public:
        return f"Claude {public}"
    return f"Claude ({model})"


def normalize_model_string_for_api(model: str) -> str:
    """Remove context window suffixes like [1m] for API calls."""
    return re.sub(r"\[\d+m\]", "", model, flags=re.IGNORECASE)


def get_runtime_main_loop_model(
    *,
    permission_mode: str,
    main_loop_model: str,
    exceeds_200k_tokens: bool = False,
) -> ModelName:
    """Get the model to use for runtime, depending on the context."""
    user_model = get_user_specified_model_setting()

    # opusplan uses Opus in plan mode
    if user_model == "opusplan" and permission_mode == "plan" and not exceeds_200k_tokens:
        return get_default_opus_model()

    # haiku uses sonnet in plan mode
    if user_model == "haiku" and permission_mode == "plan":
        return get_default_sonnet_model()

    return main_loop_model


def model_display_string(model: ModelSetting) -> str:
    """Get display string for a model setting."""
    if model is None:
        return f"Default ({get_default_main_loop_model()})"
    resolved = parse_user_specified_model(model)
    if model == resolved:
        return resolved
    return f"{model} ({resolved})"


def get_marketing_name_for_model(model_id: str) -> Optional[str]:
    """Returns a marketing name for a model ID."""
    has_1m = "[1m]" in model_id.lower()
    canonical = get_canonical_name(model_id)

    mapping = [
        ("claude-opus-4-6", "Opus 4.6", "Opus 4.6 (with 1M context)"),
        ("claude-opus-4-5", "Opus 4.5", None),
        ("claude-opus-4-1", "Opus 4.1", None),
        ("claude-opus-4", "Opus 4", None),
        ("claude-sonnet-4-6", "Sonnet 4.6", "Sonnet 4.6 (with 1M context)"),
        ("claude-sonnet-4-5", "Sonnet 4.5", "Sonnet 4.5 (with 1M context)"),
        ("claude-sonnet-4", "Sonnet 4", "Sonnet 4 (with 1M context)"),
        ("claude-3-7-sonnet", "Claude 3.7 Sonnet", None),
        ("claude-3-5-sonnet", "Claude 3.5 Sonnet", None),
        ("claude-haiku-4-5", "Haiku 4.5", None),
        ("claude-3-5-haiku", "Claude 3.5 Haiku", None),
    ]

    for fragment, name, name_1m in mapping:
        if fragment in canonical:
            if has_1m and name_1m:
                return name_1m
            return name

    return None
