"""TaskHandoff MCP server — pure stdlib stdio (newline-delimited JSON-RPC).

Zero extra dependencies. Compatible with common MCP clients that speak
JSON-RPC over stdin/stdout (one JSON object per line).

Run:
  handoff-mcp
  python -m taskhandoff.mcp_server

Logging goes to stderr only — stdout is the MCP wire.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any, Callable, Dict, List, Optional

from taskhandoff import __version__, cli

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "TaskHandoff"


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _run_cli(fn: Callable, ns: argparse.Namespace) -> str:
    out_buf = StringIO()
    err_buf = StringIO()
    code = 0
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        try:
            code = int(fn(ns) or 0)
        except SystemExit as e:
            code = int(e.code) if e.code not in (None,) else 1
        except Exception as e:  # noqa: BLE001
            return f"[error] {type(e).__name__}: {e}"
    text = (out_buf.getvalue() + err_buf.getvalue()).strip()
    if code != 0:
        return f"[exit {code}]\n{text}".strip()
    return text or "ok"


def tool_init(args: Dict[str, Any]) -> str:
    return _run_cli(
        cli.cmd_init,
        _ns(root=str(args.get("root") or "."), language=str(args.get("language") or "zh-CN")),
    )


def tool_save(args: Dict[str, Any]) -> str:
    next_actions = args.get("next_actions") or args.get("next") or []
    if isinstance(next_actions, str):
        next_actions = [next_actions]
    def _list(key: str) -> List[str]:
        v = args.get(key) or []
        if isinstance(v, str):
            return [v]
        return [str(x) for x in v]

    return _run_cli(
        cli.cmd_save,
        _ns(
            root=str(args.get("root") or "."),
            goal=str(args.get("goal") or ""),
            summary=str(args.get("summary") or ""),
            done=_list("done"),
            doing=_list("doing"),
            blocked=_list("blocked"),
            decision=_list("decision"),
            question=_list("question"),
            file=_list("file"),
            command=_list("command"),
            link=_list("link"),
            next=[str(x) for x in next_actions],
            memory_delta=_list("memory_delta"),
            body=str(args.get("body") or ""),
            auto=bool(args.get("auto", True)),
            allow_secrets=bool(args.get("allow_secrets", False)),
            agent_note=str(args.get("agent_note") or "task-handoff-mcp"),
            todos_json="",
        ),
    )


def tool_recall(args: Dict[str, Any]) -> str:
    return _run_cli(
        cli.cmd_recall,
        _ns(
            root=str(args.get("root") or "."),
            budget=int(args.get("budget") or 2500),
            brief=bool(args.get("brief", True)),
            out="",
        ),
    )


def tool_status(args: Dict[str, Any]) -> str:
    return _run_cli(cli.cmd_status, _ns(root=str(args.get("root") or ".")))


def tool_memory(args: Dict[str, Any]) -> str:
    text = args.get("text") or args.get("append") or ""
    return _run_cli(
        cli.cmd_memory,
        _ns(root=str(args.get("root") or "."), append=str(text), allow_secrets=False),
    )


def tool_doctor(args: Dict[str, Any]) -> str:
    return _run_cli(cli.cmd_doctor, _ns(root=str(args.get("root") or ".")))


TOOLS: Dict[str, Dict[str, Any]] = {
    "handoff_init": {
        "description": "Initialize .handoff/ memory layout in a project (once per repo).",
        "handler": tool_init,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Project root path", "default": "."},
                "language": {"type": "string", "default": "zh-CN"},
            },
        },
    },
    "handoff_save": {
        "description": (
            "Save a long-task handoff pack into .handoff/. "
            "Prefer auto=true. Provide goal and up to 3 next_actions when possible. "
            "Never include API keys or tokens."
        ),
        "handler": tool_save,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "goal": {"type": "string"},
                "summary": {"type": "string"},
                "done": {"type": "array", "items": {"type": "string"}},
                "doing": {"type": "array", "items": {"type": "string"}},
                "blocked": {"type": "array", "items": {"type": "string"}},
                "decision": {"type": "array", "items": {"type": "string"}},
                "question": {"type": "array", "items": {"type": "string"}},
                "file": {"type": "array", "items": {"type": "string"}},
                "command": {"type": "array", "items": {"type": "string"}},
                "link": {"type": "array", "items": {"type": "string"}},
                "next_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Up to 3 next steps for the following session",
                },
                "memory_delta": {"type": "array", "items": {"type": "string"}},
                "body": {"type": "string"},
                "auto": {"type": "boolean", "default": True},
                "allow_secrets": {"type": "boolean", "default": False},
            },
        },
    },
    "handoff_recall": {
        "description": (
            "Load handoff context for a new session. "
            "Default brief=true returns a short resume brief (token-thrifty)."
        ),
        "handler": tool_recall,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "budget": {"type": "integer", "default": 2500},
                "brief": {"type": "boolean", "default": True},
            },
        },
    },
    "handoff_status": {
        "description": "Show .handoff/ status, goal, and next actions.",
        "handler": tool_status,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
            },
        },
    },
    "handoff_memory_append": {
        "description": "Append durable project memory, or show MEMORY.md if text is empty.",
        "handler": tool_memory,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "text": {"type": "string", "description": "Markdown fragment to append"},
            },
        },
    },
    "handoff_doctor": {
        "description": "Health-check .handoff/ and scan LATEST.md for possible secrets.",
        "handler": tool_doctor,
        "schema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
            },
        },
    },
}


def _tools_list_payload() -> Dict[str, Any]:
    tools = []
    for name, meta in TOOLS.items():
        tools.append(
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta["schema"],
            }
        )
    return {"tools": tools}


def _call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    meta = TOOLS.get(name)
    if not meta:
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            "isError": True,
        }
    try:
        text = meta["handler"](arguments or {})
        return {"content": [{"type": "text", "text": text}], "isError": text.startswith("[exit ") or text.startswith("[error]")}
    except Exception as e:  # noqa: BLE001
        return {
            "content": [{"type": "text", "text": f"{type(e).__name__}: {e}\n{traceback.format_exc()}"}],
            "isError": True,
        }


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _write(msg: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications (no id) — no response
    if msg_id is None and method:
        return None

    if method == "initialize":
        client_version = (params.get("protocolVersion") if isinstance(params, dict) else None) or PROTOCOL_VERSION
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": client_version if client_version else PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
                "instructions": (
                    "Long-task project memory and cross-session handoff. "
                    "State lives in the project's .handoff/ directory. "
                    "On session start call handoff_recall(brief=true). "
                    "Before ending a long session call handoff_save(auto=true)."
                ),
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": _tools_list_payload()}

    if method == "tools/call":
        name = params.get("name") if isinstance(params, dict) else None
        arguments = params.get("arguments") if isinstance(params, dict) else {}
        result = _call_tool(str(name or ""), arguments if isinstance(arguments, dict) else {})
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}

    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}

    # Unknown method
    if method:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32600, "message": "Invalid Request"},
    }


def serve_stdio() -> int:
    _log(f"{SERVER_NAME} MCP v{__version__} listening on stdio (NDJSON JSON-RPC)")
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            _log(f"bad json: {e}")
            continue
        if not isinstance(msg, dict):
            continue
        # notifications/initialized etc.
        if msg.get("method") and msg.get("id") is None:
            continue
        resp = _handle(msg)
        if resp is not None:
            _write(resp)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    _ = argv
    return serve_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
