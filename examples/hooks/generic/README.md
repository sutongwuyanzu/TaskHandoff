# Generic harness / shell integration

Claude Code has first-class hooks (see [`../claude-code/`](../claude-code/)).  
Other hosts can still use the same Python scripts.

## Codex / OpenAI-style CLI

If the tool supports “startup command” or “session wrapper”:

```bash
# before agent loop
python /path/to/TaskHandoff/examples/hooks/session_start.py

# after agent loop / trap EXIT
python /path/to/TaskHandoff/examples/hooks/session_end.py
```

Example bash wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail
export HANDOFF_ROOT="${HANDOFF_ROOT:-$(pwd)}"
python /path/to/TaskHandoff/examples/hooks/session_start.py || true
trap 'python /path/to/TaskHandoff/examples/hooks/session_end.py || true' EXIT
# codex / your agent command here
"$@"
```

## Cursor

Cursor has no universal SessionEnd API. Practical pattern:

1. Install TaskHandoff Skill + MCP.
2. Project rule / user rule:  
   - On open / “continue” → call MCP `handoff_recall` or run skill.  
   - On “handoff” / end of day → `handoff_save`.
3. Optional: run `session_start.py` from a task in `.vscode/tasks.json`.

## DeepSeek Harness (DSH)

When DSH exposes lifecycle hooks (start / end / compact):

| DSH event (conceptual) | Map to |
|------------------------|--------|
| session start / resume | `session_start.py` or MCP `handoff_recall` |
| before context compact | same as start |
| session end / stop | `session_end.py` or MCP `handoff_save(auto=true)` |

No proprietary format — only `.handoff/` files.

## Git optional helper

Not a session hook, but useful as a **manual checkpoint** before push:

```bash
# examples/hooks/generic/pre-push-hint.sh
echo "Reminder: handoff save --auto before long break"
handoff status --root . || true
```

Do **not** force-save in pre-commit by default (can surprise teammates); prefer SessionEnd.
