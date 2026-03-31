"""
Session setup – initialization before the REPL renders.

Port of: src/setup.ts

Handles:
- Environment validation
- Working directory setup
- Hooks configuration
- Background jobs
- Permission mode validation
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from hare.utils.cwd import set_cwd


async def setup(
    *,
    cwd: str,
    permission_mode: str = "default",
    allow_dangerously_skip_permissions: bool = False,
    worktree_enabled: bool = False,
    worktree_name: Optional[str] = None,
    tmux_enabled: bool = False,
    custom_session_id: Optional[str] = None,
) -> None:
    """
    Session setup matching setup() in src/setup.ts.

    Sets up the working directory, validates permissions, starts background
    jobs, and prefetches data needed before the first query.
    """
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Hare requires Python 3.11 or higher.", file=sys.stderr)
        sys.exit(1)

    # Set custom session ID if provided
    if custom_session_id:
        from hare.bootstrap.state import switch_session
        from hare.types.ids import as_session_id
        switch_session(as_session_id(custom_session_id))

    # Set working directory
    set_cwd(cwd)

    # Validate bypass permissions mode
    if permission_mode == "bypassPermissions" or allow_dangerously_skip_permissions:
        if os.name != "nt" and os.getuid() == 0 and os.environ.get("IS_SANDBOX") != "1":
            print(
                "--dangerously-skip-permissions cannot be used with root/sudo privileges "
                "for security reasons",
                file=sys.stderr,
            )
            sys.exit(1)

    # Enable configs
    from hare.utils.config import enable_configs
    enable_configs()
