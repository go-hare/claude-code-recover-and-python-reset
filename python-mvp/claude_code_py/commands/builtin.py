from __future__ import annotations

import os
from pathlib import Path
import subprocess
from uuid import UUID

from claude_code_py.commands.types import (
    BaseCommand,
    CommandEnvironment,
    LocalCommand,
    LocalCommandResult,
)
from claude_code_py.plugins.management import (
    add_marketplace_source,
    discover_plugin_records,
    format_known_marketplaces,
    format_validation_result,
    load_known_marketplaces_config,
    parse_marketplace_input,
    refresh_all_marketplaces,
    refresh_marketplace,
    remove_marketplace_source,
    resolve_plugin_record,
    set_plugin_disabled,
    uninstall_plugin,
    validate_manifest,
)
from claude_code_py.sessions.storage import SessionMetadata, SessionStore


async def _help_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    _ = args
    commands = env.list_commands()
    builtin_lines = ["Available commands:"]
    extra_lines: list[str] = []

    for command in commands:
        if command.source == "builtin":
            builtin_lines.append(_format_command_line(command))
            continue
        if not extra_lines:
            extra_lines = ["", "Available skills and plugin commands:"]
        extra_lines.append(_format_command_line(command))

    return LocalCommandResult(output="\n".join(builtin_lines + extra_lines))


async def _tasks_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    _ = args
    snapshots = env.engine.task_manager.list_snapshots()
    if not snapshots:
        return LocalCommandResult(output="No background tasks.")

    lines = ["Background tasks:"]
    for snapshot in snapshots:
        lines.append(f"- {snapshot.task_id} [{snapshot.status}] {snapshot.description}")
        if snapshot.result:
            lines.append(f"  result: {snapshot.result[:120]}")
        if snapshot.error:
            lines.append(f"  error: {snapshot.error}")
    return LocalCommandResult(output="\n".join(lines))


async def _skills_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    _ = args
    names = env.list_skills()
    if not names:
        return LocalCommandResult(output="No skills discovered.")
    return LocalCommandResult(
        output="Available skills:\n" + "\n".join(f"- /{name}" for name in names)
    )


async def _resume_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    query = args.strip()
    sessions = _load_same_repo_sessions(env)
    if not sessions:
        message = "No conversations found to resume."
        if not query:
            message = "No conversations found to resume"
        return LocalCommandResult(output=message)

    if not query:
        resumable_sessions = [
            session
            for session in sessions
            if session.session_id != env.engine.session_id
        ]
        if not resumable_sessions:
            return LocalCommandResult(output="No conversations found to resume")
        lines = ["Conversations:"]
        for session in resumable_sessions[:20]:
            lines.append(
                f"- {session.session_id}  {session.title}  [{session.updated_at}]"
            )
        lines.append("")
        lines.append("Run /resume [conversation id or search term].")
        return LocalCommandResult(output="\n".join(lines))

    target, error = _resolve_session(query, sessions, env.session_store)
    if error is not None:
        return LocalCommandResult(output=error)

    next_engine = env.engine.load_session(target.session_id)
    env.set_engine(next_engine)
    return LocalCommandResult(output="", next_engine=next_engine)


async def _clear_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    _ = args
    next_engine = env.engine.new_session()
    env.set_engine(next_engine)
    return LocalCommandResult(output="", next_engine=next_engine)


async def _plugin_command(
    args: str,
    env: CommandEnvironment,
) -> LocalCommandResult:
    parsed = _parse_plugin_args(args)
    records = discover_plugin_records(env.cwd, env.config_home)
    try:
        if parsed["type"] == "help":
            return LocalCommandResult(output=_plugin_help_output())
        if parsed["type"] in {"menu", "manage"}:
            return LocalCommandResult(output=_format_plugin_records(records))
        if parsed["type"] == "enable":
            return LocalCommandResult(
                output=_set_plugin_enabled_state(parsed.get("plugin"), records, True, env)
            )
        if parsed["type"] == "disable":
            return LocalCommandResult(
                output=_set_plugin_enabled_state(parsed.get("plugin"), records, False, env)
            )
        if parsed["type"] == "uninstall":
            return LocalCommandResult(
                output=_uninstall_plugin(parsed.get("plugin"), records, env)
            )
        if parsed["type"] == "marketplace":
            return LocalCommandResult(output=_handle_marketplace_command(parsed, env))
        if parsed["type"] == "validate":
            path = parsed.get("path")
            if path is None:
                return LocalCommandResult(output=_plugin_validate_usage())
            return LocalCommandResult(
                output=format_validation_result(validate_manifest(path, env.cwd))
            )
        if parsed["type"] == "install":
            return LocalCommandResult(output=_plugin_install_output(parsed, env))
    except ValueError as exc:
        return LocalCommandResult(output=str(exc))

    names = [record.name for record in records if not record.disabled]
    if not names:
        return LocalCommandResult(output="No plugins discovered.")
    return LocalCommandResult(
        output="Installed plugins:\n" + "\n".join(f"- {name}" for name in names)
    )


def get_builtin_commands() -> list[BaseCommand]:
    """Return the built-in local command set."""

    return [
        LocalCommand(
            name="help",
            description="Show help and available commands",
            handler=_help_command,
        ),
        LocalCommand(
            name="clear",
            description="Clear conversation history and free up context",
            aliases=["reset", "new"],
            handler=_clear_command,
        ),
        LocalCommand(
            name="resume",
            description="Resume a previous conversation",
            aliases=["continue"],
            argument_hint="[conversation id or search term]",
            handler=_resume_command,
        ),
        LocalCommand(
            name="skills",
            description="List available skills",
            handler=_skills_command,
        ),
        LocalCommand(
            name="tasks",
            description="List and manage background tasks",
            aliases=["bashes"],
            handler=_tasks_command,
        ),
        LocalCommand(
            name="plugin",
            description="Manage Claude Code plugins",
            aliases=["plugins", "marketplace"],
            handler=_plugin_command,
        ),
    ]


def _format_command_line(command: BaseCommand) -> str:
    hint = f" {command.argument_hint}" if command.argument_hint else ""
    aliases = getattr(command, "aliases", [])
    alias_text = ""
    if aliases:
        alias_text = f" (aliases: {', '.join(f'/{alias}' for alias in aliases)})"
    return f"- /{command.name}{hint}  {command.description}{alias_text}"


def _resolve_session(
    query: str,
    sessions: list[SessionMetadata],
    session_store: SessionStore,
) -> tuple[SessionMetadata | None, str | None]:
    maybe_session_id = _validate_uuid(query)
    if maybe_session_id is not None:
        exact_id_matches = [
            session for session in sessions if session.session_id == maybe_session_id
        ]
        if exact_id_matches:
            exact_id_matches.sort(key=lambda item: item.updated_at, reverse=True)
            return exact_id_matches[0], None
        direct_match = session_store.get_session_metadata(maybe_session_id)
        if direct_match is not None:
            return direct_match, None

    lowered = query.casefold().strip()
    title_matches = [
        session for session in sessions if session.title.casefold().strip() == lowered
    ]
    if len(title_matches) == 1:
        return title_matches[0], None
    if len(title_matches) > 1:
        return (
            None,
            f"Found {len(title_matches)} sessions matching {query}. Please use /resume to pick a specific session.",
        )
    return None, f"Session {query} was not found."


def _load_same_repo_sessions(env: CommandEnvironment) -> list[SessionMetadata]:
    sessions = env.session_store.list_sessions()
    worktree_paths = _get_worktree_paths(env.cwd)
    if len(worktree_paths) <= 1:
        cwd = _normalize_path_for_match(env.cwd)
        return [
            session
            for session in sessions
            if _normalize_path_for_match(session.cwd) == cwd
        ]

    return [
        session
        for session in sessions
        if any(_path_matches_worktree(session.cwd, worktree) for worktree in worktree_paths)
    ]


def _get_worktree_paths(cwd: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            check=False,
            cwd=str(cwd),
            encoding="utf-8",
        )
    except (FileNotFoundError, OSError):
        return []
    if completed.returncode != 0:
        return []

    worktree_paths = [
        Path(line[len("worktree ") :]).resolve()
        for line in completed.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    if not worktree_paths:
        return []

    cwd_resolved = cwd.resolve()
    current_worktree = next(
        (
            path
            for path in worktree_paths
            if cwd_resolved == path or cwd_resolved.is_relative_to(path)
        ),
        None,
    )
    other_worktrees = sorted(
        [path for path in worktree_paths if path != current_worktree],
        key=lambda item: str(item).casefold(),
    )
    if current_worktree is None:
        return other_worktrees
    return [current_worktree, *other_worktrees]


def _path_matches_worktree(raw_path: str, worktree: Path) -> bool:
    session_path = Path(raw_path).resolve()
    session_text = _normalize_path_for_match(session_path)
    worktree_text = _normalize_path_for_match(worktree)
    if session_text == worktree_text:
        return True
    return session_text.startswith(worktree_text + os.sep)


def _normalize_path_for_match(path: str | Path) -> str:
    text = str(path)
    if os.name == "nt":
        return text.casefold()
    return text


def _validate_uuid(value: str) -> str | None:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _format_plugin_records(records) -> str:
    if not records:
        return "No plugins discovered."
    lines = ["Installed plugins:"]
    for record in records:
        status = "disabled" if record.disabled else "enabled"
        lines.append(f"- {record.name} [{status}] ({record.scope}) {record.path}")
    return "\n".join(lines)


def _set_plugin_enabled_state(
    plugin_name: str | None,
    records,
    enabled: bool,
    env: CommandEnvironment,
) -> str:
    if not plugin_name:
        action = "enable" if enabled else "disable"
        return f"Usage: /plugin {action} <plugin>"
    record, error = resolve_plugin_record(plugin_name, records)
    if error is not None:
        return error
    assert record is not None
    set_plugin_disabled(record, not enabled)
    env.set_engine(env.engine)
    action = "Enabled" if enabled else "Disabled"
    return f'{action} plugin "{record.name}".'


def _uninstall_plugin(
    plugin_name: str | None,
    records,
    env: CommandEnvironment,
) -> str:
    if not plugin_name:
        return "Usage: /plugin uninstall <plugin>"
    record, error = resolve_plugin_record(plugin_name, records)
    if error is not None:
        return error
    assert record is not None
    uninstall_plugin(record)
    env.set_engine(env.engine)
    return f'Uninstalled plugin "{record.name}".'


def _handle_marketplace_command(
    parsed: dict[str, str | None],
    env: CommandEnvironment,
) -> str:
    action = parsed.get("action")
    target = (parsed.get("target") or "").strip()

    if action == "list" or action is None:
        config = load_known_marketplaces_config(env.config_home)
        return format_known_marketplaces(config)

    if action == "add":
        if not target:
            return _plugin_marketplace_add_output()
        source = parse_marketplace_input(target, env.cwd)
        if source is None:
            return "Invalid marketplace source format. Try: owner/repo, https://..., or ./path"
        result = add_marketplace_source(source, env.cwd, env.config_home)
        if result.already_materialized:
            return f"Successfully added marketplace: {result.name}"
        return f"Successfully added marketplace: {result.name}"

    if action == "remove":
        if not target:
            return "Usage: /plugin marketplace remove <name>"
        remove_marketplace_source(target, env.config_home)
        return f"Successfully removed marketplace: {target}"

    if action == "update":
        config = load_known_marketplaces_config(env.config_home)
        if target:
            refresh_marketplace(target, env.config_home)
            return f"Successfully updated marketplace: {target}"
        if not config:
            return "No marketplaces configured"
        count = refresh_all_marketplaces(env.config_home)
        return f"Successfully updated {count} marketplace(s)"

    return format_known_marketplaces(load_known_marketplaces_config(env.config_home))


def _plugin_install_output(
    parsed: dict[str, str | None],
    env: CommandEnvironment,
) -> str:
    _ = parsed
    config = load_known_marketplaces_config(env.config_home)
    if not config:
        return "No marketplaces configured"
    return format_known_marketplaces(config)


def _parse_plugin_args(args: str) -> dict[str, str | None]:
    if not args.strip():
        return {"type": "menu"}

    parts = args.strip().split()
    command = parts[0].lower()

    if command in {"help", "--help", "-h"}:
        return {"type": "help"}
    if command in {"install", "i"}:
        target = parts[1] if len(parts) > 1 else None
        if not target:
            return {"type": "install", "marketplace": None, "plugin": None}
        if "@" in target:
            plugin, marketplace = target.split("@", 1)
            return {"type": "install", "plugin": plugin, "marketplace": marketplace}
        if (
            target.startswith("http://")
            or target.startswith("https://")
            or target.startswith("file://")
            or "/" in target
            or "\\" in target
        ):
            return {"type": "install", "plugin": None, "marketplace": target}
        return {"type": "install", "plugin": target, "marketplace": None}
    if command == "manage":
        return {"type": "manage"}
    if command == "uninstall":
        return {"type": "uninstall", "plugin": parts[1] if len(parts) > 1 else None}
    if command == "enable":
        return {"type": "enable", "plugin": parts[1] if len(parts) > 1 else None}
    if command == "disable":
        return {"type": "disable", "plugin": parts[1] if len(parts) > 1 else None}
    if command == "validate":
        target = " ".join(parts[1:]).strip()
        return {"type": "validate", "path": target or None}
    if command in {"marketplace", "market"}:
        action = parts[1].lower() if len(parts) > 1 else None
        target = " ".join(parts[2:]) if len(parts) > 2 else ""
        if action == "add":
            return {"type": "marketplace", "action": "add", "target": target}
        if action in {"remove", "rm"}:
            return {"type": "marketplace", "action": "remove", "target": target}
        if action == "update":
            return {"type": "marketplace", "action": "update", "target": target}
        if action == "list":
            return {"type": "marketplace", "action": "list", "target": None}
        return {"type": "marketplace", "action": None, "target": None}
    return {"type": "menu"}


def _plugin_help_output() -> str:
    return "\n".join(
        [
            "Plugin Command Usage:",
            "",
            "Installation:",
            " /plugin install - Browse and install plugins",
            " /plugin install <marketplace> - Install from specific marketplace",
            " /plugin install <plugin> - Install specific plugin",
            " /plugin install <plugin>@<market> - Install plugin from marketplace",
            "",
            "Management:",
            " /plugin manage - Manage installed plugins",
            " /plugin enable <plugin> - Enable a plugin",
            " /plugin disable <plugin> - Disable a plugin",
            " /plugin uninstall <plugin> - Uninstall a plugin",
            "",
            "Marketplaces:",
            " /plugin marketplace - Marketplace management menu",
            " /plugin marketplace add - Add a marketplace",
            " /plugin marketplace add <path/url> - Add marketplace directly",
            " /plugin marketplace update - Update marketplaces",
            " /plugin marketplace update <name> - Update specific marketplace",
            " /plugin marketplace remove - Remove a marketplace",
            " /plugin marketplace remove <name> - Remove specific marketplace",
            " /plugin marketplace list - List all marketplaces",
            "",
            "Validation:",
            " /plugin validate <path> - Validate a manifest file or directory",
            "",
            "Other:",
            " /plugin - Main plugin menu",
            " /plugin help - Show this help",
            " /plugins - Alias for /plugin",
        ]
    )


def _plugin_validate_usage() -> str:
    return "\n".join(
        [
            "Usage: /plugin validate <path>",
            "",
            "Validate a plugin or marketplace manifest file or directory.",
            "",
            "Examples:",
            "  /plugin validate .claude-plugin/plugin.json",
            "  /plugin validate /path/to/plugin-directory",
            "  /plugin validate .",
            "",
            "When given a directory, automatically validates .claude-plugin/marketplace.json",
            "or .claude-plugin/plugin.json (prefers marketplace if both exist).",
            "",
            "Or from the command line:",
            "  claude plugin validate <path>",
        ]
    )


def _plugin_marketplace_add_output() -> str:
    return "\n".join(
        [
            "Add Marketplace",
            "",
            "Enter marketplace source:",
            "Examples:",
            " - owner/repo (GitHub)",
            " - git@github.com:owner/repo.git (SSH)",
            " - https://example.com/marketplace.json",
            " - ./path/to/marketplace",
        ]
    )
