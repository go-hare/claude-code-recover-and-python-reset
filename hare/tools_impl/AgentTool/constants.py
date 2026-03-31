"""
Agent tool constants.

Port of: src/tools/AgentTool/constants.ts
"""

AGENT_TOOL_NAME = "Agent"
LEGACY_AGENT_TOOL_NAME = "Task"
VERIFICATION_AGENT_TYPE = "verification"

ONE_SHOT_BUILTIN_AGENT_TYPES: frozenset[str] = frozenset({
    "Explore",
    "Plan",
})
