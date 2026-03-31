# Python Port

This directory is a Python port of the recovered Claude Code flow, with the
implementation pushed toward the recovered source layout and command/tool surface.

It keeps the same core control flow:

1. User prompt enters a REPL or CLI entrypoint
2. `QueryEngine` appends a user message
3. `query_loop()` calls the model client
4. The model either returns text or `tool_use` blocks
5. Tool calls run through the registry and permission policy
6. Tool results are appended as messages
7. The loop continues until the assistant produces plain text
8. `AgentTool` can recursively launch another `QueryEngine`

## Source Mapping

- `src/entrypoints/cli.tsx` -> `claude_code_py/cli.py`
- `src/QueryEngine.ts` -> `claude_code_py/engine/query_engine.py`
- `src/query.ts` -> `claude_code_py/engine/query_loop.py`
- `src/tools.ts` -> `claude_code_py/tools/registry.py` and `claude_code_py/tools/defaults.py`
- `src/services/tools/toolExecution.ts` -> `claude_code_py/engine/query_loop.py`
- `src/tools/AgentTool/AgentTool.tsx` -> `claude_code_py/tools/agent.py`
- `src/tools/AgentTool/runAgent.ts` -> `claude_code_py/engine/query_engine.py`
- `src/hooks/useCanUseTool.tsx` and `src/utils/permissions/*` -> `claude_code_py/permissions/policy.py`

## Included

- A persistent conversation-level `QueryEngine`
- A tool registry with schemas
- A simplified permission policy
- Persistent session storage with `/clear` and `/resume`
- Slash command routing for built-ins, skills, and plugin commands
- `Bash`, `Read`, `Edit`, `Write`, `Glob`, `Grep`, and `Agent` tools
- Background subagent tasks with a task manager
- A stub model client for offline testing
- An optional Anthropics SDK adapter for real API calls
- Markdown-backed skills from `~/.claude-code-py/skills` and `./.claude/skills`
- Markdown-backed plugins from `~/.claude-code-py/plugins` and `./.claude/plugins`

## Not Included Yet

- Streaming token deltas
- MCP transport and auth
- Plugin marketplace and remote plugin installation
- Rich Ink-style terminal UI
- Full Claude Code frontmatter surface and hook execution
- Worktrees, bridge mode, tmux, or remote execution

## Quick Start

Use the offline stub model:

```bash
cd python-mvp
python -m claude_code_py repl
```

Useful stub prompts:

- `read /absolute/path/to/README.md`
- `bash: dir`
- `edit /absolute/path/to/scratch.txt|hello|world`
- `agent: summarize the current directory`
- `/help`
- `/clear`
- `/resume`
- `/skills`
- `/tasks`
- `/plugin`

Skill and plugin directories:

- User skills: `~/.claude-code-py/skills/<skill-name>/SKILL.md`
- Project skills: `./.claude/skills/<skill-name>/SKILL.md`
- User plugins: `~/.claude-code-py/plugins/<plugin-name>/...`
- Project plugins: `./.claude/plugins/<plugin-name>/...`

Use the Anthropic SDK adapter:

```bash
pip install -e .[anthropic]
set ANTHROPIC_API_KEY=...
python -m claude_code_py repl --client anthropic
```

## Design Notes

- The port defaults to standard library only.
- The Anthropics adapter is best-effort and isolated behind a protocol.
- The `RuleBasedModelClient` exists so we can exercise the agent loop without
  needing network access or a live API key.
