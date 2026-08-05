# Continuity proof — what is / isn’t proven

## One-liner

**Disk-level continuity across independent processes is automated and CI-gated.**  
**LLM execution quality still requires harness-level evaluation.**

---

## Run the evidence

```bash
pip install -e ".[dev]"
pytest tests/test_continuity.py -q
python scripts/continuity_proof.py
```

All of `tests/test_continuity.py` runs in GitHub Actions via `pytest -q`.

---

## Test matrix

| Test | Proves |
|------|--------|
| `test_session_a_save_session_b_recall_without_history` | New process recovers goal, **ordered** 3 next actions, decision, blocked; `LATEST.json` ≡ `LATEST.md`; tiny budget still keeps goal + next #1 |
| `test_session_end_then_session_start_hook_loop` | **Real** `session_end.py` → new process → `session_start.py` closes the lifecycle |
| `test_session_end_alone_seeds_goal_for_start` | End hook alone can seed a recoverable goal |
| `test_save_auto_inherits_goal_and_git_changes` | README-path `save --auto` inherits goal/next and attaches git change signals |
| `test_resume_and_complete_health_endpoint` | Session B completes next #1 using **only** recovered state (no LLM), smoke assertion passes, file changed |

---

## Proven

```text
Session A  →  handoff save / session_end.py
                ↓
           .handoff/ on disk  (git-friendly)
                ↓  close chat / new process / no history
Session B  →  recall --brief / session_start.py
                ↓
           goal + next[1..3] (+ decisions/blocked on full recall)
                ↓
           deterministic executor can finish next #1 (toy /health)
```

---

## Not proven (on purpose)

| Claim | Why not here |
|-------|----------------|
| Any LLM always finishes the real task | Model + harness eval, not the file contract |
| Better than a human sticky note in all cases | Needs field studies |
| Production multi-week programs | Needs long dogfood |

The module docstring and this page state that boundary explicitly.

---

## Soundbite for reviewers / DSH apply

> We prove **cross-process recovery of goal and next actions from `.handoff/` alone** (including real `session_end` → `session_start` hooks and a no-LLM “complete next #1” toy). We do **not** claim LLM execution quality.
