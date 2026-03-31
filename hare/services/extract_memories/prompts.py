"""
Prompts for memory extraction.

Port of: src/services/extractMemories/prompts.ts
"""

MEMORY_EXTRACTION_PROMPT = """Analyze the conversation and extract important facts, preferences, and context that should be remembered for future sessions.

Focus on:
- User preferences and working style
- Project-specific conventions and patterns
- Important decisions and their rationale
- Technical constraints and requirements
- Corrections the user has made

Format each memory as a concise, standalone statement."""
