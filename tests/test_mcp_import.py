"""MCP module loads tools without requiring a live stdio session."""

from __future__ import annotations

import importlib

import pytest


def test_mcp_extra_or_skip() -> None:
    pytest.importorskip("mcp")
    mod = importlib.import_module("taskhandoff.mcp_server")
    server = mod.build_mcp()
    # FastMCP keeps tools in internal registry; ensure build succeeds
    assert server is not None
    assert server.name == "TaskHandoff"