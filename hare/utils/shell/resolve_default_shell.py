"""
Resolve default shell.

Port of: src/utils/shell/resolveDefaultShell.ts
"""

from __future__ import annotations

import os
import sys

from hare.utils.shell.bash_provider import BashProvider
from hare.utils.shell.powershell_provider import PowerShellProvider
from hare.utils.shell.shell_provider import ShellProvider


def resolve_default_shell() -> ShellProvider:
    """Resolve the default shell provider for the current platform."""
    if sys.platform == "win32":
        return PowerShellProvider()
    return BashProvider()


def get_shell_name() -> str:
    """Get the name of the current shell."""
    if sys.platform == "win32":
        return "powershell"
    shell = os.environ.get("SHELL", "/bin/bash")
    return os.path.basename(shell)
