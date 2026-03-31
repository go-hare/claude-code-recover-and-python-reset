"""
CLI handler for auth subcommand.

Port of: src/cli/auth.ts
"""

from __future__ import annotations

import os
from typing import Any


async def handle_auth_command(args: dict[str, Any]) -> None:
    """Handle the 'auth' CLI subcommand."""
    action = args.get("action", "status")
    if action == "login":
        print("Login flow not yet implemented in Python port.")
    elif action == "logout":
        print("Logout flow not yet implemented in Python port.")
    elif action == "status":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:]
            print(f"Authenticated via API key: {masked}")
        else:
            print("Not authenticated. Set ANTHROPIC_API_KEY environment variable.")
    else:
        print(f"Unknown auth action: {action}")
