# task-handoff data contract

Version: 1

## Directory

```text
.handoff/
  config.json
  MEMORY.md
  todos.json
  decisions.jsonl
  handoffs/
    LATEST.md
    LATEST.json
    <YYYYMMDDTHHMMSSZ>.md
  sessions/          # optional raw dumps
```

## config.json

| Field | Type | Description |
|-------|------|-------------|
| version | number | schema version, currently `1` |
| project_id | string | short id (default: folder name) |
| language | string | preferred handoff language, e.g. `zh-CN` |
| token_budget_recall | number | default recall budget |
| created_at | string | ISO-8601 UTC |

## todos.json

```json
{
  "version": 1,
  "updated_at": "2026-08-05T00:00:00Z",
  "items": [
    {"id": "n1", "text": "Implement X", "status": "pending"}
  ]
}
```

`status`: `pending` | `doing` | `done` | `blocked`

## decisions.jsonl

One JSON object per line:

```json
{"ts": "2026-08-05T00:00:00Z", "decision": "Use pnpm instead of npm"}
```

## LATEST.json (machine sidecar)

```json
{
  "version": 1,
  "created_at": "...",
  "goal": "...",
  "next_actions": ["...", "...", "..."],
  "branch": "main",
  "head": "abc1234",
  "dirty_summary": "clean",
  "path": ".handoff/handoffs/2026....md"
}
```

## Design principles

1. **Portable** — plain files, no DB, works offline
2. **Agent-readable** — markdown first, JSON for tools
3. **Token-thrifty** — fixed section order, bullets over prose
4. **Harness-agnostic** — same contract for DSH / Claude Code / Codex
