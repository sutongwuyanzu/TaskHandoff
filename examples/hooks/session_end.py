#!/usr/bin/env python3
"""Session-end / checkpoint hook: auto-save TaskHandoff pack.

Safe defaults: never crash the host session (always exit 0).

Env:
  HANDOFF_ROOT     project root
  HANDOFF_GOAL     optional goal override for this save
  HANDOFF_SUMMARY  optional one-line summary
  HANDOFF_SKIP     if 1/true, no-op
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
                timeout=60,
            )
            out = (r.stdout or "") + (r.stderr or "")
            return r.returncode, out
        except FileNotFoundError:
            last_err = f"command not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            last_err = "handoff timed out"
    return 1, last_err


def main() -> int:
    if os.environ.get("HANDOFF_SKIP", "").lower() in ("1", "true", "yes"):
        print("[task-handoff] HANDOFF_SKIP set — session_end no-op", file=sys.stderr)
        return 0

    root = find_root(Path.cwd())
    hd = root / ".handoff"
    if not hd.is_dir():
        # auto-init so first session still leaves a pack
        code, out = run_handoff(["init", "--root", str(root)])
        print(out, file=sys.stderr)

    goal = os.environ.get("HANDOFF_GOAL", "").strip() or "Session checkpoint (auto hook)"
    summary = os.environ.get("HANDOFF_SUMMARY", "").strip() or "Auto-saved by session_end hook"

    args = [
        "save",
        "--root",
        str(root),
        "--auto",
        "--goal",
        goal,
        "--summary",
        summary,
        "--agent-note",
        "session-end-hook",
    ]
    code, out = run_handoff(args)
    # Hooks often only surface stderr; print both
    sys.stderr.write(out if out.endswith("\n") else out + "\n")
    if code != 0:
        sys.stderr.write(f"[task-handoff] save exit={code} (non-fatal)\n")
    else:
        latest = root / ".handoff" / "handoffs" / "LATEST.md"
        sys.stderr.write(f"[task-handoff] saved → {latest}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
