# TaskHandoff MCP server

Thin MCP adapter over the same `.handoff/` contract and CLI logic.

## Install

```bash
git clone https://github.com/sutongwuyanzu/TaskHandoff.git
cd TaskHandoff
pip install -e ".[mcp]"
```

## Run (stdio)

```bash
handoff-mcp
# or
python -m taskhandoff.mcp_server
```

## Tools

| Tool | Mirrors CLI | Notes |
|------|-------------|--------|
| `handoff_init` | `handoff init` | once per project |
| `handoff_save` | `handoff save` | default `auto=true` |
| `handoff_recall` | `handoff recall` | default `brief=true` |
| `handoff_status` | `handoff status` | |
| `handoff_memory_append` | `handoff memory --append` | empty text = show MEMORY |
| `handoff_doctor` | `handoff doctor` | secret scan |

## Client config examples

### Claude Desktop / generic stdio

```json
{
  "mcpServers": {
    "task-handoff": {
      "command": "python",
      "args": ["-m", "taskhandoff.mcp_server"],
      "cwd": "C:/path/to/TaskHandoff"
    }
  }
}
```

If the package is on `PATH` after install:

```json
{
  "mcpServers": {
    "task-handoff": {
      "command": "handoff-mcp"
    }
  }
}
```

### Cursor

Add the same stdio server in Cursor MCP settings (`command` + `args` as above).

## Agent usage pattern

1. Session start → `handoff_recall(root, brief=true)`
2. Work…
3. Session end / checkpoint → `handoff_save(root, auto=true, goal=..., next_actions=[...])`
4. Optional durable fact → `handoff_memory_append(root, text="...")`

## Design

- No second storage format — MCP and CLI share `taskhandoff.cli` command functions.
- Core package stays dependency-free; MCP is an **optional extra** (`pip install -e ".[mcp]"`).
