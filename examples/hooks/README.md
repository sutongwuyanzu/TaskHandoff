# Hook samples — TaskHandoff

Wire **session start → recall** and **session end → save --auto** into your coding agent.

```text
SessionStart / PreCompact  →  session_start.py  →  handoff recall --brief
SessionEnd / Stop / exit   →  session_end.py    →  handoff save --auto
```

## Files

| File | Role |
|------|------|
| [`session_start.py`](session_start.py) | Cross-platform start/compact hook |
| [`session_end.py`](session_end.py) | Cross-platform end/checkpoint hook |
| [`session-start.sh`](session-start.sh) / [`.ps1`](session-start.ps1) | Thin wrappers |
| [`session-end.sh`](session-end.sh) / [`.ps1`](session-end.ps1) | Thin wrappers |
| [`claude-code/`](claude-code/) | Claude Code `settings.json` fragment |
| [`generic/`](generic/) | Codex / Cursor / DSH / shell notes |

## Quick manual test

```bash
pip install -e ../..   # from TaskHandoff repo root: pip install -e .
cd /path/to/your-app
handoff init --root .

python /path/to/TaskHandoff/examples/hooks/session_start.py
python /path/to/TaskHandoff/examples/hooks/session_end.py
handoff status --root .
```

## Design rules

1. Hooks **never fail the host session** (exit 0).
2. Prefer **brief** on start; full pack only with `HANDOFF_FULL=1`.
3. End hook uses **`--auto`** so git dirty files attach without interactive prompts.
4. Same `.handoff/` contract as CLI / MCP / Skill.

Full write-up: [../../references/hooks.md](../../references/hooks.md)
