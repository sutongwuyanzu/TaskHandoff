"""TaskHandoff MCP server (stdio).

Exposes the same .handoff/ contract as the CLI so coding agents can
init / save / recall / status / memory / doctor without shelling out.

Run:
  pip install -e ".[mcp]"
  handoff-mcp
  # or
  python -m taskhandoff.mcp_server

Claude Desktop / Cursor example (stdio):
  command: python
  args: ["-m", "taskhandoff.mcp_server"]
  # after: pip install -e ".[mcp]" in the TaskHandoff repo (or pip install taskhandoff[mcp])
"""

from __future__ import annotations

import argparse
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import List, Optional

from taskhandoff import cli


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _run(fn, ns: argparse.Namespace) -> str:
    """Run a CLI command function and capture stdout/stderr."""
    out_buf = StringIO()
    err_buf = StringIO()
    code = 0
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        try:
            code = int(fn(ns) or 0)
        except SystemExit as e:
            code = int(e.code) if e.code not in (None,) else 1
        except Exception as e:  # noqa: BLE001 — surface tool errors to the agent
            return f"[error] {type(e).__name__}: {e}"
    text = (out_buf.getvalue() + err_buf.getvalue()).strip()
    if code != 0:
        return f"[exit {code}]\n{text}".strip()
    return text or "ok"


def build_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "MCP extra not installed. Run:\n"
            '  pip install -e ".[mcp]"\n'
            "or:\n"
            "  pip install 'mcp>=1.0'\n"
        ) from e

    mcp = FastMCP(
        "TaskHandoff",
        instructions=(
            "Long-task project memory and cross-session handoff. "
            "State lives in the project's .handoff/ directory. "
            "On session start, call handoff_recall(brief=true). "
            "Before ending a long session, call handoff_save (prefer auto=true)."
        ),
    )

    @mcp.tool()
    def handoff_init(root: str = ".", language: str = "zh-CN") -> str:
        """Initialize .handoff/ memory layout in a project (once per repo)."""
        return _run(cli.cmd_init, _ns(root=root, language=language))

    @mcp.tool()
    def handoff_save(
        root: str = ".",
        goal: str = "",
        summary: str = "",
        done: Optional[List[str]] = None,
        doing: Optional[List[str]] = None,
        blocked: Optional[List[str]] = None,
        decision: Optional[List[str]] = None,
        question: Optional[List[str]] = None,
        file: Optional[List[str]] = None,
        command: Optional[List[str]] = None,
        link: Optional[List[str]] = None,
        next_actions: Optional[List[str]] = None,
        memory_delta: Optional[List[str]] = None,
        body: str = "",
        auto: bool = True,
        allow_secrets: bool = False,
        agent_note: str = "task-handoff-mcp",
    ) -> str:
        """Save a handoff pack. Prefer auto=true so git + previous handoff fill gaps.

        next_actions: up to 3 concrete next steps for the following session.
        Never include API keys or tokens.
        """
        return _run(
            cli.cmd_save,
            _ns(
                root=root,
                goal=goal,
                summary=summary,
                done=done or [],
                doing=doing or [],
                blocked=blocked or [],
                decision=decision or [],
                question=question or [],
                file=file or [],
                command=command or [],
                link=link or [],
                next=next_actions or [],
                memory_delta=memory_delta or [],
                body=body,
                auto=auto,
                allow_secrets=allow_secrets,
                agent_note=agent_note,
                todos_json="",
            ),
        )

    @mcp.tool()
    def handoff_recall(
        root: str = ".",
        budget: int = 2500,
        brief: bool = True,
    ) -> str:
        """Load handoff context for a new session. Default brief=true (token-thrifty)."""
        return _run(
            cli.cmd_recall,
            _ns(root=root, budget=budget, brief=brief, out=""),
        )

    @mcp.tool()
    def handoff_status(root: str = ".") -> str:
        """Show whether .handoff/ exists and summarize LATEST goal / next actions."""
        return _run(cli.cmd_status, _ns(root=root))

    @mcp.tool()
    def handoff_memory_append(root: str = ".", text: str = "") -> str:
        """Append durable project memory (prefs, architecture, pitfalls). Empty text = show MEMORY.md."""
        return _run(
            cli.cmd_memory,
            _ns(root=root, append=text, allow_secrets=False),
        )

    @mcp.tool()
    def handoff_doctor(root: str = ".") -> str:
        """Health-check .handoff/ layout and scan LATEST.md for possible secrets."""
        return _run(cli.cmd_doctor, _ns(root=root))

    return mcp


def main(argv: Optional[List[str]] = None) -> int:
    # argv unused; stdio server
    _ = argv
    mcp = build_mcp()
    mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
