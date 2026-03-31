"""
Hare – Python port of Claude Code CLI v2.1.88 (recovered from sourcemap).

Keeps the same core control flow as the TypeScript original:

1. User prompt enters a REPL or CLI entrypoint
2. QueryEngine appends a user message
3. query_loop() calls the model client
4. The model either returns text or tool_use blocks
5. Tool calls run through the registry and permission policy
6. Tool results are appended as messages
7. The loop continues until the assistant produces plain text
8. AgentTool can recursively launch another QueryEngine
"""

VERSION = "2.1.88"
BUILD_TIME = "recovered-from-sourcemap"
