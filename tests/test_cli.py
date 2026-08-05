"""Smoke tests for TaskHandoff CLI contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "taskhandoff"]


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env_cwd = cwd or ROOT
    return subprocess.run(
        CLI + args,
        cwd=str(env_cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    # minimal fake project
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    return tmp_path


def test_init_save_recall_status_doctor(project: Path) -> None:
    r = run(["init", "--root", str(project)])
    assert r.returncode == 0, r.stderr
    hd = project / ".handoff"
    assert (hd / "MEMORY.md").is_file()
    assert (hd / "config.json").is_file()

    r = run(
        [
            "save",
            "--root",
            str(project),
            "--goal",
            "Ship handoff skill",
            "--done",
            "Scaffold CLI",
            "--decision",
            "Plain files no DB",
            "--file",
            "src/app.py",
            "--next",
            "Push to GitHub",
            "--next",
            "Reply on X",
            "--next",
            "Add demo",
            "--memory-delta",
            "Prefer compact handoffs",
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert (hd / "handoffs" / "LATEST.md").is_file()
    assert (hd / "handoffs" / "LATEST.json").is_file()

    data = json.loads((hd / "handoffs" / "LATEST.json").read_text(encoding="utf-8"))
    assert data["goal"] == "Ship handoff skill"
    assert len(data["next_actions"]) == 3

    r = run(["recall", "--root", str(project), "--brief", "--budget", "800"])
    assert r.returncode == 0, r.stderr
    assert "Resume brief" in r.stdout
    assert "Ship handoff skill" in r.stdout
    assert "Push to GitHub" in r.stdout

    r = run(["status", "--root", str(project)])
    assert r.returncode == 0
    assert "Ship handoff skill" in r.stdout

    r = run(["doctor", "--root", str(project)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout


def test_refuse_secrets(project: Path) -> None:
    run(["init", "--root", str(project)])
    r = run(
        [
            "save",
            "--root",
            str(project),
            "--goal",
            "leak test",
            "--body",
            "token=ghp_abcdefghijklmnopqrstuvwxyz0123456789",
            "--next",
            "a",
            "--next",
            "b",
            "--next",
            "c",
        ]
    )
    assert r.returncode != 0
    assert "secrets" in (r.stderr + r.stdout).lower() or "Refusing" in (r.stderr + r.stdout)


def test_info(project: Path) -> None:
    r = run(["info", "--root", str(project)])
    assert r.returncode == 0, r.stderr
    assert "taskhandoff" in r.stdout
    assert "skill_root" in r.stdout


def test_auto_save(project: Path) -> None:
    run(["init", "--root", str(project)])
    # first explicit save
    run(
        [
            "save",
            "--root",
            str(project),
            "--goal",
            "Keep goal across auto",
            "--next",
            "step one",
            "--next",
            "step two",
            "--next",
            "step three",
        ]
    )
    r = run(["save", "--root", str(project), "--auto", "--summary", "checkpoint"])
    assert r.returncode == 0, r.stderr + r.stdout
    data = json.loads((project / ".handoff" / "handoffs" / "LATEST.json").read_text(encoding="utf-8"))
    assert data["goal"] == "Keep goal across auto"
    assert data.get("auto") is True
