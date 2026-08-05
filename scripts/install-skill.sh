#!/usr/bin/env bash
# Install TaskHandoff as a Claude Code / agent skill.
# Usage:
#   ./scripts/install-skill.sh
#   ./scripts/install-skill.sh ~/.claude/skills/task-handoff

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$HOME/.claude/skills/task-handoff}"

mkdir -p "$TARGET"
for name in SKILL.md templates scripts taskhandoff references pyproject.toml README.md; do
  if [[ -e "$ROOT/$name" ]]; then
    rm -rf "$TARGET/$name"
    cp -R "$ROOT/$name" "$TARGET/$name"
  fi
done

echo "Installed skill to: $TARGET"
echo "Then: pip install -e \"$ROOT\""
echo "Or in a project: handoff init --root ."
