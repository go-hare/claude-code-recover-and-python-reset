"""
Main CLI application – sets up Commander, parses args, launches REPL or print mode.

Port of: src/main.tsx

The main() function in the TS source builds a Commander program with all
subcommands and options, then renders the REPL via React/Ink. In this
Python port, we use argparse and a simple REPL loop.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any, Optional

from hare import VERSION
from hare.bootstrap.state import (
    get_session_id,
    set_is_non_interactive_session,
    set_original_cwd,
    set_project_root,
)
from hare.commands import get_commands
from hare.setup import setup
from hare.tools import get_all_base_tools, get_tools
from hare.tool import get_empty_tool_permission_context
from hare.utils.cwd import get_cwd, set_cwd


async def cli_main(args: list[str] | None = None) -> None:
    """
    Main CLI entry point. Mirrors the main() export from src/main.tsx.

    In the TS source this:
    1. Builds a Commander program with all CLI options
    2. Parses arguments
    3. Calls setup()
    4. Either renders the REPL (interactive) or runs in print mode (non-interactive)
    """
    parser = argparse.ArgumentParser(
        prog="hare",
        description=f"Hare CLI v{VERSION} – Python port of Claude Code",
    )
    parser.add_argument("--version", "-v", action="version", version=f"{VERSION} (Claude Code)")
    parser.add_argument("-p", "--print", dest="print_mode", metavar="PROMPT",
                        help="Run in non-interactive (print) mode with the given prompt")
    parser.add_argument("--model", default=None, help="Model to use")
    parser.add_argument("--max-turns", type=int, default=None, help="Max turns for the query loop")
    parser.add_argument("--permission-mode", default="default",
                        choices=["default", "acceptEdits", "bypassPermissions", "plan"],
                        help="Permission mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--bare", action="store_true", help="Bare/simple mode")
    parser.add_argument("--cwd", default=None, help="Working directory")
    parser.add_argument("--system-prompt", default=None, help="Custom system prompt")
    parser.add_argument("--append-system-prompt", default=None, help="Append to system prompt")
    parser.add_argument("prompt", nargs="*", help="Prompt text (non-interactive mode)")

    parsed = parser.parse_args(args)

    # Set working directory
    cwd = parsed.cwd or os.getcwd()
    set_cwd(cwd)
    set_original_cwd(cwd)
    set_project_root(cwd)

    # Run setup
    await setup(
        cwd=cwd,
        permission_mode=parsed.permission_mode,
    )

    # Determine mode
    prompt = parsed.print_mode or " ".join(parsed.prompt) if parsed.prompt else None

    if prompt:
        # Non-interactive (print) mode
        set_is_non_interactive_session(True)
        await _run_print_mode(
            prompt=prompt,
            model=parsed.model,
            max_turns=parsed.max_turns,
            verbose=parsed.verbose,
            system_prompt=parsed.system_prompt,
            append_system_prompt=parsed.append_system_prompt,
        )
    else:
        # Interactive REPL mode
        await _run_repl(
            model=parsed.model,
            verbose=parsed.verbose,
            system_prompt=parsed.system_prompt,
            append_system_prompt=parsed.append_system_prompt,
        )


async def _run_print_mode(
    prompt: str,
    model: Optional[str] = None,
    max_turns: Optional[int] = None,
    verbose: bool = False,
    system_prompt: Optional[str] = None,
    append_system_prompt: Optional[str] = None,
) -> None:
    """Run in non-interactive (print) mode. Mirrors the print path in main.tsx."""
    from hare.query_engine import QueryEngine, QueryEngineConfig

    permission_context = get_empty_tool_permission_context()
    tools = get_tools(permission_context)
    commands = await get_commands(get_cwd())

    engine = QueryEngine(QueryEngineConfig(
        cwd=get_cwd(),
        tools=tools,
        commands=commands,
        can_use_tool=_default_can_use_tool,
        get_app_state=lambda: {},
        set_app_state=lambda f: None,
        user_specified_model=model,
        max_turns=max_turns,
        verbose=verbose,
        custom_system_prompt=system_prompt,
        append_system_prompt=append_system_prompt,
    ))

    async for msg in engine.submit_message(prompt):
        msg_type = msg.get("type", "")
        if msg_type == "result":
            result_text = msg.get("result", "")
            if result_text:
                print(result_text)
            if msg.get("is_error"):
                sys.exit(1)


async def _run_repl(
    model: Optional[str] = None,
    verbose: bool = False,
    system_prompt: Optional[str] = None,
    append_system_prompt: Optional[str] = None,
) -> None:
    """Run the interactive REPL. Simplified version of the React/Ink REPL."""
    from hare.query_engine import QueryEngine, QueryEngineConfig

    permission_context = get_empty_tool_permission_context()
    tools = get_tools(permission_context)
    commands = await get_commands(get_cwd())

    engine = QueryEngine(QueryEngineConfig(
        cwd=get_cwd(),
        tools=tools,
        commands=commands,
        can_use_tool=_default_can_use_tool,
        get_app_state=lambda: {},
        set_app_state=lambda f: None,
        user_specified_model=model,
        verbose=verbose,
        custom_system_prompt=system_prompt,
        append_system_prompt=append_system_prompt,
    ))

    print(f"\nHare v{VERSION} (Claude Code Python Port)")
    print(f"Session: {get_session_id()}")
    print(f"Working directory: {get_cwd()}")
    print("Type /help for available commands, or enter a prompt.\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit"):
            print("Goodbye!")
            break

        if user_input.startswith("/"):
            # Handle slash commands
            cmd_name = user_input.split()[0][1:]
            from hare.commands import find_command
            cmd = find_command(cmd_name, commands)
            if cmd is None:
                print(f"Unknown command: {user_input}")
                continue
            if cmd.type == "local":
                try:
                    result = await cmd.call(user_input, {})
                    print(result.get("text", str(result)))
                except Exception as e:
                    print(f"Error: {e}")
                continue

        # Send to model
        async for msg in engine.submit_message(user_input):
            msg_type = msg.get("type", "")
            if msg_type == "result":
                result_text = msg.get("result", "")
                if result_text:
                    print(f"\n{result_text}\n")
                elif msg.get("is_error"):
                    errors = msg.get("errors", [])
                    for err in errors:
                        print(f"Error: {err}")


async def _default_can_use_tool(
    tool: Any, input: Any, context: Any, assistant_msg: Any, tool_use_id: str, force: Any
) -> Any:
    """Default permission handler – allows all tools."""
    from hare.types.permissions import PermissionAllowDecision
    return PermissionAllowDecision(behavior="allow", updated_input=input)
