"""
Shell output limits.

Port of: src/utils/shell/outputLimits.ts
"""

DEFAULT_OUTPUT_LIMIT = 30_000
MAX_OUTPUT_LIMIT = 100_000


def get_output_limit(custom_limit: int = 0) -> int:
    """Get the output limit for shell commands."""
    if custom_limit > 0:
        return min(custom_limit, MAX_OUTPUT_LIMIT)
    return DEFAULT_OUTPUT_LIMIT


def truncate_output(output: str, limit: int = 0) -> str:
    """Truncate output to the limit."""
    max_chars = get_output_limit(limit)
    if len(output) <= max_chars:
        return output
    half = max_chars // 2
    return (
        output[:half]
        + f"\n\n... [{len(output) - max_chars} characters truncated] ...\n\n"
        + output[-half:]
    )
