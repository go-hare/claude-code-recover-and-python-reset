"""
Model allowlist checking.

Port of: src/utils/model/modelAllowlist.ts
"""

from __future__ import annotations

from hare.utils.model.aliases import is_model_alias, is_model_family_alias


def is_model_allowed(model: str) -> bool:
    """
    Check if a model is allowed by the availableModels allowlist.
    If availableModels is not configured, all models are allowed.
    """
    # No restrictions in the Python port (settings not fully ported)
    return True
