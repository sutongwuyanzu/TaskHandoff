# Changelog

## 0.2.5

- Soften README/SKILL claims: recover structured state (proven) vs LLM always finishes (not claimed)
- Fix skill-install commands to copy-paste cleanly on Windows/macOS

## 0.2.4

- Strengthen continuity suite (`tests/test_continuity.py`):
  - real `session_end.py` → `session_start.py` hook loop
  - `save --auto` goal/next inheritance + git change signals
  - resume-and-complete toy `/health` without LLM
  - stricter assertions: order, count=3, json≡md, budget, decision/blocked
- README “Continuity evidence” near top; docs refresh

## 0.2.3

- README terminal demo GIF: `assets/terminal-demo.gif`
- Regenerator: `python scripts/render_terminal_gif.py` (Pillow)
- How-to: `examples/how-to-record-gif.md` (script / ScreenToGif / VHS)
- Optional VHS tape: `examples/demo.tape`

## 0.2.2

- Session lifecycle **hook samples** under `examples/hooks/`
  - `session_start.py` / `session_end.py` (cross-platform)
  - Claude Code `settings.fragment.json` (SessionStart / SessionEnd / PreCompact)
  - Generic Codex wrapper + Cursor / DSH mapping notes
- Docs: `references/hooks.md`
- Tests: `tests/test_hooks.py`

## 0.2.1

- GitHub Actions CI (Python 3.9 / 3.12)
- `handoff info` — version + install paths
- Skill install scripts: `scripts/install-skill.ps1` / `install-skill.sh`
- Terminal demo: `examples/terminal-demo.md`
- Dogfood: commit `.handoff/` for this repo
- `init` writes `.handoff/.gitignore` for local dumps / key files

## 0.2.0

- Pure-stdlib **MCP stdio server** (`handoff-mcp` / `python -m taskhandoff.mcp_server`)
- Tools: init / save / recall / status / memory_append / doctor
- Sample MCP client config under `examples/mcp-config.sample.json`
- MCP unit tests (`tests/test_mcp_stdio.py`)

## 0.1.0

- Initial Skill + CLI (`handoff`)
- `.handoff/` portable contract
- `save --auto`, `recall --brief`, secret scan, `doctor`
- pytest contract tests
