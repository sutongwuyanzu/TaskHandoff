#!/usr/bin/env bash
# Thin wrapper — prefer session_start.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export HANDOFF_ROOT="${HANDOFF_ROOT:-$(pwd)}"
exec python3 "${ROOT}/examples/hooks/session_start.py"
