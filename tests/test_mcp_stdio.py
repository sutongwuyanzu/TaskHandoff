"""Unit tests for pure-stdlib MCP JSON-RPC handlers (no network)."""

from __future__ import annotations

import json
from pathlib import Path

from taskhandoff.mcp_server import TOOLS, _call_tool, _handle, _tools_list_payload


def test_tools_list_has_core_tools() -> None:
    payload = _tools_list_payload()
    names = {t["name"] for t in payload["tools"]}
    assert {
        "handoff_init",
        "handoff_save",
        "handoff_recall",
        "handoff_status",
        "handoff_memory_append",
        "handoff_doctor",
    } <= names
    for t in payload["tools"]:
        assert "inputSchema" in t
        assert t["description"]


def test_initialize_handler() -> None:
    resp = _handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}},
        }
    )
    assert resp is not None
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "TaskHandoff"
    assert "tools" in resp["result"]["capabilities"]


def test_tools_list_rpc() -> None:
    resp = _handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    assert resp is not None
    assert len(resp["result"]["tools"]) == len(TOOLS)


def test_tool_call_init_save_recall(tmp_path: Path) -> None:
    root = str(tmp_path)
    (tmp_path / "x.txt").write_text("hi", encoding="utf-8")

    r = _call_tool("handoff_init", {"root": root})
    assert r["isError"] is False
    assert (tmp_path / ".handoff" / "MEMORY.md").is_file()

    r = _call_tool(
        "handoff_save",
        {
            "root": root,
            "goal": "MCP polish",
            "next_actions": ["a", "b", "c"],
            "auto": False,
            "done": ["init"],
        },
    )
    assert r["isError"] is False, r
    assert (tmp_path / ".handoff" / "handoffs" / "LATEST.md").is_file()

    r = _call_tool("handoff_recall", {"root": root, "brief": True})
    assert r["isError"] is False
    text = r["content"][0]["text"]
    assert "MCP polish" in text
    assert "Resume brief" in text

    r = _call_tool("handoff_doctor", {"root": root})
    assert r["isError"] is False
    assert "OK" in r["content"][0]["text"]


def test_unknown_tool() -> None:
    r = _call_tool("nope", {})
    assert r["isError"] is True


def test_tools_call_rpc(tmp_path: Path) -> None:
    root = str(tmp_path)
    resp = _handle(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "handoff_init", "arguments": {"root": root}},
        }
    )
    assert resp is not None
    assert resp["id"] == 9
    assert "content" in resp["result"]
    # round-trip json serializable
    json.dumps(resp)
