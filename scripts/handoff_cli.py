#!/usr/bin/env python3
"""task-handoff CLI — long-task memory & cross-session handoff for coding agents.

Usage:
  python handoff_cli.py init   --root <project>
  python handoff_cli.py save   --root <project> --goal "..." [options]
  python handoff_cli.py recall --root <project> [--budget 2500]
  python handoff_cli.py status --root <project>
  python handoff_cli.py memory --root <project> --append "## Pref\\n- use pnpm"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"
HANDOFF_DIRNAME = ".handoff"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ts_slug(dt: Optional[datetime] = None) -> str:
    d = dt or utc_now()
    return d.strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def handoff_root(project_root: Path) -> Path:
    return project_root / HANDOFF_DIRNAME


def ensure_project(project_root: Path) -> Path:
    root = project_root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Project root is not a directory: {root}")
    return root


def run_git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if out.returncode != 0:
            return ""
        return (out.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def git_snapshot(root: Path) -> dict[str, str]:
    branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "n/a"
    status = run_git(root, "status", "--porcelain")
    if not status:
        dirty = "clean"
    else:
        lines = [ln for ln in status.splitlines() if ln.strip()]
        dirty = f"{len(lines)} changed path(s)"
        # short sample
        sample = ", ".join(ln[3:] if len(ln) > 3 else ln for ln in lines[:5])
        if sample:
            dirty = f"{dirty}: {sample}"
            if len(lines) > 5:
                dirty += ", ..."
    head = run_git(root, "rev-parse", "--short", "HEAD") or "n/a"
    return {"branch": branch, "dirty_summary": dirty, "head": head}


def copy_template(name: str, dest: Path, overwrite: bool = False) -> None:
    src = TEMPLATES / name
    if not src.exists():
        raise SystemExit(f"Missing template: {src}")
    if dest.exists() and not overwrite:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def cmd_init(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    (hd / "sessions").mkdir(parents=True, exist_ok=True)
    (hd / "handoffs").mkdir(parents=True, exist_ok=True)

    cfg_path = hd / "config.json"
    if not cfg_path.exists():
        cfg = {
            "version": 1,
            "project_id": root.name,
            "language": args.language,
            "token_budget_recall": 2500,
            "created_at": iso_now(),
            "notes": "task-handoff config — safe to commit",
        }
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    copy_template("MEMORY.md", hd / "MEMORY.md")
    copy_template("todos.json", hd / "todos.json")
    if not (hd / "decisions.jsonl").exists():
        (hd / "decisions.jsonl").write_text("", encoding="utf-8")

    # Ensure .gitignore does not ignore .handoff by default; add helper ignore for secrets pattern
    gi = hd / ".gitkeep"
    gi.write_text("", encoding="utf-8")

    # Optional: add .handoff/ to project's tracked files note
    readme_hint = hd / "README.txt"
    if not readme_hint.exists():
        readme_hint.write_text(
            "Managed by task-handoff skill.\n"
            "Load handoffs/LATEST.md + MEMORY.md when resuming a long task.\n"
            "Do not put secrets here.\n",
            encoding="utf-8",
        )

    print(f"Initialized task-handoff at: {hd}")
    print("Next: work on your task, then run `save` before ending the session.")
    return 0


def render_list(items: List[str], empty: str = "- (none)") -> str:
    cleaned = []
    for i in items:
        if not i or not str(i).strip():
            continue
        c = str(i).strip()
        # avoid "- - item" when callers already prefix bullets
        if c.startswith("- "):
            c = c[2:].strip()
        cleaned.append(c)
    if not cleaned:
        return empty
    return "\n".join(f"- {c}" for c in cleaned)


def cmd_save(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    if not hd.is_dir():
        print("`.handoff/` missing — running init first...", file=sys.stderr)
        cmd_init(argparse.Namespace(root=str(root), language="zh-CN"))

    git = git_snapshot(root)
    stamp = ts_slug()
    created = iso_now()

    next_actions = args.next or []
    while len(next_actions) < 3:
        next_actions.append("(define next action)")

    goal = (args.goal or "").strip() or "(goal not set — fill in)"
    summary = (args.summary or "").strip()
    done = args.done or ([] if not summary else [summary])
    doing = args.doing or []
    blocked = args.blocked or []
    decisions = args.decision or []
    questions = args.question or []
    key_files = args.file or []
    commands = args.command or []
    links = args.link or []
    memory_deltas = args.memory_delta or []
    agent_note = args.agent_note or "task-handoff"

    # Append decisions log
    if decisions:
        log_path = hd / "decisions.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            for d in decisions:
                rec = {"ts": created, "decision": d}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Update todos if provided as JSON file or inline markers
    todos_path = hd / "todos.json"
    if args.todos_json:
        raw = Path(args.todos_json).read_text(encoding="utf-8")
        todos_path.write_text(raw if raw.endswith("\n") else raw + "\n", encoding="utf-8")
    elif next_actions:
        todos = {
            "version": 1,
            "updated_at": created,
            "items": [
                {"id": f"n{i+1}", "text": t, "status": "pending"}
                for i, t in enumerate(next_actions[:3])
            ],
        }
        todos_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Append memory deltas to MEMORY.md
    if memory_deltas:
        mem_path = hd / "MEMORY.md"
        block = "\n".join(memory_deltas)
        with mem_path.open("a", encoding="utf-8") as f:
            f.write(f"\n\n<!-- delta {created} -->\n{block}\n")

    tpl_path = TEMPLATES / "handoff.md"
    tpl = tpl_path.read_text(encoding="utf-8")
    body = tpl
    replacements = {
        "{{timestamp}}": created,
        "{{branch}}": f"{git['branch']} @ {git['head']}",
        "{{dirty_summary}}": git["dirty_summary"],
        "{{agent_note}}": agent_note,
        "{{goal}}": goal,
        "{{done}}": render_list(done),
        "{{doing}}": render_list(doing),
        "{{blocked}}": render_list(blocked),
        "{{decisions}}": render_list(decisions),
        "{{memory_deltas}}": render_list(memory_deltas),
        "{{key_files}}": ", ".join(key_files) if key_files else "(none)",
        "{{commands}}": "; ".join(commands) if commands else "(none)",
        "{{links}}": ", ".join(links) if links else "(none)",
        "{{open_questions}}": render_list(questions),
        "{{next_1}}": next_actions[0],
        "{{next_2}}": next_actions[1],
        "{{next_3}}": next_actions[2],
    }
    for k, v in replacements.items():
        body = body.replace(k, v)

    # Free-form extra section
    if args.body:
        body += "\n\n## Extra notes\n\n" + args.body.strip() + "\n"

    out_name = f"{stamp}.md"
    out_path = hd / "handoffs" / out_name
    out_path.write_text(body, encoding="utf-8")
    latest = hd / "handoffs" / "LATEST.md"
    latest.write_text(body, encoding="utf-8")

    # Also keep a compact JSON sidecar for tooling
    sidecar = {
        "version": 1,
        "created_at": created,
        "goal": goal,
        "next_actions": next_actions[:3],
        "branch": git["branch"],
        "head": git["head"],
        "dirty_summary": git["dirty_summary"],
        "path": str(out_path.relative_to(root)).replace("\\", "/"),
    }
    (hd / "handoffs" / "LATEST.json").write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Saved handoff: {out_path}")
    print(f"Latest:        {latest}")
    print("Next actions:")
    for i, a in enumerate(next_actions[:3], 1):
        print(f"  {i}. {a}")
    return 0


def approx_tokens(text: str) -> int:
    # rough: CJK ~1.5 chars/token, ASCII ~4 chars/token — use simple char/3
    return max(1, len(text) // 3)


def trim_to_budget(text: str, budget: int) -> str:
    if approx_tokens(text) <= budget:
        return text
    # keep head sections by cutting from bottom
    lines = text.splitlines()
    out: List[str] = []
    for line in lines:
        trial = "\n".join(out + [line])
        if approx_tokens(trial) > budget:
            out.append("\n...[truncated by token budget]...")
            break
        out.append(line)
    return "\n".join(out)


def cmd_recall(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    if not hd.is_dir():
        print("No `.handoff/` in this project. Run: handoff_cli.py init --root .")
        return 1

    budget = int(args.budget)
    parts: List[str] = []
    parts.append(f"# task-handoff recall @ {iso_now()}")
    parts.append(f"project: {root}")
    parts.append("")

    mem = hd / "MEMORY.md"
    latest = hd / "handoffs" / "LATEST.md"
    todos = hd / "todos.json"
    cfg = hd / "config.json"

    if cfg.exists():
        try:
            c = json.loads(cfg.read_text(encoding="utf-8"))
            parts.append(f"config.project_id: {c.get('project_id', '')}")
            parts.append("")
        except json.JSONDecodeError:
            pass

    if mem.exists():
        parts.append("===== MEMORY.md =====")
        parts.append(mem.read_text(encoding="utf-8").strip())
        parts.append("")
    else:
        parts.append("(no MEMORY.md)")

    if latest.exists():
        parts.append("===== handoffs/LATEST.md =====")
        parts.append(latest.read_text(encoding="utf-8").strip())
        parts.append("")
    else:
        parts.append("(no LATEST handoff yet — nothing to resume)")

    if todos.exists():
        parts.append("===== todos.json =====")
        parts.append(todos.read_text(encoding="utf-8").strip())
        parts.append("")

    # Recent decisions (last 10)
    dec = hd / "decisions.jsonl"
    if dec.exists():
        lines = [ln for ln in dec.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            parts.append("===== recent decisions (last 10) =====")
            for ln in lines[-10:]:
                parts.append(ln)
            parts.append("")

    pack = "\n".join(parts).strip() + "\n"
    pack = trim_to_budget(pack, budget)

    out = args.out
    if out:
        Path(out).write_text(pack, encoding="utf-8")
        print(f"Wrote recall pack: {out} (~{approx_tokens(pack)} tokens est.)")
    else:
        sys.stdout.write(pack)
        if not pack.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    print(f"project: {root}")
    if not hd.is_dir():
        print("handoff: NOT initialized")
        return 1
    print(f"handoff: {hd}")
    latest = hd / "handoffs" / "LATEST.md"
    mem = hd / "MEMORY.md"
    print(f"MEMORY.md: {'yes' if mem.exists() else 'no'} ({mem.stat().st_size if mem.exists() else 0} bytes)")
    print(f"LATEST.md: {'yes' if latest.exists() else 'no'}")
    if latest.exists():
        text = latest.read_text(encoding="utf-8")
        print(f"LATEST size: {len(text)} chars (~{approx_tokens(text)} tokens est.)")
        # extract goal / next
        g = re.search(r"## Goal\s*\n+(.+?)(?:\n## |\Z)", text, re.S)
        if g:
            print("goal:", " ".join(g.group(1).split())[:120])
        n = re.search(r"## Next actions\s*\n+(.+?)(?:\n## |\Z)", text, re.S)
        if n:
            print("next actions:")
            for line in n.group(1).strip().splitlines()[:5]:
                print(" ", line)
    handoffs = sorted((hd / "handoffs").glob("20*.md"))
    print(f"history packs: {len(handoffs)}")
    git = git_snapshot(root)
    print(f"git: {git['branch']} @ {git['head']} ({git['dirty_summary']})")
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    if not hd.is_dir():
        cmd_init(argparse.Namespace(root=str(root), language="zh-CN"))
    mem = hd / "MEMORY.md"
    if not mem.exists():
        copy_template("MEMORY.md", mem)
    append = args.append
    if not append:
        print(mem.read_text(encoding="utf-8"))
        return 0
    with mem.open("a", encoding="utf-8") as f:
        f.write(f"\n\n<!-- {iso_now()} -->\n")
        f.write(append.rstrip() + "\n")
    print(f"Appended to {mem}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="handoff_cli",
        description="DeepSeek-friendly long-task handoff & project memory for coding agents",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize .handoff/ in a project")
    p_init.add_argument("--root", default=".", help="Project root (default: .)")
    p_init.add_argument("--language", default="zh-CN")
    p_init.set_defaults(func=cmd_init)

    p_save = sub.add_parser("save", help="Save a handoff pack + update todos/decisions")
    p_save.add_argument("--root", default=".")
    p_save.add_argument("--goal", default="")
    p_save.add_argument("--summary", default="", help="Short summary (also used as done item if --done omitted)")
    p_save.add_argument("--done", action="append", default=[], help="Done item (repeatable)")
    p_save.add_argument("--doing", action="append", default=[])
    p_save.add_argument("--blocked", action="append", default=[])
    p_save.add_argument("--decision", action="append", default=[])
    p_save.add_argument("--question", action="append", default=[])
    p_save.add_argument("--file", action="append", default=[], help="Key file path")
    p_save.add_argument("--command", action="append", default=[])
    p_save.add_argument("--link", action="append", default=[])
    p_save.add_argument("--next", action="append", default=[], help="Next action (up to 3)")
    p_save.add_argument("--memory-delta", action="append", default=[], dest="memory_delta")
    p_save.add_argument("--agent-note", default="task-handoff", dest="agent_note")
    p_save.add_argument("--body", default="", help="Extra free-form markdown")
    p_save.add_argument("--todos-json", default="", help="Replace todos.json from file")
    p_save.set_defaults(func=cmd_save)

    p_recall = sub.add_parser("recall", help="Print compact recall pack for the agent")
    p_recall.add_argument("--root", default=".")
    p_recall.add_argument("--budget", default=2500, type=int, help="Approx token budget")
    p_recall.add_argument("--out", default="", help="Write to file instead of stdout")
    p_recall.set_defaults(func=cmd_recall)

    p_status = sub.add_parser("status", help="Show handoff status")
    p_status.add_argument("--root", default=".")
    p_status.set_defaults(func=cmd_status)

    p_mem = sub.add_parser("memory", help="Show or append durable MEMORY.md")
    p_mem.add_argument("--root", default=".")
    p_mem.add_argument("--append", default="", help="Markdown fragment to append")
    p_mem.set_defaults(func=cmd_memory)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
