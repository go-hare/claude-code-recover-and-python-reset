"""
Output style configuration.

Port of: src/constants/outputStyles.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OutputStyleConfig:
    name: str
    description: str
    system_prompt_addition: str = ""
    output_style_label: str = ""


OUTPUT_STYLE_CONFIGS: dict[str, OutputStyleConfig] = {
    "concise": OutputStyleConfig(
        name="concise",
        description="Brief, to-the-point responses",
        system_prompt_addition="Be concise. Minimize output length. Skip unnecessary explanation.",
        output_style_label="Concise",
    ),
    "explanatory": OutputStyleConfig(
        name="explanatory",
        description="Detailed explanations with context",
        system_prompt_addition="Provide thorough explanations. Include context and reasoning.",
        output_style_label="Explanatory",
    ),
    "learning": OutputStyleConfig(
        name="learning",
        description="Teaching-oriented responses with explanations of concepts",
        system_prompt_addition="Explain concepts as you go. Help the user learn from the changes you make.",
        output_style_label="Learning",
    ),
}


def get_all_output_styles() -> list[str]:
    return list(OUTPUT_STYLE_CONFIGS.keys())


def get_output_style_config(name: str) -> Optional[OutputStyleConfig]:
    return OUTPUT_STYLE_CONFIGS.get(name)


def has_custom_output_style(name: str) -> bool:
    return name in OUTPUT_STYLE_CONFIGS
