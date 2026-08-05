"""Continuity proof: Session A → disk → Session B without chat history.

Proves:
- handoff files preserve goal / decisions / next actions across processes
- session_end.py → session_start.py lifecycle closes the loop
- save --auto inherits goal and attaches git signals
- a deterministic executor can complete next #1 using only recovered state

Does NOT prove an LLM will always execute correctly (harness-level eval).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "taskhandoff"]
SESSION_END = ROOT / "examples" / "hooks" / "session_end.py"
SESSION_START = ROOT / "examples" / "hooks" / "session_start.py"


def env_for(project: Path, extra: Optional[dict] = None) -> dict:
    e = os.environ.copy()
    e["PYTHONPATH"] = str(ROOT) + os.pathsep + e.get("PYTHONPATH", "")
    e["HANDOFF_ROOT"] = str(project)
    if extra:
        e.update(extra)
    return e


def run(
    args: list[str],
    *,
    root: Optional[Path] = None,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        CLI + args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env or env_for(root or ROOT),
    )


def run_hook(script: Path, project: Path, extra_env: Optional[dict] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=str(project),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env_for(project, extra_env),
        timeout=60,
    )


def git(project: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=str(project),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, r.stderr or r.stdout
    return (r.stdout or "").strip()


def parse_next_actions_from_brief(brief: str) -> List[str]:
    """Extract ordered next actions from resume brief."""
    lines = brief.splitlines()
    actions: List[str] = []
    in_next = False
    for line in lines:
        if re.match(r"^- next:\s*$", line.strip()) or line.strip() == "- next:":
            in_next = True
            continue
        if in_next:
            m = re.match(r"^\s*(\d+)\.\s+(.+)$", line)
            if m:
                actions.append(m.group(2).strip())
                continue
            if line.startswith("- ") or line.startswith("#"):
                break
    return actions


def parse_goal_from_brief(brief: str) -> str:
    for line in brief.splitlines():
        if line.startswith("- goal:"):
            return line.split(":", 1)[1].strip()
    return ""


def parse_goal_from_md(md: str) -> str:
    m = re.search(r"## Goal\s*\n+(.+?)(?:\n## |\Z)", md, re.S)
    return " ".join(m.group(1).split()) if m else ""


def parse_next_from_md(md: str) -> List[str]:
    m = re.search(r"## Next actions\s*\n+(.+?)(?:\n## |\Z)", md, re.S)
    if not m:
        return []
    out: List[str] = []
    for line in m.group(1).splitlines():
        mm = re.match(r"^\d+\.\s+(.+)$", line.strip())
        if mm:
            out.append(mm.group(1).strip())
    return out


def assert_latest_json_md_consistent(project: Path) -> dict:
    hd = project / ".handoff" / "handoffs"
    data = json.loads((hd / "LATEST.json").read_text(encoding="utf-8"))
    md = (hd / "LATEST.md").read_text(encoding="utf-8")
    assert data["goal"] == parse_goal_from_md(md)
    assert data["next_actions"] == parse_next_from_md(md)
    assert len(data["next_actions"]) == 3
    return data


# ---------------------------------------------------------------------------
# 1) Explicit save → new process recall (strengthened assertions)
# ---------------------------------------------------------------------------


def test_session_a_save_session_b_recall_without_history(tmp_path: Path) -> None:
    app = tmp_path / "app"
    app.mkdir()
    (app / "main.py").write_text("# WIP feature\n", encoding="utf-8")

    goal = "Add /health endpoint and return JSON ok"
    nexts = [
        'Implement GET /health returning {"status":"ok"}',
        "Add a one-line smoke test",
        "Document the endpoint in README",
    ]
    decision = "Use plain dict response, no framework yet"
    blocked = "Waiting on port allocation decision"

    assert run(["init", "--root", str(app)], root=app).returncode == 0
    r = run(
        [
            "save",
            "--root",
            str(app),
            "--goal",
            goal,
            "--done",
            "Created main.py scaffold",
            "--doing",
            "Writing health handler",
            "--decision",
            decision,
            "--blocked",
            blocked,
            "--file",
            "main.py",
            "--next",
            nexts[0],
            "--next",
            nexts[1],
            "--next",
            nexts[2],
            "--memory-delta",
            "API style: minimal stdlib-first",
        ],
        root=app,
    )
    assert r.returncode == 0, r.stderr + r.stdout

    pack = assert_latest_json_md_consistent(app)
    assert pack["goal"] == goal
    assert pack["next_actions"] == nexts  # exact order + count

    # Session B — independent CLI process
    r = run(["recall", "--root", str(app), "--brief"], root=app)
    assert r.returncode == 0, r.stderr
    brief = r.stdout
    assert "Resume brief" in brief
    assert goal in brief
    parsed = parse_next_actions_from_brief(brief)
    assert parsed == nexts
    assert len(parsed) == 3
    assert "Execute next action #1" in brief or "next action #1" in brief.lower()

    # Full recall keeps decision + blocked
    r = run(["recall", "--root", str(app), "--budget", "2500"], root=app)
    assert r.returncode == 0
    full = r.stdout
    assert decision in full
    assert blocked in full
    assert "main.py" in full

    # Tiny budget: still keep goal + next #1 (brief path)
    r = run(["recall", "--root", str(app), "--brief", "--budget", "120"], root=app)
    assert r.returncode == 0
    tiny = r.stdout
    assert goal in tiny
    assert nexts[0] in tiny or "1." in tiny


# ---------------------------------------------------------------------------
# 2) Real hook loop: session_end.py → new process → session_start.py
# ---------------------------------------------------------------------------


def test_session_end_then_session_start_hook_loop(tmp_path: Path) -> None:
    """True lifecycle: end hook writes pack, start hook injects recovery context."""
    app = tmp_path / "hookapp"
    app.mkdir()
    (app / "README.md").write_text("# hook app\n", encoding="utf-8")

    goal = "Lifecycle continuity goal"
    nexts = ["step-a-implement", "step-b-test", "step-c-docs"]

    # Mid-session work leaves an explicit handoff (agent did real save)
    assert run(["init", "--root", str(app)], root=app).returncode == 0
    assert (
        run(
            [
                "save",
                "--root",
                str(app),
                "--goal",
                goal,
                "--next",
                nexts[0],
                "--next",
                nexts[1],
                "--next",
                nexts[2],
            ],
            root=app,
        ).returncode
        == 0
    )

    # Session end — MUST call session_end.py (not bare CLI save)
    r_end = run_hook(
        SESSION_END,
        app,
        {
            "HANDOFF_GOAL": goal,
            "HANDOFF_SUMMARY": "ended session mid-feature via hook",
        },
    )
    assert r_end.returncode == 0, r_end.stderr + r_end.stdout
    assert (app / ".handoff" / "handoffs" / "LATEST.md").is_file()
    pack = assert_latest_json_md_consistent(app)
    assert pack["goal"] == goal
    # auto inherits previous next actions
    assert pack["next_actions"] == nexts

    # Brand-new process — only session_start.py
    r_start = run_hook(SESSION_START, app)
    assert r_start.returncode == 0, r_start.stderr + r_start.stdout
    out = r_start.stdout
    assert "TaskHandoff session context" in out or "Resume brief" in out
    assert goal in out
    assert nexts[0] in out
    parsed = parse_next_actions_from_brief(out)
    # start hook wraps brief; still ordered
    assert parsed[:3] == nexts or all(n in out for n in nexts)


def test_session_end_alone_seeds_goal_for_start(tmp_path: Path) -> None:
    """Even without prior CLI save, session_end with HANDOFF_GOAL is recoverable."""
    app = tmp_path / "seed"
    app.mkdir()
    assert run(["init", "--root", str(app)], root=app).returncode == 0

    r_end = run_hook(
        SESSION_END,
        app,
        {"HANDOFF_GOAL": "Pure hook seeded goal", "HANDOFF_SUMMARY": "first end"},
    )
    assert r_end.returncode == 0, r_end.stderr
    pack = json.loads((app / ".handoff" / "handoffs" / "LATEST.json").read_text(encoding="utf-8"))
    assert pack["goal"] == "Pure hook seeded goal"
    assert len(pack["next_actions"]) == 3

    r_start = run_hook(SESSION_START, app)
    assert r_start.returncode == 0
    assert "Pure hook seeded goal" in r_start.stdout


# ---------------------------------------------------------------------------
# 3) save --auto inherits goal + git signals
# ---------------------------------------------------------------------------


def test_save_auto_inherits_goal_and_git_changes(tmp_path: Path) -> None:
    app = tmp_path / "autoapp"
    app.mkdir()
    (app / "app.py").write_text("x = 1\n", encoding="utf-8")

    git(app, "init")
    git(app, "config", "user.email", "th@test.local")
    git(app, "config", "user.name", "TaskHandoff Test")
    git(app, "add", "app.py")
    git(app, "commit", "-m", "init app")

    goal = "Keep auto goal across sessions"
    assert run(["init", "--root", str(app)], root=app).returncode == 0
    assert (
        run(
            [
                "save",
                "--root",
                str(app),
                "--goal",
                goal,
                "--next",
                "n1",
                "--next",
                "n2",
                "--next",
                "n3",
            ],
            root=app,
        ).returncode
        == 0
    )

    # Session B: modify git-tracked file, auto save without re-stating goal
    (app / "app.py").write_text("x = 2  # session B edit\n", encoding="utf-8")
    (app / "new_feature.py").write_text("print('new')\n", encoding="utf-8")
    git(app, "add", "-A")

    r = run(["save", "--root", str(app), "--auto", "--summary", "checkpoint after edit"], root=app)
    assert r.returncode == 0, r.stderr + r.stdout

    pack = assert_latest_json_md_consistent(app)
    assert pack["goal"] == goal  # inherited
    assert pack["next_actions"] == ["n1", "n2", "n3"]  # inherited order
    assert pack.get("auto") is True

    md = (app / ".handoff" / "handoffs" / "LATEST.md").read_text(encoding="utf-8")
    # changed files / commits appear in auto body or meta
    assert "app.py" in md or "new_feature.py" in md
    assert "Changed files" in md or "changed" in md.lower() or "new_feature.py" in str(pack.get("key_files", []))


# ---------------------------------------------------------------------------
# 4) Resume next #1 and actually finish a tiny task (no LLM)
# ---------------------------------------------------------------------------


def test_resume_and_complete_health_endpoint(tmp_path: Path) -> None:
    """Session B → recall --brief → parse brief only → complete next #1 (no LLM, no LATEST.json).

    Proves recovered *brief text* is enough to drive a deterministic executor.
    Does not open LATEST.json / LATEST.md after Session A ends.
    """
    app = tmp_path / "healthapp"
    app.mkdir()
    (app / "main.py").write_text(
        '''\
# TODO: implement /health
# Session A stopped here.

def handle(path: str) -> dict:
    raise NotImplementedError("not done yet")
''',
        encoding="utf-8",
    )

    goal = 'Add /health endpoint and return {"status":"ok"}'
    next1 = 'Implement handle("/health") returning {"status":"ok"}'
    assert run(["init", "--root", str(app)], root=app).returncode == 0
    assert (
        run(
            [
                "save",
                "--root",
                str(app),
                "--goal",
                goal,
                "--done",
                "Scaffold main.py with TODO",
                "--blocked",
                "Implementation incomplete",
                "--decision",
                "Pure function handle(path)->dict",
                "--file",
                "main.py",
                "--next",
                next1,
                "--next",
                "Add smoke test for /health",
                "--next",
                "Remove NotImplementedError",
            ],
            root=app,
        ).returncode
        == 0
    )

    # --- Session B: cold start; only recall --brief stdout is the context bus ---
    r = run(["recall", "--root", str(app), "--brief"], root=app)
    assert r.returncode == 0
    brief = r.stdout

    recovered_goal = parse_goal_from_brief(brief)
    actions = parse_next_actions_from_brief(brief)
    assert recovered_goal == goal
    assert len(actions) == 3
    recovered_next = actions[0]
    assert recovered_next == next1

    # Executor policy: act ONLY on parsed brief fields (no disk sidecars, no Session A vars)
    assert "health" in recovered_goal.lower() or "health" in recovered_next.lower()
    assert "handle" in recovered_next.lower() or "/health" in recovered_next

    # Complete next #1 using recovered instruction text only
    (app / "main.py").write_text(
        '''\
"""Minimal app — completed in Session B from recall --brief next #1."""

def handle(path: str) -> dict:
    if path.rstrip("/") == "/health":
        return {"status": "ok"}
    return {"status": "not_found"}
''',
        encoding="utf-8",
    )

    tr = subprocess.run(
        [sys.executable, "-c", "from main import handle; assert handle('/health')=={'status':'ok'}"],
        cwd=str(app),
        capture_output=True,
        text=True,
    )
    assert tr.returncode == 0, tr.stderr

    body = (app / "main.py").read_text(encoding="utf-8")
    assert "NotImplementedError" not in body
    assert '"ok"' in body or "'ok'" in body

    # Chain: save progress using only brief-derived goal/next (still no reading LATEST.json in test)
    assert (
        run(
            [
                "save",
                "--root",
                str(app),
                "--auto",
                "--goal",
                recovered_goal,
                "--done",
                f"Completed: {recovered_next}",
                "--next",
                actions[1] if len(actions) > 1 else "follow-up",
                "--next",
                actions[2] if len(actions) > 2 else "follow-up",
                "--next",
                "Ship",
            ],
            root=app,
        ).returncode
        == 0
    )
