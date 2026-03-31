"""
Read-only validation for bash commands.

Port of: src/tools/BashTool/readOnlyValidation.ts

Determines whether a command is safe to run in read-only mode
by checking against an allowlist of known read-only commands.
"""

from __future__ import annotations

from typing import Any

COMMAND_ALLOWLIST = frozenset({
    # File viewing
    "cat", "head", "tail", "less", "more", "bat",
    # Search
    "grep", "egrep", "fgrep", "rg", "ag", "ack",
    # File finding
    "find", "fd", "locate", "which", "whereis", "type",
    # File info
    "file", "stat", "wc", "du", "df", "ls", "ll", "la",
    "exa", "eza", "tree", "lsd",
    # Text processing (read-only)
    "sort", "uniq", "cut", "tr", "awk", "sed",  # sed without -i
    "jq", "yq", "xq", "column", "fmt", "fold", "rev",
    "paste", "join", "comm",
    # System info
    "uname", "hostname", "whoami", "id", "groups",
    "date", "uptime", "free", "top", "htop", "ps", "pgrep",
    "lsof", "netstat", "ss",
    # Git (read-only)
    "git status", "git log", "git diff", "git show",
    "git branch", "git remote", "git tag",
    "git rev-parse", "git rev-list", "git ls-files",
    "git ls-tree", "git describe", "git blame",
    "git shortlog", "git stash list", "git config --get",
    # Version/help
    "python --version", "python3 --version",
    "node --version", "npm --version",
    "go version", "cargo --version", "rustc --version",
    "java -version", "javac -version",
    # Path/env
    "pwd", "printenv", "env", "echo",
    # Network (read-only)
    "curl", "wget", "ping", "dig", "nslookup", "host",
})


def check_read_only_constraints(
    command: str,
) -> dict[str, Any]:
    """Check if a command is allowed in read-only mode."""
    cmd = command.strip()
    first_word = cmd.split()[0] if cmd.split() else ""

    if first_word in COMMAND_ALLOWLIST or cmd in COMMAND_ALLOWLIST:
        # Extra check: sed with -i is NOT read-only
        if first_word == "sed" and ("-i" in cmd.split() or "--in-place" in cmd.split()):
            return {"allowed": False, "reason": "sed -i modifies files in place"}
        return {"allowed": True}

    # Check for git read-only subcommands
    if first_word == "git":
        parts = cmd.split()
        if len(parts) >= 2:
            git_cmd = f"git {parts[1]}"
            if git_cmd in COMMAND_ALLOWLIST:
                return {"allowed": True}

    return {
        "allowed": False,
        "reason": f"Command '{first_word}' is not in the read-only allowlist",
    }
