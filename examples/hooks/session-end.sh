#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export HANDOFF_ROOT="${HANDOFF_ROOT:-$(pwd)}"
exec python3 "${ROOT}/examples/hooks/session_end.py"
