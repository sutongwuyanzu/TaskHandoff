# Project Memory

> Durable facts only. Updated by task-handoff. Keep under ~800 tokens when possible.

## Identity

- **Project**: TaskHandoff
- **One-liner**: Long-task project memory & cross-session handoff for coding agents (DeepSeek / DSH friendly)
- **Primary language / stack**: Python 3.9+, stdlib only

## Preferences

- Package manager: pip
- Style / conventions: compact markdown handoffs; zh body ok, EN section titles for tooling
- Deploy / runtime: local CLI + stdio MCP; no cloud required

## Architecture

- CLI: `taskhandoff.cli` → `handoff`
- MCP: `taskhandoff.mcp_server` → NDJSON JSON-RPC stdio (`handoff-mcp`)
- Skill playbook: `SKILL.md`
- State: project-local `.handoff/` (MEMORY + LATEST + todos + decisions)

## Constraints

- Zero third-party runtime deps (MCP is pure stdlib too)
- Do not store secrets in handoff files

## Pitfalls (do not repeat)

- Prefer `recall --brief` on new sessions (not full dump first)
- Installing optional `mcp` PyPI package is unnecessary — use built-in server
- Windows PowerShell: use `python -m taskhandoff` if `handoff` not on PATH

## Glossary

| Term | Meaning |
|------|---------|
| handoff pack | `.handoff/handoffs/LATEST.md` snapshot for resume |
| brief | short resume restatement for token thrift |
| DSH | DeepSeek Harness |
