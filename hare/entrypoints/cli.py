"""
Bootstrap entrypoint – checks for special flags before loading the full CLI.

Port of: src/entrypoints/cli.tsx

All imports are dynamic to minimize module evaluation for fast paths.
Fast-path for --version has zero imports beyond this file.
"""

from __future__ import annotations

import os
import sys

VERSION = "2.1.88"
BUILD_TIME = "recovered-from-sourcemap"


def main() -> None:
    """
    Bootstrap entrypoint. Checks for special flags before loading the full CLI.

    Mirrors the async function main() in src/entrypoints/cli.tsx.
    """
    args = sys.argv[1:]

    # Fast-path for --version/-v: zero module loading needed
    if len(args) == 1 and args[0] in ("--version", "-v", "-V"):
        print(f"{VERSION} (Claude Code)")
        return

    # Set COREPACK_ENABLE_AUTO_PIN=0 (bugfix for corepack auto-pinning)
    os.environ["COREPACK_ENABLE_AUTO_PIN"] = "0"

    # Set max heap size for child processes in CCR environments
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        existing = os.environ.get("NODE_OPTIONS", "")
        os.environ["NODE_OPTIONS"] = (
            f"{existing} --max-old-space-size=8192" if existing else "--max-old-space-size=8192"
        )

    # --bare: set SIMPLE early so gates fire during module eval
    if "--bare" in args:
        os.environ["CLAUDE_CODE_SIMPLE"] = "1"

    # Redirect common update flag mistakes to the update subcommand
    if len(args) == 1 and args[0] in ("--update", "--upgrade"):
        args = ["update"]

    # No special flags detected, load and run the full CLI
    import asyncio
    from hare.main import cli_main

    asyncio.run(cli_main(args))


if __name__ == "__main__":
    main()
