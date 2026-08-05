"""Continuity proof: Session A saves → Session B recalls the same goal/next.

This is mechanical evidence that the handoff pack is sufficient to resume
without chat history. It does not claim an LLM will always execute correctly;
it proves the recovery contract preserves the facts needed to continue.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "taskhandoff"]


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        CLI + args,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_session_a_save_session_b_recall_without_history(tmp_path: Path) -> None:
    """Simulate two independent shells (no shared process state)."""
    app = tmp_path / "app"
    app.mkdir()
    (app / "main.py").write_text("# WIP feature\n", encoding="utf-8")

    # --- Session A: long task mid-way, user closes chat ---
    assert run(["init", "--root", str(app)]).returncode == 0
    r = run(
        [
            "save",
            "--root",
            str(app),
            "--goal",
            "Add /health endpoint and return JSON ok",
            "--done",
            "Created main.py scaffold",
            "--doing",
            "Writing health handler",
            "--decision",
            "Use plain dict response, no framework yet",
            "--file",
            "main.py",
            "--next",
            "Implement GET /health returning {\"status\":\"ok\"}",
            "--next",
            "Add a one-line smoke test",
            "--next",
            "Document the endpoint in README",
            "--memory-delta",
            "API style: minimal stdlib-first",
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout

    latest_json = app / ".handoff" / "handoffs" / "LATEST.json"
    assert latest_json.is_file()
    pack = json.loads(latest_json.read_text(encoding="utf-8"))
    assert pack["goal"] == "Add /health endpoint and return JSON ok"
    assert pack["next_actions"][0].startswith("Implement GET /health")

    # --- Session B: brand-new process, only disk state ---
    # (we only read via CLI; no variables from Session A)
    r = run(["recall", "--root", str(app), "--brief"])
    assert r.returncode == 0, r.stderr
    brief = r.stdout
    assert "Add /health endpoint and return JSON ok" in brief
    assert "Implement GET /health" in brief
    assert "Add a one-line smoke test" in brief
    assert "Document the endpoint" in brief
    assert "Resume brief" in brief
    assert "Execute next action #1" in brief or "next action #1" in brief.lower()

    # Full pack still available if agent needs detail
    r = run(["recall", "--root", str(app), "--budget", "2000"])
    assert r.returncode == 0
    assert "Use plain dict response" in r.stdout or "decision" in r.stdout.lower()
    assert "main.py" in r.stdout


def test_hook_start_after_end_recovers_goal(tmp_path: Path) -> None:
    """session_end save → session_start brief contains goal (lifecycle proof)."""
    env_root = {
        "PYTHONPATH": str(ROOT),
        "HANDOFF_ROOT": str(tmp_path),
        "HANDOFF_GOAL": "Lifecycle continuity goal",
        "HANDOFF_SUMMARY": "ended session mid-feature",
    }
    import os

    e = {**os.environ, **env_root, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}

    assert (
        subprocess.run(
            CLI + ["init", "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            env=e,
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            CLI
            + [
                "save",
                "--root",
                str(tmp_path),
                "--goal",
                "Lifecycle continuity goal",
                "--next",
                "step-a",
                "--next",
                "step-b",
                "--next",
                "step-c",
            ],
            capture_output=True,
            text=True,
            env=e,
        ).returncode
        == 0
    )

    start = ROOT / "examples" / "hooks" / "session_start.py"
    r = subprocess.run(
        [sys.executable, str(start)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=e,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert "Lifecycle continuity goal" in r.stdout
    assert "step-a" in r.stdout
