"""
Post-compact cleanup.

Port of: src/services/compact/postCompactCleanup.ts
"""

from hare.services.compact.compact_warning_state import clear_compact_warning_suppression


def run_post_compact_cleanup(query_source: str = "") -> None:
    """Run cleanup after compaction."""
    clear_compact_warning_suppression()
