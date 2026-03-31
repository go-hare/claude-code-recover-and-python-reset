from __future__ import annotations

import asyncio
from dataclasses import dataclass

from claude_code_py.commands.parser import parse_slash_command
from claude_code_py.commands.registry import CommandRegistry
from claude_code_py.commands.types import (
    BaseCommand,
    CommandEnvironment,
    LocalCommand,
    PromptCommand,
)
from claude_code_py.engine.query_engine import QueryEngine
from claude_code_py.sessions.storage import SessionStore


@dataclass(slots=True)
class InputResult:
    output: str
    should_exit: bool = False


async def _ainput(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def execute_user_input(
    raw_input: str,
    *,
    engine_ref: dict[str, QueryEngine],
    command_registry: CommandRegistry,
    session_store: SessionStore,
) -> InputResult:
    """Dispatch one line of user input through slash commands or the engine."""

    def set_engine(next_engine: QueryEngine) -> None:
        engine_ref["engine"] = next_engine
        command_registry.refresh(
            cwd=next_engine.config.cwd,
            config_home=next_engine.config.resolved_config_home,
            session_id=next_engine.session_id,
        )

    engine = engine_ref["engine"]
    parsed = parse_slash_command(raw_input)
    if parsed is not None:
        command_name, args = parsed
        command = command_registry.get(command_name)
        if command is None and _looks_like_command(command_name):
            return InputResult(output=f"Unknown command: /{command_name}")
        if command is not None:
            env = CommandEnvironment(
                engine=engine,
                session_store=session_store,
                tool_registry=engine.tool_registry,
                config_home=engine.config.resolved_config_home,
                cwd=engine.config.cwd,
                set_engine=set_engine,
                list_commands=command_registry.list_commands,
                list_plugins=command_registry.list_plugins,
                list_skills=command_registry.list_skills,
            )
            if isinstance(command, LocalCommand):
                result = await command.handler(args, env)
                return InputResult(
                    output=result.output,
                    should_exit=result.should_exit,
                )
            if isinstance(command, PromptCommand):
                invocation = command.invoke(args)
                active_engine = engine_ref["engine"]
                if invocation.context == "fork":
                    query_result = await active_engine.run_subagent(
                        prompt=invocation.prompt,
                        description=invocation.description,
                        allowed_tools=invocation.allowed_tools,
                    )
                else:
                    query_result = await active_engine.submit(
                        invocation.prompt,
                        title_hint=raw_input,
                    )
                return InputResult(output=query_result.output_text)

    result = await engine_ref["engine"].submit(raw_input)
    return InputResult(output=result.output_text)


async def run_repl(
    engine: QueryEngine,
    command_registry: CommandRegistry | None = None,
) -> None:
    """Run an interactive prompt loop with slash-command support."""

    registry = command_registry or CommandRegistry(
        cwd=engine.config.cwd,
        config_home=engine.config.resolved_config_home,
        session_id=engine.session_id,
    )
    engine_ref = {"engine": engine}
    session_store = engine.session_store

    print("Claude Code REPL. Type /help for commands. Type /exit to quit.")
    while True:
        try:
            raw = (await _ainput("you> ")).strip()
        except EOFError:
            print()
            return

        if not raw:
            continue
        if raw in {"/exit", "exit", "quit"}:
            return

        result = await execute_user_input(
            raw,
            engine_ref=engine_ref,
            command_registry=registry,
            session_store=session_store,
        )
        if result.output:
            print(f"assistant> {result.output}")
        if result.should_exit:
            return


def _looks_like_command(command_name: str) -> bool:
    return all(character.isalnum() or character in ":-_" for character in command_name)
