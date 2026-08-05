# TaskHandoff

**DeepSeek-friendly long-task project memory & cross-session handoff** for coding agents.

> 长任务做到一半换会话 / 上下文被压掉 / 换模型 —— Agent 忘了目标、决策和下一步。  
> TaskHandoff 把可恢复状态写进仓库 `.handoff/`，任何能读文件的 Harness 都能接着干。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/sutongwuyanzu/TaskHandoff/actions/workflows/ci.yml/badge.svg)](https://github.com/sutongwuyanzu/TaskHandoff/actions/workflows/ci.yml)
[![GitHub](https://img.shields.io/badge/github-sutongwuyanzu%2FTaskHandoff-black)](https://github.com/sutongwuyanzu/TaskHandoff)

| | |
|--|--|
| **Repo** | https://github.com/sutongwuyanzu/TaskHandoff |
| **Skill name** | `task-handoff` |
| **CLI** | `handoff`（`pip install -e .` 后） |
| **MCP** | `handoff-mcp`（纯 stdlib，无额外依赖）见 [references/mcp.md](references/mcp.md) |
| **DSH** | Skill + CLI + MCP 同一 `.handoff/` 契约（见 [references/deepseek-notes.md](references/deepseek-notes.md)） |

---

## 30 秒心智模型

```text
会话 A 干到一半  →  handoff save [--auto]  →  写入 .handoff/
新开会话 / 换模型 →  handoff recall --brief →  执行 Next #1
```

| 文件 | 作用 |
|------|------|
| `.handoff/MEMORY.md` | 长期记忆（偏好、架构、坑） |
| `.handoff/handoffs/LATEST.md` | 上一会话状态 + **下一步 3 条** |
| `.handoff/todos.json` / `decisions.jsonl` | 结构化待办与决策日志 |

---

## 安装（推荐最低完整版）

需要 **Python 3.9+**，**零第三方运行时依赖**。

```bash
git clone https://github.com/sutongwuyanzu/TaskHandoff.git
cd TaskHandoff
pip install -e .

# 验证
handoff --version
# 或
python -m taskhandoff --version
```

### MCP（stdio，零额外依赖）

```bash
pip install -e .
handoff-mcp
# 或
python -m taskhandoff.mcp_server
```

把 stdio server 配进 Claude Desktop / Cursor 等（示例：[examples/mcp-config.sample.json](examples/mcp-config.sample.json)，说明：[references/mcp.md](references/mcp.md)）。

不装包也可以用 CLI：

```bash
python scripts/handoff_cli.py init --root /path/to/project
```

### 装成 Agent Skill

```bash
# 一键脚本（推荐）
# Windows PowerShell:
.\scripts\install-skill.ps1
# macOS / Linux:
./scripts/install-skill.sh

# 或手动
cp -r TaskHandoff ~/.claude/skills/task-handoff
```

装好后对 Agent 说：交接 / 接着做 / handoff。  
`SKILL.md` 是剧本；`handoff` CLI / MCP 是执行层。

---

## 快速演示：init → save → recall

在任意项目里：

```bash
cd /path/to/your-app

# 1) 初始化（每个仓库一次）
handoff init --root .

# 2) 会话结束前交接（推荐 --auto：自动带上 git 变更/最近 commit）
handoff save --root . --auto \
  --goal "Ship JWT auth" \
  --done "Middleware scaffolded" \
  --decision "Refresh token in httpOnly cookie" \
  --next "Finish refresh endpoint" \
  --next "Add 401/403 tests" \
  --next "Document env vars" \
  --memory-delta "Auth: access token memory-only; refresh httpOnly cookie"

# 3) 新会话只读 brief（短、稳、给 Agent 直接开干）
handoff recall --root . --brief

# 4) 需要全文时
handoff recall --root . --budget 2500

# 5) 健康检查（含密钥扫描）
handoff doctor --root .
handoff status --root .
```

### 自然语言（Agent 读 `SKILL.md`）

| 你说 | Agent 应做 |
|------|------------|
| 交接 / handoff | `handoff save`（能加 `--auto` 就加） |
| 接着做 / continue / resume | `handoff recall --brief` → 执行 Next #1 |
| 记住我们用 pnpm | `handoff memory --append "..."` |
| handoff 状态 | `handoff status` / `doctor` |

### 示例交接包

完整样例见 [examples/filled-LATEST.md](examples/filled-LATEST.md)。

`recall --brief` 输出形态：

```text
# Resume brief (TaskHandoff)
- project: `your-app`
- goal: Ship JWT auth
- next:
  1. Finish refresh endpoint
  2. Add 401/403 tests
  3. Document env vars
- instruction: Execute next action #1 now. ...
```

---

## 安全

- **默认拒绝**把疑似密钥写进 handoff（GitHub PAT、JWT、私钥块、常见 `api_key=` 等）
- 误报时才用：`handoff save ... --allow-secrets`（不推荐）
- `handoff doctor` 会扫描已有 `LATEST.md`

---

## 目录结构

```text
TaskHandoff/
  SKILL.md                 # Agent skill 剧本
  taskhandoff/             # 可安装 Python 包（CLI）
  scripts/handoff_cli.py   # 兼容入口
  templates/               # MEMORY / handoff 模板
  references/              # schema + DSH 接入说明
  examples/                # 示例流程与 filled handoff
  tests/                   # pytest 契约测试
  APPLY.md                 # DSH 内测报名文案
  pyproject.toml
```

项目内生成：

```text
your-app/.handoff/
  config.json
  MEMORY.md
  todos.json
  decisions.jsonl
  handoffs/LATEST.md
  handoffs/LATEST.json
```

契约说明：[references/schema.md](references/schema.md)

---

## DeepSeek Harness (DSH)

- 类型：**Skill + CLI + MCP**（同一 `.handoff/` 契约）
- 无私有二进制格式：纯 Markdown + JSON
- Token 预算：`recall --budget` / `--brief`
- 发布日接入计划：[references/deepseek-notes.md](references/deepseek-notes.md)

报名文案：[APPLY.md](APPLY.md)

---

## 更多示例

- 终端抄作业：[examples/terminal-demo.md](examples/terminal-demo.md)
- 真实风格交接包：[examples/filled-LATEST.md](examples/filled-LATEST.md)
- **会话 Hook 样例**：[examples/hooks/](examples/hooks/)（SessionStart → recall，SessionEnd → save）
- 本仓库自用 dogfood：`.handoff/`（`handoff recall --root . --brief`）

## 开发与测试

```bash
pip install -e ".[dev]"
pytest -q
handoff info --root .
```

CI：GitHub Actions 在 `main` 上跑 Python 3.9 / 3.12。

---

## 设计原则

1. **Portable** — 状态在仓库里，不绑云  
2. **Token-thrifty** — 固定章节 + brief  
3. **Harness-agnostic** — Claude Code / Codex / 未来 DSH  
4. **Safe by default** — 密钥扫描  

## Roadmap

- [x] 可安装 CLI（`handoff`）
- [x] `save --auto`（git + 上次 handoff）
- [x] `recall --brief` 固定复述
- [x] 密钥拒绝写入 + `doctor`
- [x] pytest 契约测试
- [x] 纯 stdlib MCP server（同一 `.handoff/` 契约）
- [x] GitHub Actions CI + skill 安装脚本 + 仓库 dogfood
- [x] 会话 hook 样例（Claude Code / generic / DSH 映射）
- [ ] README 终端 GIF（可选）

## License

MIT
