from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from claude_code_py.engine.models import (
    AssistantMessage,
    ConversationMessage,
    TextBlock,
    ToolResultMessage,
    ToolSchema,
    ToolUseBlock,
    UserMessage,
)


class RuleBasedModelClient:
    """Offline model that exercises the agent loop without network access."""

    async def create_assistant_message(
        self,
        *,
        system_prompt: str,
        messages: list[ConversationMessage],
        tools: list[ToolSchema],
        model: str,
        max_output_tokens: int,
    ) -> AssistantMessage:
        _ = (system_prompt, tools, model, max_output_tokens)
        last_message = messages[-1]
        request_id = str(uuid4())

        if isinstance(last_message, ToolResultMessage):
            prefix = "Tool failed" if last_message.is_error else "Tool completed"
            return AssistantMessage(
                blocks=[TextBlock(text=f"{prefix}:\n{last_message.content}")],
                request_id=request_id,
            )

        if not isinstance(last_message, UserMessage):
            return AssistantMessage(
                blocks=[TextBlock(text="I need a user message to continue.")],
                request_id=request_id,
            )

        prompt = last_message.content.strip()
        actionable_prompt = _extract_actionable_prompt(prompt)
        lower = actionable_prompt.lower()

        if lower.startswith("read "):
            return AssistantMessage(
                blocks=[
                    ToolUseBlock(
                        id=str(uuid4()),
                        name="Read",
                        input={"file_path": actionable_prompt[5:].strip()},
                    )
                ],
                request_id=request_id,
            )

        if lower.startswith("bash:") or actionable_prompt.startswith("!"):
            command = (
                actionable_prompt[5:].strip()
                if lower.startswith("bash:")
                else actionable_prompt[1:].strip()
            )
            return AssistantMessage(
                blocks=[
                    ToolUseBlock(
                        id=str(uuid4()),
                        name="Bash",
                        input={"command": command},
                    )
                ],
                request_id=request_id,
            )

        if lower.startswith("edit "):
            payload = actionable_prompt[5:]
            try:
                path, old_text, new_text = payload.split("|", 2)
            except ValueError:
                return AssistantMessage(
                    blocks=[
                        TextBlock(text="Stub edit syntax: edit path|old_text|new_text")
                    ],
                    request_id=request_id,
                )
            return AssistantMessage(
                blocks=[
                    ToolUseBlock(
                        id=str(uuid4()),
                        name="Edit",
                        input={
                            "file_path": path.strip(),
                            "old_string": old_text,
                            "new_string": new_text,
                        },
                    )
                ],
                request_id=request_id,
            )

        if lower.startswith("agent:"):
            child_prompt = actionable_prompt.partition(":")[2].strip()
            return AssistantMessage(
                blocks=[
                    ToolUseBlock(
                        id=str(uuid4()),
                        name="Agent",
                        input={
                            "prompt": child_prompt,
                            "description": "Delegated task",
                            "run_in_background": False,
                        },
                    )
                ],
                request_id=request_id,
            )

        return AssistantMessage(
            blocks=[
                TextBlock(
                    text=(
                        "Stub model reply.\n"
                        f"You said: {prompt}\n\n"
                        "Try one of:\n"
                        f"- read {Path.cwd() / 'README.md'}\n"
                        "- bash: dir\n"
                        f"- edit {Path.cwd() / 'scratch.txt'}|hello|world\n"
                        "- agent: summarize this project"
                    )
                )
            ],
            request_id=request_id,
        )


def _extract_actionable_prompt(prompt: str) -> str:
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("base directory for this skill:"):
            continue
        return line
    return prompt.strip()
