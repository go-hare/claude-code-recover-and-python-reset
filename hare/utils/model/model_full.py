"""
Full model resolution.

Port of: src/utils/model/model.ts

Resolves which model to use based on user settings, environment,
subscription type, and runtime context.
"""

from __future__ import annotations

import os
from typing import Optional


def get_small_fast_model() -> str:
    return os.environ.get("ANTHROPIC_SMALL_FAST_MODEL", get_default_haiku_model())


def get_default_opus_model() -> str:
    env = os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
    if env:
        return env
    return "claude-opus-4-0-20250514"


def get_default_sonnet_model() -> str:
    env = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
    if env:
        return env
    return "claude-sonnet-4-20250514"


def get_default_haiku_model() -> str:
    env = os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL")
    if env:
        return env
    return "claude-haiku-4-20250414"


def get_user_specified_model_setting() -> Optional[str]:
    """Get user-specified model from env/settings."""
    env_model = os.environ.get("ANTHROPIC_MODEL")
    if env_model:
        return env_model
    return None


def get_main_loop_model() -> str:
    """Get the main loop model to use."""
    user_model = get_user_specified_model_setting()
    if user_model:
        return user_model
    return get_default_sonnet_model()


def get_best_model() -> str:
    return get_default_opus_model()


def get_runtime_main_loop_model(
    *,
    permission_mode: str = "",
    main_loop_model: str = "",
    exceeds_200k_tokens: bool = False,
) -> str:
    """Get the model to use for runtime, considering context."""
    user_setting = get_user_specified_model_setting()

    if user_setting == "opusplan" and permission_mode == "plan" and not exceeds_200k_tokens:
        return get_default_opus_model()

    if user_setting == "haiku" and permission_mode == "plan":
        return get_default_sonnet_model()

    return main_loop_model or get_main_loop_model()
