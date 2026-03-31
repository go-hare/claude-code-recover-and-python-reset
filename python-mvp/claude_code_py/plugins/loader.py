from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from claude_code_py.commands.types import PromptCommand, PromptCommandInvocation
from claude_code_py.skills.loader import build_prompt_text, normalize_string_list
from claude_code_py.utils.frontmatter import parse_frontmatter


@dataclass(slots=True)
class PluginDefinition:
    name: str
    path: Path
    commands: list[PromptCommand] = field(default_factory=list)


class PluginLoader:
    """Discover markdown-backed plugin commands and skills."""

    def load(
        self,
        *,
        cwd: Path,
        config_home: Path,
        session_id: str | None = None,
    ) -> list[PluginDefinition]:
        plugins: list[PluginDefinition] = []
        locations = [
            cwd / ".claude" / "plugins",
            config_home / "plugins",
        ]
        for directory in locations:
            plugins.extend(
                self.load_from_directory(directory, session_id=session_id)
            )
        return plugins

    def load_from_directory(
        self,
        directory: Path,
        *,
        session_id: str | None = None,
    ) -> list[PluginDefinition]:
        if not directory.exists():
            return []

        plugins: list[PluginDefinition] = []
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            definition = self._load_plugin(entry, session_id=session_id)
            if definition is not None:
                plugins.append(definition)
        return plugins

    def _load_plugin(
        self,
        plugin_dir: Path,
        *,
        session_id: str | None,
    ) -> PluginDefinition | None:
        manifest = _load_plugin_manifest(plugin_dir)
        if bool(manifest.get("disabled", False)):
            return None

        plugin_name = str(manifest.get("name") or plugin_dir.name).strip()
        commands = []

        command_directories = _resolve_manifest_paths(
            plugin_dir,
            manifest,
            singular_key="commands_dir",
            plural_key="commands_paths",
            fallback="commands",
        )
        skill_directories = _resolve_manifest_paths(
            plugin_dir,
            manifest,
            singular_key="skills_dir",
            plural_key="skills_paths",
            fallback="skills",
        )

        for command_dir in command_directories:
            commands.extend(
                self._load_commands_from_tree(
                    command_dir,
                    plugin_name=plugin_name,
                    plugin_dir=plugin_dir,
                    session_id=session_id,
                )
            )

        for skill_dir in skill_directories:
            commands.extend(
                self._load_skills_from_tree(
                    skill_dir,
                    plugin_name=plugin_name,
                    plugin_dir=plugin_dir,
                    session_id=session_id,
                )
            )

        return PluginDefinition(name=plugin_name, path=plugin_dir, commands=commands)

    def _load_commands_from_tree(
        self,
        root: Path,
        *,
        plugin_name: str,
        plugin_dir: Path,
        session_id: str | None,
    ) -> list[PromptCommand]:
        if not root.exists():
            return []
        markdown_paths = _collect_markdown_commands(root)
        commands: list[PromptCommand] = []
        for file_path in markdown_paths:
            command_name = _plugin_command_name(file_path, root, plugin_name)
            command = _build_plugin_prompt_command(
                file_path,
                command_name=command_name,
                plugin_dir=plugin_dir,
                session_id=session_id,
                is_skill=file_path.name.lower() == "skill.md",
            )
            if command is not None:
                commands.append(command)
        return commands

    def _load_skills_from_tree(
        self,
        root: Path,
        *,
        plugin_name: str,
        plugin_dir: Path,
        session_id: str | None,
    ) -> list[PromptCommand]:
        if not root.exists():
            return []

        commands: list[PromptCommand] = []
        if (root / "SKILL.md").exists():
            command = _build_plugin_prompt_command(
                root / "SKILL.md",
                command_name=f"{plugin_name}:{root.name}",
                plugin_dir=plugin_dir,
                session_id=session_id,
                is_skill=True,
            )
            return [command] if command is not None else []

        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            command = _build_plugin_prompt_command(
                skill_file,
                command_name=f"{plugin_name}:{entry.name}",
                plugin_dir=plugin_dir,
                session_id=session_id,
                is_skill=True,
            )
            if command is not None:
                commands.append(command)
        return commands


def _load_plugin_manifest(plugin_dir: Path) -> dict[str, Any]:
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _resolve_manifest_paths(
    plugin_dir: Path,
    manifest: dict[str, Any],
    *,
    singular_key: str,
    plural_key: str,
    fallback: str,
) -> list[Path]:
    values: list[Path] = []
    singular = manifest.get(singular_key)
    if isinstance(singular, str) and singular.strip():
        values.append(plugin_dir / singular)

    for item in normalize_string_list(manifest.get(plural_key)):
        values.append(plugin_dir / item)

    if not values:
        values.append(plugin_dir / fallback)
    return values


def _collect_markdown_commands(root: Path) -> list[Path]:
    paths: list[Path] = []

    def visit(directory: Path) -> None:
        skill_file = directory / "SKILL.md"
        if skill_file.exists():
            paths.append(skill_file)
            return
        for entry in sorted(directory.iterdir()):
            if entry.is_dir():
                visit(entry)
            elif entry.suffix.lower() == ".md":
                paths.append(entry)

    visit(root)
    return paths


def _plugin_command_name(file_path: Path, root: Path, plugin_name: str) -> str:
    if file_path.name.lower() == "skill.md":
        relative = file_path.parent.relative_to(root)
        parts = relative.parts
    else:
        relative = file_path.relative_to(root).with_suffix("")
        parts = relative.parts
    suffix = ":".join(parts)
    return f"{plugin_name}:{suffix}" if suffix else plugin_name


def _build_plugin_prompt_command(
    file_path: Path,
    *,
    command_name: str,
    plugin_dir: Path,
    session_id: str | None,
    is_skill: bool,
) -> PromptCommand | None:
    document = parse_frontmatter(file_path.read_text(encoding="utf-8"))
    metadata = document.metadata

    if not _parse_frontmatter_bool(metadata.get("user-invocable"), True):
        return None

    description = str(
        metadata.get("description") or _extract_description(document.body) or command_name
    ).strip()
    argument_names = normalize_string_list(metadata.get("arguments"))
    allowed_tools = normalize_string_list(
        metadata.get("allowed-tools") or metadata.get("allowed_tools")
    )
    context = "fork" if str(metadata.get("context", "")).strip() == "fork" else "inline"
    progress_message = str(metadata.get("progress-message") or "running").strip()
    argument_hint = _optional_string(metadata.get("argument-hint"))

    def loader(args: str) -> PromptCommandInvocation:
        prompt_body = build_prompt_text(
            document.body,
            args=args,
            argument_names=argument_names,
            base_dir=file_path.parent if is_skill else None,
            session_id=session_id,
            extra_variables={"CLAUDE_PLUGIN_ROOT": plugin_dir.resolve().as_posix()},
        )
        prompt = prompt_body
        if is_skill:
            prompt = (
                f"Base directory for this skill: {file_path.parent.resolve().as_posix()}\n\n"
                f"{prompt_body}"
            )
        return PromptCommandInvocation(
            prompt=prompt,
            description=f"/{command_name} {args}".strip(),
            context=context,
            allowed_tools=allowed_tools or None,
        )

    return PromptCommand(
        name=command_name,
        description=description,
        progress_message=progress_message,
        context=context,
        allowed_tools=allowed_tools or None,
        argument_hint=argument_hint,
        source="plugin",
        loader=loader,
    )


def _extract_description(body: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line:
            return line[:120]
    return ""


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(item).strip() for item in value if str(item).strip())
    else:
        text = str(value).strip()
    return text or None


def _parse_frontmatter_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}
