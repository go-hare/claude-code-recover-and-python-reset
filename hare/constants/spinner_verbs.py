"""
Spinner verb phrases.

Port of: src/constants/spinnerVerbs.ts
"""

from __future__ import annotations

SPINNER_VERBS: list[str] = [
    "Thinking",
    "Reasoning",
    "Analyzing",
    "Processing",
    "Computing",
    "Evaluating",
    "Considering",
    "Examining",
    "Reviewing",
    "Exploring",
    "Investigating",
    "Planning",
    "Synthesizing",
    "Deliberating",
    "Formulating",
    "Strategizing",
    "Brainstorming",
    "Contemplating",
    "Pondering",
    "Cogitating",
]


def get_spinner_verbs() -> list[str]:
    return list(SPINNER_VERBS)


def get_random_spinner_verb() -> str:
    import random
    return random.choice(SPINNER_VERBS)
