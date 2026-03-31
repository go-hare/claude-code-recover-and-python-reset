"""Port of: src/commands/copy.ts"""
from __future__ import annotations
from typing import Any

COMMAND_NAME = "copy"
DESCRIPTION = "Copy the last assistant response to clipboard"
ALIASES: list[str] = []

async def call(args: str, messages: list[dict[str, Any]], **context: Any) -> dict[str, Any]:
    for msg in reversed(messages):
        if msg.get("type") == "assistant":
            content = msg.get("message", {}).get("content", [])
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if text:
                try:
                    import subprocess, sys
                    if sys.platform == "win32":
                        subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
                    elif sys.platform == "darwin":
                        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
                    else:
                        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
                    return {"type": "copy", "display_text": "Copied to clipboard!"}
                except Exception as e:
                    return {"type": "error", "display_text": f"Failed to copy: {e}"}
    return {"type": "error", "display_text": "No assistant message to copy."}
