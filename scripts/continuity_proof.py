#!/usr/bin/env python3
"""Print a human-readable continuity proof (Session A → wipe memory → Session B).

Run:
  python scripts/continuity_proof.py

Exit 0 only if Session B brief recovers goal + next actions without any
in-process state from Session A.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "taskhandoff"]


def sh(args: list[str], cwd: Path) -> str:
    r = subprocess.run(
        CLI + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**dict(**__import__("os").environ), "PYTHONPATH": str(ROOT)},
    )
    if r.returncode != 0:
        raise SystemExit(f"FAIL cmd {args}: {r.stderr or r.stdout}")
    return r.stdout


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="th-continuity-"))
    try:
        app = tmp / "demo-app"
        app.mkdir()
        (app / "main.py").write_text("# session A work in progress\n", encoding="utf-8")

        print("=== Session A (old chat — will be discarded) ===")
        print(sh(["init", "--root", str(app)], ROOT).rstrip())
        out = sh(
            [
                "save",
                "--root",
                str(app),
                "--goal",
                "Add /health endpoint returning JSON ok",
                "--done",
                "Scaffold main.py",
                "--decision",
                "stdlib only",
                "--file",
                "main.py",
                "--next",
                "Implement /health",
                "--next",
                "Add smoke test",
                "--next",
                "Update README",
            ],
            ROOT,
        )
        print(out.rstrip())
        pack = json.loads((app / ".handoff" / "handoffs" / "LATEST.json").read_text(encoding="utf-8"))
        print(f"\n[disk] LATEST.json goal = {pack['goal']!r}")
        print(f"[disk] next_actions   = {pack['next_actions']!r}")

        print("\n=== Simulate: close chat / new agent / no history ===")
        print("(new process; only files under .handoff/ remain)\n")

        print("=== Session B (new chat — recall only) ===")
        brief = sh(["recall", "--root", str(app), "--brief"], ROOT)
        print(brief.rstrip())

        need = [
            "Add /health endpoint returning JSON ok",
            "Implement /health",
            "Add smoke test",
            "Update README",
        ]
        missing = [x for x in need if x not in brief]
        print("\n=== Proof check ===")
        if missing:
            print("FAIL — brief missing:", missing)
            return 1
        print("PASS — Session B recovered goal + all 3 next actions from disk alone.")
        print("Claim: chat history was not required for the recovery contract.")
        print("Scope: disk-level continuity (not LLM execution quality).")
        print("Full suite: pytest tests/test_continuity.py -q")
        print(f"Artifacts: {app / '.handoff'}")
        return 0
    finally:
        # keep tmp if FAIL for inspection? always clean for demo
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    # ensure package import path
    import os

    os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")
    raise SystemExit(main())
