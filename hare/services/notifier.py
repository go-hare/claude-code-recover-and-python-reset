"""
Notification service.

Port of: src/services/notifier.ts

Sends notifications via terminal bell or other channels.
"""

from __future__ import annotations

import sys
from typing import Literal, Optional


NotificationChannel = Literal["terminal", "iterm2", "terminal_bell"]


def send_notification(
    title: str,
    body: str = "",
    channel: NotificationChannel = "terminal",
) -> None:
    """Send a notification to the user."""
    if channel == "terminal_bell":
        sys.stderr.write("\a")
        sys.stderr.flush()
    elif channel == "iterm2":
        _send_iterm2_notification(title, body)
    else:
        _send_terminal_notification(title, body)


def _send_terminal_notification(title: str, body: str) -> None:
    """Send notification via terminal escape sequence."""
    sys.stderr.write(f"\033]0;{title}\007")
    sys.stderr.flush()


def _send_iterm2_notification(title: str, body: str) -> None:
    """Send notification via iTerm2 escape sequence."""
    msg = f"{title}: {body}" if body else title
    sys.stderr.write(f"\033]9;{msg}\007")
    sys.stderr.flush()
