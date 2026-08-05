"""Compatibility: pure-stdlib MCP module always importable."""

from __future__ import annotations

from taskhandoff.mcp_server import PROTOCOL_VERSION, SERVER_NAME, TOOLS, main


def test_mcp_module_importable() -> None:
    assert SERVER_NAME == "TaskHandoff"
    assert PROTOCOL_VERSION
    assert "handoff_recall" in TOOLS
    assert callable(main)
