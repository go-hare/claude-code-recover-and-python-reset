"""
Unicode figure constants.

Port of: src/constants/figures.ts
"""

import os

# Check if terminal supports unicode
_supports_unicode = os.name != "nt" or os.environ.get("WT_SESSION")

FIGURES = {
    "tick": "✔" if _supports_unicode else "√",
    "cross": "✖" if _supports_unicode else "×",
    "star": "★" if _supports_unicode else "*",
    "square_small": "◻" if _supports_unicode else "□",
    "square_small_filled": "◼" if _supports_unicode else "■",
    "play": "▶" if _supports_unicode else "►",
    "circle": "◯" if _supports_unicode else "( )",
    "circle_filled": "◉" if _supports_unicode else "(*)",
    "circle_dotted": "◌" if _supports_unicode else "( )",
    "circle_double": "◎" if _supports_unicode else "(o)",
    "circle_cross": "ⓧ" if _supports_unicode else "(x)",
    "circle_pipe": "Ⓘ" if _supports_unicode else "(i)",
    "circle_question_mark": "?⃝" if _supports_unicode else "(?)",
    "bullet": "●" if _supports_unicode else "*",
    "dot": "․" if _supports_unicode else ".",
    "line": "─" if _supports_unicode else "-",
    "ellipsis": "…" if _supports_unicode else "...",
    "pointer": "❯" if _supports_unicode else ">",
    "pointer_small": "›" if _supports_unicode else ">",
    "info": "ℹ" if _supports_unicode else "i",
    "warning": "⚠" if _supports_unicode else "‼",
    "hamburger": "☰" if _supports_unicode else "≡",
    "smiley": "㋡" if _supports_unicode else "☺",
    "mustache": "෴" if _supports_unicode else "┌─┐",
    "heart": "♥" if _supports_unicode else "<3",
    "nodejs": "⬢" if _supports_unicode else "♦",
    "arrow_up": "↑" if _supports_unicode else "↑",
    "arrow_down": "↓" if _supports_unicode else "↓",
    "arrow_left": "←" if _supports_unicode else "←",
    "arrow_right": "→" if _supports_unicode else "→",
    "radio_on": "◉" if _supports_unicode else "(*)",
    "radio_off": "◯" if _supports_unicode else "( )",
    "checkbox_on": "☒" if _supports_unicode else "[×]",
    "checkbox_off": "☐" if _supports_unicode else "[ ]",
    "checkbox_circle_on": "ⓧ" if _supports_unicode else "(×)",
    "checkbox_circle_off": "Ⓘ" if _supports_unicode else "( )",
    "question_mark_prefix": "?⃝" if _supports_unicode else "(?)",
    "one_half": "½" if _supports_unicode else "1/2",
    "one_third": "⅓" if _supports_unicode else "1/3",
    "one_quarter": "¼" if _supports_unicode else "1/4",
    "one_fifth": "⅕" if _supports_unicode else "1/5",
    "one_sixth": "⅙" if _supports_unicode else "1/6",
    "one_seventh": "⅐" if _supports_unicode else "1/7",
    "one_eighth": "⅛" if _supports_unicode else "1/8",
    "one_ninth": "⅑" if _supports_unicode else "1/9",
    "one_tenth": "⅒" if _supports_unicode else "1/10",
    "two_thirds": "⅔" if _supports_unicode else "2/3",
    "two_fifths": "⅖" if _supports_unicode else "2/5",
    "three_quarters": "¾" if _supports_unicode else "3/4",
    "three_fifths": "⅗" if _supports_unicode else "3/5",
    "three_eighths": "⅜" if _supports_unicode else "3/8",
    "four_fifths": "⅘" if _supports_unicode else "4/5",
    "five_sixths": "⅚" if _supports_unicode else "5/6",
    "five_eighths": "⅝" if _supports_unicode else "5/8",
    "seven_eighths": "⅞" if _supports_unicode else "7/8",
}

PAUSE_ICON = "||"
SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
