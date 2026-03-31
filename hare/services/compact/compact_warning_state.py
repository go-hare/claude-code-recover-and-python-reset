"""
Compact warning state management.

Port of: src/services/compact/compactWarningState.ts
"""

_suppressed = False


def suppress_compact_warning() -> None:
    global _suppressed
    _suppressed = True


def clear_compact_warning_suppression() -> None:
    global _suppressed
    _suppressed = False


def is_compact_warning_suppressed() -> bool:
    return _suppressed
