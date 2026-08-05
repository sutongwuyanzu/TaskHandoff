# TaskHandoff

**DeepSeek-friendly long-task project memory & cross-session handoff Skill** for coding agents.

> 解决真实痛点：长任务做到一半换会话 / 上下文被压缩 / 换模型后，Agent 忘了目标、决策和下一步。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](scripts/handoff_cli.py)

**Repo:** https://github.com/sutongwuyanzu/TaskHandoff  
**Skill name:** `task-handoff`（安装目录名 / slash 触发名）

## 30 秒理解

```text
会话 A 干到一半  →  handoff save  →  .handoff/ 写入仓库
新开会话 / 换模型 →  handoff recall →  Agent 接着 Next actions 干
```

## Why

Coding agents are strong in a single chat, weak across **session boundaries**.

TaskHandoff keeps recovery state **inside the repo** (`.handoff/`), so any harness that can read files — Claude Code, Codex, Cursor, and **DeepSeek Harness (DSH)** — can resume the same long task.

| Layer | Purpose |
|-------|---------|
| `MEMORY.md` | Durable project facts (prefs, architecture, pitfalls) |
| `handoffs/LATEST.md` | Last session status + exact next 3 actions |
| `todos.json` / `decisions.jsonl` | Structured machine-readable state |
| `scripts/handoff_cli.py` | `init` / `save` / `recall` / `status` / `memory` |

## Install as a Skill

### Option A — copy into agent skills dir

```bash
git clone https://github.com/sutongwuyanzu/TaskHandoff.git
# Claude Code example
cp -r TaskHandoff ~/.claude/skills/task-handoff

# Or project-local
cp -r TaskHandoff /path/to/your-app/.claude/skills/task-handoff
```

### Option B — use CLI only (any agent with shell)

```bash
git clone https://github.com/sutongwuyanzu/TaskHandoff.git
cd /path/to/your-project
python /path/to/TaskHandoff/scripts/handoff_cli.py init --root .
```

Requires **Python 3.9+** (stdlib only, no pip deps).

## Quick start

```bash
# 1) init once per repo
python scripts/handoff_cli.py init --root /path/to/project

# 2) end of session — save handoff
python scripts/handoff_cli.py save --root /path/to/project \
  --goal "Ship JWT auth" \
  --done "Middleware scaffolded" \
  --decision "Refresh token in httpOnly cookie" \
  --file "src/auth/middleware.ts" \
  --next "Finish refresh endpoint" \
  --next "Add 401/403 tests" \
  --next "Document env vars" \
  --memory-delta "- Auth: access token memory-only; refresh httpOnly cookie"

# 3) new session — recall compact pack
python scripts/handoff_cli.py recall --root /path/to/project --budget 2500

# 4) status
python scripts/handoff_cli.py status --root /path/to/project
```

Natural language (via `SKILL.md` playbook):

| You say | Agent should |
|---------|----------------|
| 交接 / handoff | `save` |
| 接着做 / continue / resume | `recall` then act |
| 记住我们用 pnpm | append `MEMORY.md` |
| handoff status | `status` |

## Layout after init

```text
your-project/
  .handoff/
    config.json
    MEMORY.md
    todos.json
    decisions.jsonl
    handoffs/
      LATEST.md      # load this first on resume
      LATEST.json
      20260805T....md
```

Safe to commit (do **not** put secrets there). See [references/schema.md](references/schema.md).

## DeepSeek Harness (DSH)

Designed for **day-0 DSH support**:

- Universal skill format (`SKILL.md`)
- Portable `.handoff/` contract (markdown + JSON, no DB)
- Token budgets tuned for long-context coding models
- Integration plan: [references/deepseek-notes.md](references/deepseek-notes.md)

We will adapt triggers/hooks as soon as DSH public skill APIs ship.

## Repo structure

```text
TaskHandoff/
  SKILL.md                 # agent playbook (required for skill installs)
  scripts/handoff_cli.py   # CLI
  templates/               # MEMORY / handoff / config templates
  references/              # schema + DSH notes
  examples/                # sample multi-day flow + filled handoff
  APPLY.md                 # DSH 内测报名文案
```

## Design principles

1. **Portable** — plain files in the project
2. **Token-thrifty** — fixed sections, bullets, `recall --budget`
3. **Harness-agnostic** — works before DSH; plugs into DSH on day one
4. **Agent-operable** — CLI + templates; agent can also edit files directly

## Roadmap

- [ ] Optional MCP server wrapping the same contract
- [ ] VS Code / JetBrains “Resume from handoff” button
- [ ] Auto-save hook samples for multiple harnesses
- [ ] Soft merge for concurrent handoffs

## Apply / contribute

Issues and PRs welcome. If you are integrating DSH, open an issue tagged `dsh`.

## License

MIT
