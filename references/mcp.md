# TaskHandoff MCP server

**Zero extra dependencies.** Pure stdlib stdio MCP (newline-delimited JSON-RPC), wrapping the same `.handoff/` contract as the CLI.

## Install / run

```bash
git clone https://github.com/sutongwuyanzu/TaskHandoff.git
cd TaskHandoff
pip install -e .          # no [mcp] extra required

handoff-mcp
# or
python -m taskhandoff.mcp_server
```

Stdout = MCP wire. Logs go to **stderr**.

## Tools

| Tool | Mirrors CLI | Notes |
|------|-------------|--------|
| `handoff_init` | `handoff init` | once per project |
| `handoff_save` | `handoff save` | default `auto=true` |
| `handoff_recall` | `handoff recall` | default `brief=true` |
| `handoff_status` | `handoff status` | |
| `handoff_memory_append` | `handoff memory --append` | empty text = show MEMORY |
| `handoff_doctor` | `handoff doctor` | secret scan |

## Client config

Sample: [examples/mcp-config.sample.json](../examples/mcp-config.sample.json)

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

After `pip install -e .` and `handoff-mcp` on PATH:

```json
{
  "mcpServers": {
    "task-handoff": {
      "command": "handoff-mcp"
    }
  }
}
```

Works with Claude Desktop, Cursor, and other MCP clients that launch a local stdio server.

## Agent usage pattern

1. Session start → `handoff_recall` (`brief=true`)
2. Work…
3. Checkpoint / end → `handoff_save` (`auto=true`, set `goal` + `next_actions`)
4. Durable fact → `handoff_memory_append`

## Design

- One storage format for Skill / CLI / MCP
- No second framework dependency for MCP
- Unit-tested JSON-RPC handlers (`tests/test_mcp_stdio.py`)
