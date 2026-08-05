# Terminal demo (copy-paste)

GIF 预览：[`assets/terminal-demo.gif`](../assets/terminal-demo.gif)  
怎么录 / 怎么重渲：[how-to-record-gif.md](how-to-record-gif.md)

Assumes: `pip install -e .` from the TaskHandoff repo.

```bash
# 0) version
handoff --version

# 1) init in a throwaway project
mkdir -p /tmp/th-demo && cd /tmp/th-demo
echo 'print("hi")' > app.py
handoff init --root .

# 2) save with auto (git optional)
handoff save --root . --auto \
  --goal "Demo long task resume" \
  --done "Scaffolded app.py" \
  --next "Add tests" \
  --next "Document CLI" \
  --next "Ship handoff pack" \
  --memory-delta "Demo prefers compact handoffs"

# 3) new-session style brief
handoff recall --root . --brief

# 4) health
handoff doctor --root .
handoff status --root .
```

Expected highlights:

- `.handoff/handoffs/LATEST.md` exists
- `recall --brief` prints `Resume brief` + goal + 3 next actions
- `doctor` prints `result: OK`

## MCP one-liner smoke (no client needed)

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python -m taskhandoff.mcp_server 2>/dev/null
```

You should see JSON responses for `initialize` and six tools.
