"""
Model aliases.

Port of: src/utils/model/aliases.ts
"""

from __future__ import annotations

from typing import Literal

MODEL_ALIASES = (
    "sonnet", "opus", "haiku", "best",
    "sonnet[1m]", "opus[1m]", "opusplan",
)
ModelAlias = Literal[
    "sonnet", "opus", "haiku", "best",
    "sonnet[1m]", "opus[1m]", "opusplan",
]

MODEL_FAMILY_ALIASES = ("sonnet", "opus", "haiku")


def is_model_alias(model_input: str) -> bool:
    return model_input.lower() in [a.lower() for a in MODEL_ALIASES]


def is_model_family_alias(model: str) -> bool:
    return model.lower() in [a.lower() for a in MODEL_FAMILY_ALIASES]
