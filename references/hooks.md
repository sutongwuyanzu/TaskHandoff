# Lifecycle hooks for TaskHandoff

## Why

Long tasks die at **session boundaries** and **context compact**.  
Hooks make recall/save mechanical instead of relying on the model to remember.

## Canonical scripts

Location: [`examples/hooks/`](../examples/hooks/)

| Script | When | Effect |
|--------|------|--------|
| `session_start.py` | session start, resume, pre-compact | print `handoff recall --brief` to stdout |
| `session_end.py` | session end, stop, exit trap | `handoff save --auto` checkpoint |

Both always **exit 0** so the host harness is not blocked.

## Claude Code

See [`examples/hooks/claude-code/`](../examples/hooks/claude-code/).

Events used:

- `SessionStart` — inject brief
- `PreCompact` — re-inject brief before compression
- `SessionEnd` — auto checkpoint

## Generic agents

See [`examples/hooks/generic/`](../examples/hooks/generic/) for Codex wrappers, Cursor rules pattern, and DSH mapping.

## Environment variables

| Variable | Used by | Meaning |
|----------|---------|---------|
| `HANDOFF_ROOT` | both | project root override |
| `HANDOFF_FULL` | start | full recall instead of brief |
| `HANDOFF_BUDGET` | start | token budget when full |
| `HANDOFF_GOAL` | end | goal for auto save |
| `HANDOFF_SUMMARY` | end | summary line |
| `HANDOFF_SKIP` | end | disable auto save |

## Recommended policy

1. **Start** → always brief if `.handoff/` exists  
2. **End** → auto save (user can set `HANDOFF_SKIP=1`)  
3. **Human handoff** still better when ending a major milestone (explicit `save` with real next_actions)  
4. Auto end-save is a **safety net**, not a replacement for a good handoff

## DSH day-0

Ship these scripts unchanged; map DSH lifecycle to the same entrypoints or MCP tools.
