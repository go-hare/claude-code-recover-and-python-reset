"""
Common constants.

Port of: src/constants/common.ts
"""

from datetime import date


def get_local_iso_date() -> str:
    return date.today().isoformat()
