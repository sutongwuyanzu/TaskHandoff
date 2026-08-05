#!/usr/bin/env python3
"""Session-start hook: inject TaskHandoff brief into agent context.

Exit 0 always (never block session start).
Stdout is meant to be injected as context (Claude Code SessionStart, etc.).

Env:
  HANDOFF_ROOT   project root (default: walk up from cwd for .handoff / .git)
  HANDOFF_BUDGET approx token budget for full recall (only if HANDOFF_FULL=1)
  HANDOFF_FULL   if 1/true, print full recall instead of --brief
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_root(start: Path) -> Path:
    env = os.environ.get("HANDOFF_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".handoff").is_dir() or (p / ".git").exists():
            return p
    return cur


def run_handoff(args: list[str]) -> tuple[int, str]:
    # Prefer installed module; fall back to `handoff` on PATH
    cmds = [
        [sys.executable, "-m", "taskhandoff", *args],
        ["handoff", *args],
    ]
    last_err = ""
    for cmd in cmds:
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            out = (r.stdout or "") + (r.stderr or "")
            if r.returncode == 0 or "No `.handoff/`" not in out:
                return r.returncode, out
            last_err = out
        except FileNotFoundError:
            last_err = f"command not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            last_err = "handoff timed out"
    return 1, last_err


def main() -> int:
    root = find_root(Path.cwd())
    hd = root / ".handoff"
    if not hd.is_dir():
        # Quiet no-op when project not initialized
        print(f"[task-handoff] no .handoff/ under {root} (skip recall)")
        return 0

    full = os.environ.get("HANDOFF_FULL", "").lower() in ("1", "true", "yes")
    budget = os.environ.get("HANDOFF_BUDGET", "2500")
    if full:
        code, out = run_handoff(["recall", "--root", str(root), "--budget", str(budget)])
    else:
        code, out = run_handoff(["recall", "--root", str(root), "--brief"])

    header = (
        "# TaskHandoff session context\n"
        f"# root: {root}\n"
        "# instruction: continue from next action #1 if clear; do not re-ask known goal.\n\n"
    )
    sys.stdout.write(header)
    sys.stdout.write(out if out.endswith("\n") else out + "\n")
    if code != 0:
        sys.stdout.write(f"\n[task-handoff] recall exit={code} (non-fatal)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
