from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

LineEnding = Literal["LF", "CRLF", "CR"]

UTF8_BOM = b"\xef\xbb\xbf"
UTF16LE_BOM = b"\xff\xfe"

LEFT_SINGLE_CURLY_QUOTE = "‘"
RIGHT_SINGLE_CURLY_QUOTE = "’"
LEFT_DOUBLE_CURLY_QUOTE = "“"
RIGHT_DOUBLE_CURLY_QUOTE = "”"


@dataclass(slots=True)
class TextFileContents:
    content: str
    encoding: str
    bom: bytes
    line_ending: LineEnding


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def detect_line_ending(text: str) -> LineEnding:
    if "\r\n" in text:
        return "CRLF"
    if "\r" in text:
        return "CR"
    return "LF"


def read_text_file(path: Path) -> TextFileContents:
    raw = path.read_bytes()
    bom = b""
    encoding = "utf-8"

    if raw.startswith(UTF16LE_BOM):
        bom = UTF16LE_BOM
        encoding = "utf-16le"
        payload = raw[len(UTF16LE_BOM) :]
    elif raw.startswith(UTF8_BOM):
        bom = UTF8_BOM
        payload = raw[len(UTF8_BOM) :]
    else:
        payload = raw

    text = payload.decode(encoding)
    return TextFileContents(
        content=normalize_newlines(text),
        encoding=encoding,
        bom=bom,
        line_ending=detect_line_ending(text),
    )


def write_text_file(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    bom: bytes = b"",
    line_ending: LineEnding | None = None,
) -> None:
    rendered = content
    if line_ending == "CRLF":
        rendered = content.replace("\n", "\r\n")
    elif line_ending == "CR":
        rendered = content.replace("\n", "\r")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bom + rendered.encode(encoding))


def normalize_quotes(text: str) -> str:
    return (
        text.replace(LEFT_SINGLE_CURLY_QUOTE, "'")
        .replace(RIGHT_SINGLE_CURLY_QUOTE, "'")
        .replace(LEFT_DOUBLE_CURLY_QUOTE, '"')
        .replace(RIGHT_DOUBLE_CURLY_QUOTE, '"')
    )


def find_actual_string(file_content: str, search_string: str) -> str | None:
    if search_string in file_content:
        return search_string

    normalized_search = normalize_quotes(search_string)
    normalized_file = normalize_quotes(file_content)
    start = normalized_file.find(normalized_search)
    if start == -1:
        return None
    return file_content[start : start + len(search_string)]


def preserve_quote_style(
    old_string: str,
    actual_old_string: str,
    new_string: str,
) -> str:
    if old_string == actual_old_string:
        return new_string

    has_double_quotes = (
        LEFT_DOUBLE_CURLY_QUOTE in actual_old_string
        or RIGHT_DOUBLE_CURLY_QUOTE in actual_old_string
    )
    has_single_quotes = (
        LEFT_SINGLE_CURLY_QUOTE in actual_old_string
        or RIGHT_SINGLE_CURLY_QUOTE in actual_old_string
    )
    if not has_double_quotes and not has_single_quotes:
        return new_string

    result = new_string
    if has_double_quotes:
        result = _apply_curly_double_quotes(result)
    if has_single_quotes:
        result = _apply_curly_single_quotes(result)
    return result


def apply_edit_to_content(
    original_content: str,
    old_string: str,
    new_string: str,
    *,
    replace_all: bool = False,
) -> str:
    if old_string == "":
        return new_string
    if new_string != "":
        if replace_all:
            return original_content.replace(old_string, new_string)
        return original_content.replace(old_string, new_string, 1)

    strip_trailing_newline = (
        not old_string.endswith("\n")
        and f"{old_string}\n" in original_content
    )
    target = f"{old_string}\n" if strip_trailing_newline else old_string
    if replace_all:
        return original_content.replace(target, new_string)
    return original_content.replace(target, new_string, 1)


def _is_opening_context(chars: list[str], index: int) -> bool:
    if index == 0:
        return True
    previous = chars[index - 1]
    return previous in {" ", "\t", "\n", "\r", "(", "[", "{", "\u2014", "\u2013"}


def _apply_curly_double_quotes(text: str) -> str:
    chars = list(text)
    result: list[str] = []
    for index, char in enumerate(chars):
        if char == '"':
            result.append(
                LEFT_DOUBLE_CURLY_QUOTE
                if _is_opening_context(chars, index)
                else RIGHT_DOUBLE_CURLY_QUOTE
            )
        else:
            result.append(char)
    return "".join(result)


def _apply_curly_single_quotes(text: str) -> str:
    chars = list(text)
    result: list[str] = []
    for index, char in enumerate(chars):
        if char != "'":
            result.append(char)
            continue

        previous = chars[index - 1] if index > 0 else None
        next_char = chars[index + 1] if index < len(chars) - 1 else None
        if (
            previous is not None
            and next_char is not None
            and previous.isalpha()
            and next_char.isalpha()
        ):
            result.append(RIGHT_SINGLE_CURLY_QUOTE)
            continue

        result.append(
            LEFT_SINGLE_CURLY_QUOTE
            if _is_opening_context(chars, index)
            else RIGHT_SINGLE_CURLY_QUOTE
        )
    return "".join(result)
