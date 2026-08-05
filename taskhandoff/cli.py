#!/usr/bin/env python3
"""TaskHandoff CLI — long-task memory & cross-session handoff for coding agents.

Usage:
  handoff init   --root <project>
  handoff save   --root <project> [--auto] --goal "..." [options]
  handoff recall --root <project> [--budget 2500] [--brief]
  handoff status --root <project>
  handoff memory --root <project> [--append "..."]
  handoff doctor --root <project>
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
from typing import List, Optional, Sequence, Tuple

from taskhandoff import __version__

__all__ = ["main", "build_parser"]

# Repo root when installed editable / run from source tree
_PKG_DIR = Path(__file__).resolve().parent
_CANDIDATE_ROOTS = [
    _PKG_DIR.parent,  # repo root (dev / editable)
    _PKG_DIR,  # package-local data (wheel with package-data)
]


def find_skill_root() -> Path:
    for root in _CANDIDATE_ROOTS:
        if (root / "templates" / "handoff.md").exists():
            return root
        if (root / "templates" / "handoff.md").exists():
            return root
    # fallback: repo-style
    return _PKG_DIR.parent


def skill_root() -> Path:
    return find_skill_root()


def templates_dir() -> Path:
    return skill_root() / "templates"


HANDOFF_DIRNAME = ".handoff"

# Obvious secret patterns — refuse to write these into handoff files
SECRET_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
    ("bearer_jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_pat", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
]


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
            timeout=15,
            check=False,
        )
        if out.returncode != 0:
            return ""
        return (out.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def git_snapshot(root: Path) -> dict:
    branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD") or "n/a"
    status = run_git(root, "status", "--porcelain")
    changed_files: List[str] = []
    if not status:
        dirty = "clean"
    else:
        lines = [ln for ln in status.splitlines() if ln.strip()]
        for ln in lines:
            # porcelain: XY PATH or XY ORIG -> PATH
            path = ln[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if path:
                changed_files.append(path)
        dirty = f"{len(lines)} changed path(s)"
        sample = ", ".join(changed_files[:5])
        if sample:
            dirty = f"{dirty}: {sample}"
            if len(changed_files) > 5:
                dirty += ", ..."
    head = run_git(root, "rev-parse", "--short", "HEAD") or "n/a"
    log = run_git(root, "log", "-5", "--oneline")
    recent_commits = [ln for ln in log.splitlines() if ln.strip()] if log else []
    return {
        "branch": branch,
        "dirty_summary": dirty,
        "head": head,
        "changed_files": changed_files,
        "recent_commits": recent_commits,
    }


def scan_secrets(text: str) -> List[str]:
    hits: List[str] = []
    for name, pat in SECRET_PATTERNS:
        if pat.search(text):
            hits.append(name)
    return hits


def assert_no_secrets(*chunks: str, allow: bool = False) -> None:
    blob = "\n".join(c for c in chunks if c)
    hits = scan_secrets(blob)
    if hits and not allow:
        raise SystemExit(
            "Refusing to write possible secrets into handoff files: "
            + ", ".join(hits)
            + "\nStrip secrets, or pass --allow-secrets if this is a false positive."
        )


def copy_template(name: str, dest: Path, overwrite: bool = False) -> None:
    src = templates_dir() / name
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

    (hd / ".gitkeep").write_text("", encoding="utf-8")

    readme_hint = hd / "README.txt"
    if not readme_hint.exists():
        readme_hint.write_text(
            "Managed by TaskHandoff (task-handoff skill).\n"
            "Load handoffs/LATEST.md + MEMORY.md when resuming a long task.\n"
            "Do not put secrets here.\n",
            encoding="utf-8",
        )

    # Suggest tracking .handoff in git
    # Lightweight ignore for accidental secret dumps (still track the rest of .handoff/)
    local_gi = hd / ".gitignore"
    if not local_gi.exists():
        local_gi.write_text(
            "# optional local dumps — keep MEMORY/handoffs tracked\n"
            "sessions/*\n"
            "!.gitkeep\n"
            "*.secret\n"
            "*.key\n",
            encoding="utf-8",
        )

    print(f"Initialized TaskHandoff at: {hd}")
    print("Next: work on your task, then run `handoff save --auto --goal \"...\"` before ending the session.")
    return 0


def render_list(items: Sequence[str], empty: str = "- (none)") -> str:
    cleaned: List[str] = []
    for i in items:
        if not i or not str(i).strip():
            continue
        c = str(i).strip()
        if c.startswith("- "):
            c = c[2:].strip()
        cleaned.append(c)
    if not cleaned:
        return empty
    return "\n".join(f"- {c}" for c in cleaned)


def load_previous_goal(hd: Path) -> str:
    latest_json = hd / "handoffs" / "LATEST.json"
    if latest_json.exists():
        try:
            data = json.loads(latest_json.read_text(encoding="utf-8"))
            g = (data.get("goal") or "").strip()
            if g and g != "(goal not set — fill in)":
                return g
        except json.JSONDecodeError:
            pass
    latest_md = hd / "handoffs" / "LATEST.md"
    if latest_md.exists():
        m = re.search(r"## Goal\s*\n+(.+?)(?:\n## |\Z)", latest_md.read_text(encoding="utf-8"), re.S)
        if m:
            return " ".join(m.group(1).split())
    return ""


def auto_fill(root: Path, hd: Path, args: argparse.Namespace) -> dict:
    """Fill missing fields from git + previous handoff."""
    git = git_snapshot(root)
    goal = (args.goal or "").strip() or load_previous_goal(hd)
    if not goal:
        if git["recent_commits"]:
            # use latest commit subject as weak goal hint
            subj = git["recent_commits"][0].split(" ", 1)
            goal = f"(auto) continue work near: {subj[-1] if len(subj) > 1 else subj[0]}"
        else:
            goal = "(goal not set — fill in)"

    done = list(args.done or [])
    summary = (args.summary or "").strip()
    if summary and summary not in done:
        done.append(summary)
    if not done and git["recent_commits"]:
        done = [f"recent: {c}" for c in git["recent_commits"][:3]]

    key_files = list(args.file or [])
    if not key_files and git["changed_files"]:
        key_files = git["changed_files"][:12]

    doing = list(args.doing or [])
    if not doing and git["changed_files"]:
        doing = [f"uncommitted changes in {len(git['changed_files'])} file(s)"]

    next_actions = list(args.next or [])
    if not next_actions:
        # try previous next actions from LATEST.json
        lj = hd / "handoffs" / "LATEST.json"
        if lj.exists():
            try:
                prev = json.loads(lj.read_text(encoding="utf-8")).get("next_actions") or []
                next_actions = [str(x) for x in prev if str(x).strip()]
            except json.JSONDecodeError:
                pass
        if not next_actions:
            if git["changed_files"]:
                next_actions = [
                    f"Review and commit: {key_files[0]}" if key_files else "Review uncommitted changes",
                    "Update tests for the current change",
                    "Run handoff save again with explicit --next actions",
                ]
            else:
                next_actions = [
                    "Define the next concrete coding step",
                    "Implement and verify with a command/test",
                    "Save a richer handoff with --done / --decision",
                ]

    body_extra = (args.body or "").strip()
    if getattr(args, "auto", False):
        auto_bits = []
        if git["recent_commits"]:
            auto_bits.append("### Recent commits\n" + "\n".join(f"- `{c}`" for c in git["recent_commits"]))
        if git["changed_files"]:
            auto_bits.append(
                "### Changed files (git)\n" + "\n".join(f"- `{p}`" for p in git["changed_files"][:20])
            )
        if auto_bits:
            chunk = "\n\n".join(auto_bits)
            body_extra = (body_extra + "\n\n" + chunk).strip() if body_extra else chunk

    return {
        "goal": goal,
        "done": done,
        "doing": doing,
        "blocked": list(args.blocked or []),
        "decisions": list(args.decision or []),
        "questions": list(args.question or []),
        "key_files": key_files,
        "commands": list(args.command or []),
        "links": list(args.link or []),
        "memory_deltas": list(args.memory_delta or []),
        "next_actions": next_actions,
        "body": body_extra,
        "git": git,
    }


def cmd_save(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    if not hd.is_dir():
        print("`.handoff/` missing — running init first...", file=sys.stderr)
        cmd_init(argparse.Namespace(root=str(root), language="zh-CN"))

    if getattr(args, "auto", False):
        fields = auto_fill(root, hd, args)
    else:
        git = git_snapshot(root)
        next_actions = list(args.next or [])
        fields = {
            "goal": (args.goal or "").strip() or "(goal not set — fill in)",
            "done": list(args.done or ([] if not (args.summary or "").strip() else [args.summary.strip()])),
            "doing": list(args.doing or []),
            "blocked": list(args.blocked or []),
            "decisions": list(args.decision or []),
            "questions": list(args.question or []),
            "key_files": list(args.file or []),
            "commands": list(args.command or []),
            "links": list(args.link or []),
            "memory_deltas": list(args.memory_delta or []),
            "next_actions": next_actions,
            "body": (args.body or "").strip(),
            "git": git,
        }

    git = fields["git"]
    stamp = ts_slug()
    created = iso_now()

    next_actions = list(fields["next_actions"])
    while len(next_actions) < 3:
        next_actions.append("(define next action)")
    next_actions = next_actions[:3]

    goal = fields["goal"]
    done = fields["done"]
    doing = fields["doing"]
    blocked = fields["blocked"]
    decisions = fields["decisions"]
    questions = fields["questions"]
    key_files = fields["key_files"]
    commands = fields["commands"]
    links = fields["links"]
    memory_deltas = fields["memory_deltas"]
    agent_note = args.agent_note or "task-handoff"
    body_extra = fields.get("body") or ""

    # Secret scan on all user-provided text
    assert_no_secrets(
        goal,
        "\n".join(done),
        "\n".join(doing),
        "\n".join(blocked),
        "\n".join(decisions),
        "\n".join(questions),
        "\n".join(memory_deltas),
        body_extra,
        allow=bool(getattr(args, "allow_secrets", False)),
    )

    if decisions:
        log_path = hd / "decisions.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            for d in decisions:
                rec = {"ts": created, "decision": d}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    todos_path = hd / "todos.json"
    if args.todos_json:
        raw = Path(args.todos_json).read_text(encoding="utf-8")
        assert_no_secrets(raw, allow=bool(getattr(args, "allow_secrets", False)))
        todos_path.write_text(raw if raw.endswith("\n") else raw + "\n", encoding="utf-8")
    else:
        todos = {
            "version": 1,
            "updated_at": created,
            "items": [
                {"id": f"n{i+1}", "text": t, "status": "pending"}
                for i, t in enumerate(next_actions[:3])
            ],
        }
        todos_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if memory_deltas:
        mem_path = hd / "MEMORY.md"
        # normalize bullets
        lines = []
        for d in memory_deltas:
            s = d.strip()
            if s.startswith("- "):
                lines.append(s)
            else:
                lines.append(f"- {s}")
        with mem_path.open("a", encoding="utf-8") as f:
            f.write(f"\n\n<!-- delta {created} -->\n")
            f.write("\n".join(lines) + "\n")

    tpl_path = templates_dir() / "handoff.md"
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

    if body_extra:
        body += "\n\n## Extra notes\n\n" + body_extra.strip() + "\n"

    out_name = f"{stamp}.md"
    out_path = hd / "handoffs" / out_name
    out_path.write_text(body, encoding="utf-8")
    latest = hd / "handoffs" / "LATEST.md"
    latest.write_text(body, encoding="utf-8")

    sidecar = {
        "version": 1,
        "created_at": created,
        "goal": goal,
        "next_actions": next_actions[:3],
        "branch": git["branch"],
        "head": git["head"],
        "dirty_summary": git["dirty_summary"],
        "key_files": key_files,
        "path": str(out_path.relative_to(root)).replace("\\", "/"),
        "auto": bool(getattr(args, "auto", False)),
    }
    (hd / "handoffs" / "LATEST.json").write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Saved handoff: {out_path}")
    print(f"Latest:        {latest}")
    print(f"Goal:          {goal}")
    print("Next actions:")
    for i, a in enumerate(next_actions[:3], 1):
        print(f"  {i}. {a}")
    if getattr(args, "auto", False):
        print("(auto mode: filled from git + previous handoff where possible)")
    return 0


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def trim_to_budget(text: str, budget: int) -> str:
    if approx_tokens(text) <= budget:
        return text
    lines = text.splitlines()
    out: List[str] = []
    for line in lines:
        trial = "\n".join(out + [line])
        if approx_tokens(trial) > budget:
            out.append("...[truncated by token budget]...")
            break
        out.append(line)
    return "\n".join(out)


def extract_section(md: str, heading: str) -> str:
    pat = rf"## {re.escape(heading)}\s*\n+(.+?)(?:\n## |\Z)"
    m = re.search(pat, md, re.S)
    if not m:
        return ""
    return m.group(1).strip()


def build_brief(root: Path, hd: Path) -> str:
    """Fixed short restatement for the next agent session (≤ ~15 lines)."""
    lines: List[str] = [
        "# Resume brief (TaskHandoff)",
        f"- project: `{root.name}`",
        f"- path: `{root}`",
        f"- recalled_at: {iso_now()}",
    ]
    latest = hd / "handoffs" / "LATEST.md"
    mem = hd / "MEMORY.md"
    lj = hd / "handoffs" / "LATEST.json"

    goal = ""
    nexts: List[str] = []
    if lj.exists():
        try:
            data = json.loads(lj.read_text(encoding="utf-8"))
            goal = (data.get("goal") or "").strip()
            nexts = [str(x) for x in (data.get("next_actions") or [])]
            lines.append(f"- branch: {data.get('branch', 'n/a')} @ {data.get('head', 'n/a')}")
            lines.append(f"- dirty: {data.get('dirty_summary', 'n/a')}")
        except json.JSONDecodeError:
            pass

    status_bits = []
    if latest.exists():
        text = latest.read_text(encoding="utf-8")
        if not goal:
            goal = " ".join(extract_section(text, "Goal").split())
        doing = extract_section(text, "Status")
        # pull Doing subsection if present
        dm = re.search(r"### Doing\s*\n+(.+?)(?:\n### |\Z)", extract_section(text, "Status") + "\n", re.S)
        if dm:
            doing_txt = " ".join(dm.group(1).split()).strip().lstrip("- ").strip()
            if doing_txt and doing_txt not in ("(none)", "none"):
                status_bits.append(f"doing: {doing_txt[:120]}")
        if not nexts:
            na = extract_section(text, "Next actions")
            for ln in na.splitlines():
                ln = ln.strip()
                if re.match(r"^\d+\.", ln):
                    nexts.append(re.sub(r"^\d+\.\s*", "", ln))

    lines.append(f"- goal: {goal or '(unknown)'}")
    if status_bits:
        lines.extend(f"- {s}" for s in status_bits)

    # durable prefs snippet
    if mem.exists():
        mtxt = mem.read_text(encoding="utf-8")
        prefs = re.search(r"## Preferences\s*\n+(.+?)(?:\n## |\Z)", mtxt, re.S)
        if prefs:
            pref_line = " ".join(prefs.group(1).split())[:160]
            if pref_line and pref_line != "- Package manager: - Style / conventions: - Deploy / runtime:":
                lines.append(f"- memory_prefs: {pref_line}")

    lines.append("- next:")
    for i, a in enumerate((nexts + ["(none)", "(none)", "(none)"])[:3], 1):
        lines.append(f"  {i}. {a}")
    lines.append("- instruction: Execute next action #1 now. Re-read `.handoff/handoffs/LATEST.md` if details are missing.")
    lines.append("")
    return "\n".join(lines)


def cmd_recall(args: argparse.Namespace) -> int:
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    if not hd.is_dir():
        print("No `.handoff/` in this project. Run: handoff init --root .")
        return 1

    budget = int(args.budget)
    brief_only = bool(getattr(args, "brief", False))

    brief = build_brief(root, hd)
    if brief_only:
        pack = brief
        pack = trim_to_budget(pack, budget)
    else:
        parts: List[str] = [brief, "", "---", ""]
        parts.append(f"# full recall pack @ {iso_now()}")
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

        dec = hd / "decisions.jsonl"
        if dec.exists():
            dlines = [ln for ln in dec.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if dlines:
                parts.append("===== recent decisions (last 10) =====")
                parts.extend(dlines[-10:])
                parts.append("")

        pack = "\n".join(parts).strip() + "\n"
        pack = trim_to_budget(pack, budget)

    out = args.out
    if out:
        Path(out).write_text(pack, encoding="utf-8")
        print(f"Wrote recall pack: {out} (~{approx_tokens(pack)} tokens est.)")
    else:
        sys.stdout.write(pack if pack.endswith("\n") else pack + "\n")
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
    assert_no_secrets(append, allow=bool(getattr(args, "allow_secrets", False)))
    with mem.open("a", encoding="utf-8") as f:
        f.write(f"\n\n<!-- {iso_now()} -->\n")
        f.write(append.rstrip() + "\n")
    print(f"Appended to {mem}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Health check for a project handoff setup."""
    root = ensure_project(Path(args.root))
    hd = handoff_root(root)
    ok = True
    print(f"doctor: {root}")
    print(f"skill_root: {skill_root()}")
    print(f"templates: {templates_dir()} ({'ok' if templates_dir().is_dir() else 'MISSING'})")
    if not templates_dir().is_dir():
        ok = False
    if not hd.is_dir():
        print("`.handoff/`: missing (run handoff init)")
        return 1
    for rel in ["config.json", "MEMORY.md", "todos.json", "handoffs"]:
        p = hd / rel
        print(f"  {rel}: {'ok' if p.exists() else 'MISSING'}")
        if not p.exists():
            ok = False
    latest = hd / "handoffs" / "LATEST.md"
    if latest.exists():
        text = latest.read_text(encoding="utf-8")
        hits = scan_secrets(text)
        if hits:
            print(f"  WARNING: possible secrets in LATEST.md: {', '.join(hits)}")
            ok = False
        else:
            print("  LATEST.md secret scan: clean")
    else:
        print("  LATEST.md: none yet")
    print("result:", "OK" if ok else "ISSUES")
    return 0 if ok else 2


def cmd_info(args: argparse.Namespace) -> int:
    """Print install paths / version (debug helper)."""
    print(f"taskhandoff {__version__}")
    print(f"skill_root: {skill_root()}")
    print(f"templates:  {templates_dir()}")
    print(f"cli_file:   {Path(__file__).resolve()}")
    root = Path(args.root).resolve()
    hd = handoff_root(root)
    print(f"project:    {root}")
    print(f".handoff:   {hd} ({'exists' if hd.is_dir() else 'missing'})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="handoff",
        description="TaskHandoff — DeepSeek-friendly long-task handoff & project memory",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize .handoff/ in a project")
    p_init.add_argument("--root", default=".", help="Project root (default: .)")
    p_init.add_argument("--language", default="zh-CN")
    p_init.set_defaults(func=cmd_init)

    p_save = sub.add_parser("save", help="Save a handoff pack")
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
    p_save.add_argument(
        "--auto",
        action="store_true",
        help="Auto-fill from git status/log + previous handoff (best effort)",
    )
    p_save.add_argument(
        "--allow-secrets",
        action="store_true",
        dest="allow_secrets",
        help="Allow writing text that looks like secrets (not recommended)",
    )
    p_save.set_defaults(func=cmd_save)

    p_recall = sub.add_parser("recall", help="Print compact recall pack for the agent")
    p_recall.add_argument("--root", default=".")
    p_recall.add_argument("--budget", default=2500, type=int, help="Approx token budget")
    p_recall.add_argument("--out", default="", help="Write to file instead of stdout")
    p_recall.add_argument(
        "--brief",
        action="store_true",
        help="Only print the short resume brief (best for new sessions)",
    )
    p_recall.set_defaults(func=cmd_recall)

    p_status = sub.add_parser("status", help="Show handoff status")
    p_status.add_argument("--root", default=".")
    p_status.set_defaults(func=cmd_status)

    p_mem = sub.add_parser("memory", help="Show or append durable MEMORY.md")
    p_mem.add_argument("--root", default=".")
    p_mem.add_argument("--append", default="", help="Markdown fragment to append")
    p_mem.add_argument("--allow-secrets", action="store_true", dest="allow_secrets")
    p_mem.set_defaults(func=cmd_memory)

    p_doc = sub.add_parser("doctor", help="Check .handoff/ health and secret scan")
    p_doc.add_argument("--root", default=".")
    p_doc.set_defaults(func=cmd_doctor)

    p_info = sub.add_parser("info", help="Show version and install paths")
    p_info.add_argument("--root", default=".")
    p_info.set_defaults(func=cmd_info)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
