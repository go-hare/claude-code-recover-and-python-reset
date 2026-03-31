from __future__ import annotations


def parse_slash_command(raw_input: str) -> tuple[str, str] | None:
    """Parse `/name args` into `(name, args)`."""

    if not raw_input.startswith("/"):
        return None
    stripped = raw_input[1:].strip()
    if not stripped:
        return None
    if " " not in stripped:
        return stripped, ""
    name, args = stripped.split(" ", 1)
    return name.strip(), args.strip()
