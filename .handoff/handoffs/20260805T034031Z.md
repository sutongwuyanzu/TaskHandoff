# Handoff Pack

## Meta

- **Created**: 2026-08-05T03:40:31Z
- **Branch**: main @ 88e981c
- **Dirty**: 6 changed path(s): askhandoff/cli.py, .github/, .handoff/, examples/terminal-demo.md, scripts/install-skill.ps1, ...
- **Agent note**: task-handoff

## Goal

Polish TaskHandoff for DeepSeek Harness closed-beta apply

## Status

### Done

- v0.2.0 pure-stdlib MCP
- CLI auto/brief/doctor/secret scan
- pytest + GitHub Actions CI
- Small polish batch: CI, install-skill scripts, dogfood, info cmd

### Doing

- uncommitted changes in 6 file(s)

### Blocked

- (none)

## Decisions

- MCP zero extra deps via NDJSON JSON-RPC
- Same .handoff contract for Skill/CLI/MCP

## Memory deltas

- Product stack: Skill + CLI + pure-stdlib MCP

## Artifacts

- **Key files**: taskhandoff/cli.py, taskhandoff/mcp_server.py, SKILL.md, APPLY.md
- **Commands**: (none)
- **Links / PRs**: (none)

## Open questions

- (none)

## Next actions

1. Optional: terminal GIF for README
2. Optional: session-end hook samples
3. Apply to DSH via APPLY.md when ready

## Resume prompt

```text
Continue this project from the handoff pack.
Goal: Polish TaskHandoff for DeepSeek Harness closed-beta apply
Next: 1) Optional: terminal GIF for README 2) Optional: session-end hook samples 3) Apply to DSH via APPLY.md when ready
Read .handoff/MEMORY.md and .handoff/handoffs/LATEST.md first, then execute action 1.
```


## Extra notes

### Recent commits
- `88e981c v0.2.0: pure-stdlib MCP stdio server, zero extra deps.`
- `166cba4 Add optional MCP stdio server over the same handoff contract.`
- `a2e60ba Polish to minimum complete product for DSH apply.`
- `aa8a84f Initial TaskHandoff skill: long-task memory and cross-session handoff.`

### Changed files (git)
- `askhandoff/cli.py`
- `.github/`
- `.handoff/`
- `examples/terminal-demo.md`
- `scripts/install-skill.ps1`
- `scripts/install-skill.sh`
