"""Smoke tests for session hook scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "examples" / "hooks" / "session_start.py"
END = ROOT / "examples" / "hooks" / "session_end.py"


def run_py(script: Path, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=e,
        timeout=60,
    )


def test_session_start_without_handoff(tmp_path: Path) -> None:
    r = run_py(START, tmp_path)
    assert r.returncode == 0
    assert "no .handoff" in r.stdout.lower() or "skip" in r.stdout.lower()


def test_session_start_and_end_with_project(tmp_path: Path) -> None:
    # ensure module path
    env = {
        "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""),
        "HANDOFF_ROOT": str(tmp_path),
        "HANDOFF_GOAL": "Hook test goal",
        "HANDOFF_SUMMARY": "from test",
    }
    # init via CLI module
    subprocess.run(
        [sys.executable, "-m", "taskhandoff", "init", "--root", str(tmp_path)],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "taskhandoff",
            "save",
            "--root",
            str(tmp_path),
            "--goal",
            "Hook test goal",
            "--next",
            "one",
            "--next",
            "two",
            "--next",
            "three",
        ],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
    )

    r = run_py(START, tmp_path, env)
    assert r.returncode == 0, r.stderr
    assert "Resume brief" in r.stdout or "Hook test goal" in r.stdout

    r = run_py(END, tmp_path, env)
    assert r.returncode == 0, r.stderr + r.stdout
    assert (tmp_path / ".handoff" / "handoffs" / "LATEST.md").is_file()


def test_session_end_skip(tmp_path: Path) -> None:
    r = run_py(END, tmp_path, {"HANDOFF_SKIP": "1"})
    assert r.returncode == 0
