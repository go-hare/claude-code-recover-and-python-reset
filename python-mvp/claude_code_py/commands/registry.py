from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from claude_code_py.commands.builtin import get_builtin_commands
from claude_code_py.commands.types import BaseCommand
from claude_code_py.plugins.loader import PluginDefinition, PluginLoader
from claude_code_py.skills.loader import SkillDefinition, SkillLoader

_MISSING = object()


@dataclass(slots=True)
class CommandRegistry:
    """Materialized command catalog built from built-ins, skills, and plugins."""

    cwd: Path
    config_home: Path
    session_id: str | None = None
    skill_loader: SkillLoader = field(default_factory=SkillLoader)
    plugin_loader: PluginLoader = field(default_factory=PluginLoader)
    _skills: list[SkillDefinition] = field(default_factory=list, init=False)
    _plugins: list[PluginDefinition] = field(default_factory=list, init=False)
    _commands: dict[str, BaseCommand] = field(default_factory=dict, init=False)
    _command_list: list[BaseCommand] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.refresh()

    def refresh(
        self,
        *,
        cwd: Path | None = None,
        config_home: Path | None = None,
        session_id: str | None | object = _MISSING,
    ) -> None:
        if cwd is not None:
            self.cwd = cwd
        if config_home is not None:
            self.config_home = config_home
        if session_id is not _MISSING:
            self.session_id = session_id

        self._skills = self.skill_loader.load(
            cwd=self.cwd,
            config_home=self.config_home,
            session_id=self.session_id,
        )
        self._plugins = self.plugin_loader.load(
            cwd=self.cwd,
            config_home=self.config_home,
            session_id=self.session_id,
        )

        lookup: dict[str, BaseCommand] = {}
        ordered: list[BaseCommand] = []
        seen_names: set[str] = set()

        def register(command: BaseCommand) -> None:
            if command.name in seen_names:
                return
            seen_names.add(command.name)
            ordered.append(command)
            for key in [command.name, *getattr(command, "aliases", [])]:
                lookup.setdefault(key, command)

        for command in get_builtin_commands():
            register(command)
        for definition in self._skills:
            register(definition.command)
        for plugin in self._plugins:
            for command in plugin.commands:
                register(command)

        self._commands = lookup
        self._command_list = ordered

    def get(self, name: str) -> BaseCommand | None:
        return self._commands.get(name)

    def list_commands(self) -> list[BaseCommand]:
        return [
            command
            for command in self._command_list
            if not getattr(command, "is_hidden", False)
        ]

    def list_skills(self) -> list[str]:
        return sorted({definition.command.name for definition in self._skills})

    def list_plugins(self) -> list[str]:
        return sorted({plugin.name for plugin in self._plugins})
