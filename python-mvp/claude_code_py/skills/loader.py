from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
from typing import Any, Iterable

from claude_code_py.commands.types import PromptCommand, PromptCommandInvocation
from claude_code_py.utils.frontmatter import parse_frontmatter


@dataclass(slots=True)
class SkillDefinition:
    name: str
    description: str
    path: Path
    source: str
    command: PromptCommand


def normalize_string_list(value: object) -> list[str]:
    """Coerce frontmatter list-like values into a string list."""

    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        return [item.strip() for item in stripped.split(",") if item.strip()]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def build_prompt_text(
    body: str,
    *,
    args: str,
    argument_names: list[str],
    base_dir: Path | None,
    session_id: str | None,
    extra_variables: dict[str, str] | None = None,
) -> str:
    """Render a markdown-backed prompt command with a few Claude-style vars."""

    rendered = body
    parsed_args = _split_args(args)

    rendered = rendered.replace("${CLAUDE_SESSION_ID}", session_id or "")
    if base_dir is not None:
        rendered = rendered.replace(
            "${CLAUDE_SKILL_DIR}",
            _portable_path(base_dir),
        )

    for key, value in (extra_variables or {}).items():
        rendered = rendered.replace(f"${{{key}}}", value)

    rendered = _replace_template_var(rendered, "args", args)

    for index, value in enumerate(parsed_args, start=1):
        rendered = rendered.replace(f"${index}", value)

    for name, value in zip(argument_names, parsed_args):
        rendered = _replace_template_var(rendered, name, value)

    return rendered


class SkillLoader:
    """Load markdown-backed skills from config and project directories."""

    def load(
        self,
        *,
        cwd: Path,
        config_home: Path,
        session_id: str | None = None,
    ) -> list[SkillDefinition]:
        definitions: list[SkillDefinition] = []
        locations = [
            ("user", config_home / "skills"),
            ("project", cwd / ".claude" / "skills"),
        ]
        for source, directory in locations:
            definitions.extend(
                self.load_from_directory(
                    directory,
                    source=source,
                    session_id=session_id,
                )
            )
        return definitions

    def load_from_directory(
        self,
        directory: Path,
        *,
        source: str = "skills",
        session_id: str | None = None,
    ) -> list[SkillDefinition]:
        if not directory.exists():
            return []

        skills: list[SkillDefinition] = []
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            definition = self._load_skill_file(
                skill_file,
                skill_name=entry.name,
                source=source,
                session_id=session_id,
            )
            if definition is not None:
                skills.append(definition)
        return skills

    def _load_skill_file(
        self,
        skill_file: Path,
        *,
        skill_name: str,
        source: str,
        session_id: str | None,
    ) -> SkillDefinition | None:
        document = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        metadata = document.metadata

        user_invocable = _parse_frontmatter_bool(
            metadata.get("user-invocable"),
            True,
        )
        if not user_invocable:
            return None

        description = str(
            metadata.get("description")
            or _extract_description(document.body)
            or f"Loaded from {skill_file.name}"
        ).strip()
        display_name = str(metadata.get("name") or skill_name).strip()
        argument_hint = _optional_string(metadata.get("argument-hint"))
        argument_names = normalize_string_list(metadata.get("arguments"))
        allowed_tools = normalize_string_list(
            metadata.get("allowed-tools") or metadata.get("allowed_tools")
        )
        context = "fork" if str(metadata.get("context", "")).strip() == "fork" else "inline"
        progress_message = str(metadata.get("progress-message") or "running").strip()

        def loader(args: str) -> PromptCommandInvocation:
            prompt_body = build_prompt_text(
                document.body,
                args=args,
                argument_names=argument_names,
                base_dir=skill_file.parent,
                session_id=session_id,
            )
            prompt = (
                f"Base directory for this skill: {_portable_path(skill_file.parent)}\n\n"
                f"{prompt_body}"
            )
            return PromptCommandInvocation(
                prompt=prompt,
                description=_build_invocation_description(display_name, args, description),
                context=context,
                allowed_tools=allowed_tools or None,
            )

        command = PromptCommand(
            name=skill_name,
            description=description,
            progress_message=progress_message,
            context=context,
            allowed_tools=allowed_tools or None,
            argument_hint=argument_hint,
            source="skills",
            loader=loader,
        )
        return SkillDefinition(
            name=display_name,
            description=description,
            path=skill_file,
            source=source,
            command=command,
        )


def _split_args(args: str) -> list[str]:
    if not args.strip():
        return []
    try:
        return shlex.split(args)
    except ValueError:
        return args.split()


def _portable_path(path: Path) -> str:
    return path.resolve().as_posix()


def _replace_template_var(text: str, key: str, value: str) -> str:
    return text.replace(f"{{{{{key}}}}}", value).replace(f"{{{key}}}", value)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(item).strip() for item in value if str(item).strip())
    else:
        text = str(value).strip()
    return text or None


def _extract_description(body: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line:
            return line[:120]
    return ""


def _build_invocation_description(name: str, args: str, fallback: str) -> str:
    stripped_args = args.strip()
    if stripped_args:
        return f"/{name} {stripped_args}"
        return fallback or f"/{name}"


def _parse_frontmatter_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}
