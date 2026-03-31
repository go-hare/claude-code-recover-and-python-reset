from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from typing import Any

from claude_code_py.engine.context import ToolContext
from claude_code_py.engine.models import ToolRunResult
from claude_code_py.tools.base import Tool

DEFAULT_HEAD_LIMIT = 250
TYPE_TO_GLOB = {
    "py": "**/*.py",
    "js": "**/*.js",
    "ts": "**/*.ts",
    "tsx": "**/*.tsx",
    "jsx": "**/*.jsx",
    "md": "**/*.md",
    "json": "**/*.json",
    "java": "**/*.java",
    "go": "**/*.go",
    "rust": "**/*.rs",
}


class GrepTool(Tool):
    name = "Grep"
    description = "A powerful search tool built on ripgrep"
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regular expression pattern to search for in file contents.",
            },
            "path": {
                "type": "string",
                "description": "File or directory to search in. Defaults to current working directory.",
            },
            "glob": {
                "type": "string",
                "description": "Glob pattern to filter files.",
            },
            "output_mode": {
                "type": "string",
                "description": 'Output mode: "content", "files_with_matches", or "count".',
            },
            "-B": {"type": "integer", "description": "Lines of context before each match."},
            "-A": {"type": "integer", "description": "Lines of context after each match."},
            "-C": {"type": "integer", "description": "Alias for context."},
            "context": {
                "type": "integer",
                "description": "Lines of context before and after each match.",
            },
            "-n": {
                "type": "boolean",
                "description": "Show line numbers in content mode. Defaults to true.",
            },
            "-i": {"type": "boolean", "description": "Case insensitive search."},
            "type": {"type": "string", "description": "Common file type filter."},
            "head_limit": {
                "type": "integer",
                "description": "Limit output to the first N entries.",
            },
            "offset": {
                "type": "integer",
                "description": "Skip the first N entries before applying head_limit.",
            },
            "multiline": {
                "type": "boolean",
                "description": "Allow matches to span multiple lines.",
            },
        },
        "required": ["pattern"],
    }

    async def run(
        self,
        tool_input: Mapping[str, Any],
        context: ToolContext,
    ) -> ToolRunResult:
        pattern_text = str(tool_input["pattern"])
        target = context.resolve_path(str(tool_input.get("path", ".")))
        output_mode = str(tool_input.get("output_mode", "files_with_matches"))
        ignore_case = bool(tool_input.get("-i", False))
        show_line_numbers = bool(tool_input.get("-n", True))
        before = _coerce_int(tool_input.get("-B"))
        after = _coerce_int(tool_input.get("-A"))
        full_context = _coerce_int(tool_input.get("context"))
        context_alias = _coerce_int(tool_input.get("-C"))
        head_limit = _coerce_int(tool_input.get("head_limit"))
        offset = max(_coerce_int(tool_input.get("offset")) or 0, 0)
        multiline = bool(tool_input.get("multiline", False))
        file_glob = _resolve_glob(
            raw_glob=tool_input.get("glob"),
            file_type=tool_input.get("type"),
        )

        if full_context is None:
            full_context = context_alias
        if full_context is not None:
            before = full_context
            after = full_context
        before = before or 0
        after = after or 0

        if not target.exists():
            return ToolRunResult(content=f"Path does not exist: {target}", is_error=True)

        flags = re.MULTILINE
        if ignore_case:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.DOTALL
        pattern = re.compile(pattern_text, flags)

        candidates = _resolve_candidates(target, file_glob)

        content_lines: list[str] = []
        file_counts: dict[str, int] = {}
        mtimes: dict[str, float] = {}

        for file_path in candidates:
            relative = (
                file_path.relative_to(target).as_posix()
                if target.is_dir()
                else file_path.name
            )
            mtimes[relative] = file_path.stat().st_mtime

            try:
                raw_text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            if multiline:
                match_count, entries = _search_multiline(
                    relative=relative,
                    content=raw_text,
                    pattern=pattern,
                    show_line_numbers=show_line_numbers,
                )
            else:
                match_count, entries = _search_lines(
                    relative=relative,
                    lines=raw_text.splitlines(),
                    pattern=pattern,
                    before=before,
                    after=after,
                    show_line_numbers=show_line_numbers,
                )

            if match_count:
                file_counts[relative] = match_count
                content_lines.extend(entries)

        if output_mode == "content":
            if not content_lines:
                return ToolRunResult(content="No matches found")
            items, applied_limit = _apply_head_limit(content_lines, head_limit, offset)
            output = "\n".join(items)
            suffix = _format_limit_suffix(applied_limit, offset)
            if suffix:
                output = f"{output}\n\n{suffix}"
            return ToolRunResult(content=output[: context.max_output_chars])

        if output_mode == "count":
            if not file_counts:
                return ToolRunResult(content="No matches found")
            lines = [f"{file_name}:{file_counts[file_name]}" for file_name in sorted(file_counts)]
            items, applied_limit = _apply_head_limit(lines, head_limit, offset)
            output = "\n".join(items)
            total_matches = sum(int(item.rsplit(":", 1)[1]) for item in items)
            suffix = f"\n\nFound {total_matches} total occurrences across {len(items)} files."
            limit_suffix = _format_limit_suffix(applied_limit, offset)
            if limit_suffix:
                suffix = f"{suffix} {limit_suffix}"
            return ToolRunResult(content=(output + suffix)[: context.max_output_chars])

        if not file_counts:
            return ToolRunResult(content="No files found")

        ordered_files = sorted(file_counts, key=lambda file_name: mtimes[file_name], reverse=True)
        items, applied_limit = _apply_head_limit(ordered_files, head_limit, offset)
        header = f"Found {len(items)} files"
        limit_suffix = _format_limit_suffix(applied_limit, offset)
        if limit_suffix:
            header = f"{header} {limit_suffix}"
        output = header + "\n" + "\n".join(items)
        return ToolRunResult(content=output[: context.max_output_chars])


def _coerce_int(raw: object) -> int | None:
    if raw is None:
        return None
    return int(raw)


def _resolve_glob(*, raw_glob: object, file_type: object) -> str:
    if raw_glob is not None:
        return str(raw_glob)
    if file_type is not None:
        return TYPE_TO_GLOB.get(str(file_type), "**/*")
    return "**/*"


def _resolve_candidates(target: Path, file_glob: str) -> list[Path]:
    if target.is_file():
        return [target]
    return [path for path in target.glob(file_glob) if path.is_file()]


def _search_lines(
    *,
    relative: str,
    lines: list[str],
    pattern: re.Pattern[str],
    before: int,
    after: int,
    show_line_numbers: bool,
) -> tuple[int, list[str]]:
    match_count = 0
    entries: list[str] = []
    emitted: set[int] = set()
    for index, line in enumerate(lines):
        if not pattern.search(line):
            continue
        match_count += 1
        start = max(index - before, 0)
        end = min(index + after, len(lines) - 1)
        for context_index in range(start, end + 1):
            if context_index in emitted:
                continue
            emitted.add(context_index)
            prefix = f"{relative}:"
            if show_line_numbers:
                prefix = f"{prefix}{context_index + 1}:"
            entries.append(f"{prefix} {lines[context_index]}")
    return match_count, entries


def _search_multiline(
    *,
    relative: str,
    content: str,
    pattern: re.Pattern[str],
    show_line_numbers: bool,
) -> tuple[int, list[str]]:
    entries: list[str] = []
    match_count = 0
    line_starts = [0]
    for index, character in enumerate(content):
        if character == "\n":
            line_starts.append(index + 1)

    for match in pattern.finditer(content):
        match_count += 1
        start_line = 1
        if show_line_numbers:
            start_offset = match.start()
            start_line = 1
            for line_number, line_start in enumerate(line_starts, start=1):
                if line_start > start_offset:
                    break
                start_line = line_number
        prefix = f"{relative}:"
        if show_line_numbers:
            prefix = f"{prefix}{start_line}:"
        entries.append(f"{prefix} {match.group(0)}")
    return match_count, entries


def _apply_head_limit(
    items: list[str],
    limit: int | None,
    offset: int,
) -> tuple[list[str], int | None]:
    if limit == 0:
        return items[offset:], None
    effective_limit = limit or DEFAULT_HEAD_LIMIT
    sliced = items[offset : offset + effective_limit]
    was_truncated = len(items) - offset > effective_limit
    return sliced, effective_limit if was_truncated else None


def _format_limit_suffix(limit: int | None, offset: int) -> str:
    parts: list[str] = []
    if limit is not None:
        parts.append(f"limit: {limit}")
    if offset:
        parts.append(f"offset: {offset}")
    if not parts:
        return ""
    return f"[Showing results with pagination = {', '.join(parts)}]"
