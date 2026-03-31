from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FrontmatterDocument:
    metadata: dict[str, object]
    body: str


def parse_frontmatter(raw_text: str) -> FrontmatterDocument:
    """Parse a small YAML-like frontmatter subset used by skills/plugins."""

    if not raw_text.startswith("---\n"):
        return FrontmatterDocument(metadata={}, body=raw_text)

    end_marker = raw_text.find("\n---\n", 4)
    if end_marker == -1:
        end_marker = raw_text.find("\n---", 4)
    if end_marker == -1:
        return FrontmatterDocument(metadata={}, body=raw_text)

    header = raw_text[4:end_marker]
    body = raw_text[end_marker + 5 :]
    return FrontmatterDocument(metadata=_parse_mapping(header.splitlines()), body=body)


def _parse_mapping(lines: list[str]) -> dict[str, object]:
    metadata: dict[str, object] = {}
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if ":" not in stripped:
            index += 1
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, remainder = stripped.split(":", 1)
        key = key.strip()
        value = remainder.lstrip()

        if value in {"|", ">"}:
            next_index, block_lines = _collect_child_lines(lines, index + 1, indent)
            block_text = _dedent_lines(block_lines)
            if value == ">":
                block_text = " ".join(
                    line.strip() for line in block_text.splitlines() if line.strip()
                )
            metadata[key] = block_text
            index = next_index
            continue

        if value == "":
            next_index, child_lines = _collect_child_lines(lines, index + 1, indent)
            if not child_lines:
                metadata[key] = ""
            else:
                metadata[key] = _parse_nested_value(child_lines)
            index = next_index
            continue

        metadata[key] = _coerce_scalar(value)
        index += 1

    return metadata


def _collect_child_lines(
    lines: list[str],
    start_index: int,
    parent_indent: int,
) -> tuple[int, list[str]]:
    child_lines: list[str] = []
    index = start_index
    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped:
            child_lines.append(raw_line)
            index += 1
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent <= parent_indent:
            break
        child_lines.append(raw_line)
        index += 1
    return index, child_lines


def _parse_nested_value(lines: list[str]) -> object:
    dedented = _dedent_lines(lines)
    nested_lines = dedented.splitlines()
    if not nested_lines:
        return ""

    first_non_empty = next((line for line in nested_lines if line.strip()), "")
    if first_non_empty.startswith("- "):
        return _parse_list(nested_lines)
    if ":" in first_non_empty:
        return _parse_mapping(nested_lines)
    return dedented.strip()


def _parse_list(lines: list[str]) -> list[object]:
    items: list[object] = []
    current: list[str] = []

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            if current:
                current.append("")
            continue
        if stripped.startswith("- "):
            if current:
                items.append(_parse_list_item(current))
            current = [stripped[2:]]
            continue
        current.append(raw_line)

    if current:
        items.append(_parse_list_item(current))
    return items


def _parse_list_item(lines: list[str]) -> object:
    if len(lines) == 1:
        return _coerce_scalar(lines[0].strip())
    return _parse_nested_value(lines)


def _dedent_lines(lines: list[str]) -> str:
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return ""
    margin = min(len(line) - len(line.lstrip(" ")) for line in non_empty)
    return "\n".join(line[margin:] if line.strip() else "" for line in lines)


def _coerce_scalar(raw_value: str) -> object:
    value = raw_value.strip().strip("'\"")
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(item) for item in inner.split(",")]
    if "," in value and not value.startswith(("http://", "https://")):
        return [part.strip().strip("'\"") for part in value.split(",")]
    if value.isdigit():
        return int(value)
    return value
