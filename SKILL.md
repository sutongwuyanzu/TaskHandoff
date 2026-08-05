---
name: task-handoff
description: >
  DeepSeek-friendly long-task project memory and cross-session handoff.
  Use when the user says handoff, 交接, 续上, 接着做, 项目记忆, long task,
  resume session, save progress, 跨会话, or when starting a multi-hour /
  multi-day coding task that must survive chat resets. Provides init/save/
  recall/status workflows and compact context packs optimized for coding agents.
---

# task-handoff

You help coding agents **survive session resets**: save durable project memory,
produce portable handoff packs, and reload the minimum context needed to continue
long tasks on DeepSeek Harness, Claude Code, Codex, and similar agents.

## When to activate

- User starts a large / multi-day task
- User says: 交接、handoff、续上、接着做、save progress、resume
- New session in a repo that already has `.handoff/`
- Context is getting long and important decisions risk being lost

## Storage layout (project-local)

All state lives in the **project root** under `.handoff/` (git-friendly, portable):

```text
.handoff/
  config.json           # project id, language, compression prefs
  MEMORY.md             # durable project memory (always prefer loading)
  todos.json            # structured open todos
  decisions.jsonl       # append-only decision log
  sessions/             # optional full session snapshots
  handoffs/
    LATEST.md           # newest handoff pack (agent should load this first)
    <timestamp>.md      # history
```

Never store secrets (API keys, tokens, passwords) in handoff files.

## Core workflow

### 1) Init (once per repo)

```bash
python scripts/handoff_cli.py init --root <project-root>
```

If scripts path is relative to this skill, resolve it from the skill install location.

After init, briefly confirm `.handoff/` exists and show `status`.

### 2) Save / Handoff (end of session or mid-task checkpoint)

When the user asks to handoff, or before context overflow, or after major milestones:

1. Collect facts (do not invent):
   - Goal & success criteria
   - Done / in-progress / blocked
   - Key decisions + why
   - Open questions
   - Relevant files / commands
   - Git branch + dirty summary if available
   - Exact **next 3 actions**
2. Run:

```bash
python scripts/handoff_cli.py save --root <project-root> \
  --goal "..." \
  --summary "..." \
  --next "action1" --next "action2" --next "action3"
```

Or write/update files directly using the templates in `templates/` if the CLI is unavailable.

3. Tell the user the path to `.handoff/handoffs/LATEST.md` and that the next session can `/task-handoff` or say「接着做」.

### 3) Recall (start of session)

On session start, if `.handoff/` exists:

```bash
python scripts/handoff_cli.py recall --root <project-root> --budget 2500
```

Then:

1. Load `MEMORY.md` + `handoffs/LATEST.md` (and todos if present)
2. Restate goal, current status, and next 3 actions in ≤10 bullets
3. Ask only if a critical fact is missing — otherwise continue work immediately

### 4) Status

```bash
python scripts/handoff_cli.py status --root <project-root>
```

## Writing rules (DeepSeek-friendly)

Optimize for **token efficiency** and **tool-using agents**:

| Do | Don't |
|----|--------|
| Short bullets, scannable headings | Long narrative essays |
| Concrete paths, commands, file:line | Vague "fixed some stuff" |
| Explicit next actions | "Continue as needed" |
| Stable section order (templates) | Random structure each time |
| zh or en matching the user | Mixed fluff |

Prefer compact markdown. Target handoff body **≤ 1500 tokens** unless user asks for full dump.

## Section contract for LATEST.md

Always keep this order:

1. `## Meta` — time, branch, agent/model note
2. `## Goal`
3. `## Status` — done / doing / blocked
4. `## Decisions`
5. `## Memory deltas` — what was added to durable memory
6. `## Artifacts` — key files, commands, PRs
7. `## Open questions`
8. `## Next actions` — exactly 3, ordered
9. `## Resume prompt` — one copy-paste block for the next session

## Durable MEMORY.md rules

Update `MEMORY.md` only with facts that should outlive one session:

- Architecture choices
- User preferences (style, package manager, deploy target)
- Non-obvious constraints
- Recurring pitfalls

Do **not** dump transient todos into MEMORY.md (those go in `todos.json` / handoff).

## Integration notes

- **Claude Code / Codex / Cursor-style skills**: this `SKILL.md` is the playbook; run scripts from skill dir or copy skill into the agent's skills path.
- **DeepSeek Harness (DSH)**: treat this as a first-party skill; on DSH release, map the same `.handoff/` contract — no proprietary format.
- **Auto-trigger**: if user opens a repo with `.handoff/handoffs/LATEST.md` and says anything like "continue" / "接着", run **recall** first.

## Examples

**User:** 先做到这里，帮我交接一下  
**You:** save handoff → print path → show next 3 actions

**User:** 接着昨天的做  
**You:** recall → restate status → execute next action #1

**User:** 这个项目以后都用 pnpm，记住  
**You:** append preference to MEMORY.md + confirm

## Safety

- Respect `.gitignore`; ensure `.handoff/` is not ignoring itself unless user wants
- Redact secrets if they appear in git status or logs
- Do not overwrite `MEMORY.md` entirely; merge carefully
