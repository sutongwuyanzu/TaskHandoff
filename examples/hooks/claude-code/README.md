# Claude Code hooks for TaskHandoff

## 1) Copy hook scripts into the project

From your **application repo** (not only TaskHandoff):

```bash
mkdir -p .claude/hooks/task-handoff
# if TaskHandoff is cloned nearby:
cp /path/to/TaskHandoff/examples/hooks/session_start.py .claude/hooks/task-handoff/
cp /path/to/TaskHandoff/examples/hooks/session_end.py   .claude/hooks/task-handoff/
```

Or install TaskHandoff and point commands at the package:

```bash
pip install -e /path/to/TaskHandoff
# then use: python -m taskhandoff ... inside custom wrappers
```

## 2) Merge settings fragment

Copy keys from [`settings.fragment.json`](settings.fragment.json) into:

- project: `.claude/settings.json` (share with team), or
- user: `~/.claude/settings.json`

Adjust the `command` path if your scripts live elsewhere.

### Minimal merged example

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/task-handoff/session_start.py\""
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/task-handoff/session_end.py\""
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PROJECT_DIR}/.claude/hooks/task-handoff/session_start.py\""
          }
        ]
      }
    ]
  }
}
```

## Behavior

| Event | Action |
|-------|--------|
| **SessionStart** | `handoff recall --brief` → stdout injected as context |
| **PreCompact** | same as start — re-inject brief before context shrinks |
| **SessionEnd** | `handoff save --auto` checkpoint (stderr log) |

## Env knobs

| Variable | Meaning |
|----------|---------|
| `HANDOFF_ROOT` | Force project root |
| `HANDOFF_GOAL` | Goal string for auto save |
| `HANDOFF_SUMMARY` | Summary line for auto save |
| `HANDOFF_SKIP=1` | Disable session_end save |
| `HANDOFF_FULL=1` | SessionStart prints full recall |

## Prerequisites

```bash
pip install -e /path/to/TaskHandoff
# in each app repo once:
handoff init --root .
```
