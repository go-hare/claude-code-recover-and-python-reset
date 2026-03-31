from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .api.anthropic_client import AnthropicSDKClient
from .api.base import ModelClient
from .api.stub_client import RuleBasedModelClient
from .commands.registry import CommandRegistry
from .config import AppConfig
from .engine.query_engine import QueryEngine
from .permissions.policy import PermissionMode, PermissionPolicy
from .repl import execute_user_input, run_repl
from .tools.defaults import build_default_tool_registry


def build_engine(config: AppConfig, client_name: str) -> QueryEngine:
    """Construct a configured query engine."""

    model_client: ModelClient
    if client_name == "anthropic":
        model_client = AnthropicSDKClient()
    else:
        model_client = RuleBasedModelClient()

    tool_registry = build_default_tool_registry()
    policy = PermissionPolicy(mode=PermissionMode.DEFAULT)
    return QueryEngine(
        config=config,
        model_client=model_client,
        tool_registry=tool_registry,
        permission_policy=policy,
    )


async def run_prompt(
    engine: QueryEngine,
    prompt: str,
    command_registry: CommandRegistry,
) -> int:
    """Execute a single prompt or slash command and print the final response."""

    engine_ref = {"engine": engine}
    result = await execute_user_input(
        prompt,
        engine_ref=engine_ref,
        command_registry=command_registry,
        session_store=engine.session_store,
    )
    if result.output:
        print(result.output)
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the command line parser."""

    parser = argparse.ArgumentParser(description="Python port of the Claude Code flow")
    parser.add_argument(
        "--client",
        choices=["stub", "anthropic"],
        default="stub",
        help="Model backend to use.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    repl_parser = subparsers.add_parser("repl", help="Start an interactive session.")
    repl_parser.add_argument(
        "--cwd",
        default=str(Path.cwd()),
        help="Working directory for file and shell tools.",
    )

    run_parser = subparsers.add_parser("run", help="Execute a single prompt.")
    run_parser.add_argument("prompt", help="Prompt text to send to the engine.")
    run_parser.add_argument(
        "--cwd",
        default=str(Path.cwd()),
        help="Working directory for file and shell tools.",
    )

    return parser


def main() -> None:
    """CLI entrypoint."""

    parser = create_parser()
    args = parser.parse_args()

    config = AppConfig.from_env(Path(args.cwd))
    if args.client == "anthropic":
        config.use_stub_model = False

    engine = build_engine(config, args.client)
    command_registry = CommandRegistry(
        cwd=engine.config.cwd,
        config_home=engine.config.resolved_config_home,
        session_id=engine.session_id,
    )

    if args.command == "repl":
        asyncio.run(run_repl(engine, command_registry))
        return
    if args.command == "run":
        raise SystemExit(asyncio.run(run_prompt(engine, args.prompt, command_registry)))

    parser.error(f"Unsupported command: {args.command}")
