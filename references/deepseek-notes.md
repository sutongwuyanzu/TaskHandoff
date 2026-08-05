# DeepSeek Harness (DSH) integration notes

## Why this skill fits DSH

DeepSeek Harness is expected to ship as a coding-agent runtime with plugins/skills/MCP.
Long tasks fail most often because of **session boundaries**, not model IQ:

- user closes chat
- context is compacted
- switch between Flash / Think / different harnesses
- multi-day features with intermittent work

`task-handoff` stores recovery state **in the repo** (`.handoff/`), so any agent that can read files can resume.

## Planned DSH adapter (day-0 support)

When DSH public APIs land:

1. Register skill entry pointing at `SKILL.md`
2. Map slash / skill triggers: `handoff`, `交接`, `接着做`
3. Prefer running `scripts/handoff_cli.py` via shell tool; fallback to direct file R/W
4. On session start hook (if available): auto-`recall` when `.handoff/handoffs/LATEST.md` exists
5. On session end / compact hook: prompt or auto-`save`

No proprietary binary format — only markdown + JSON already defined in `schema.md`.

## Token strategy for DeepSeek models

| Layer | Budget (approx) | Content |
|-------|-----------------|---------|
| Always | ≤ 800 tokens | `MEMORY.md` durable facts |
| Session start | ≤ 2500 tokens | MEMORY + LATEST handoff + todos |
| Full dump | unlimited | history under `handoffs/` |

`recall --budget N` truncates from the bottom when over budget.

## Chinese-first ergonomics

- Section titles stable in English for tooling; body can be zh-CN
- CLI messages bilingual-friendly
- Resume prompt block is copy-paste ready for new chats

## Non-goals

- Cloud sync (users can put repo on git)
- Vector DB memory (optional future MCP)
- Replacing the harness itself
