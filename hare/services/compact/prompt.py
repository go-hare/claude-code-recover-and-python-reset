"""
Compact prompts.

Port of: src/services/compact/prompt.ts
"""

COMPACT_SYSTEM_PROMPT = """You are a conversation summarizer. Your task is to create a concise summary of the conversation so far that preserves all important context, decisions, and progress.

Focus on:
- What task the user is working on
- Key decisions made
- Files modified and why
- Current state of progress
- Any errors encountered and how they were resolved
- Important context that would be needed to continue the work"""


def get_compact_prompt(custom_instructions: str = "") -> str:
    """Get the system prompt for compaction."""
    prompt = COMPACT_SYSTEM_PROMPT
    if custom_instructions:
        prompt += f"\n\nAdditional instructions: {custom_instructions}"
    return prompt


def get_compact_user_summary_message(summary: str) -> str:
    """Format a compact summary as a user message."""
    return f"<conversation_summary>\n{summary}\n</conversation_summary>"


def get_partial_compact_prompt() -> str:
    """Get prompt for partial compaction."""
    return COMPACT_SYSTEM_PROMPT + "\n\nNote: Only summarize the older portion of the conversation. Recent messages will be kept as-is."
