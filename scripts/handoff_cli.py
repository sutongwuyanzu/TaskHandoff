#!/usr/bin/env python3
"""Backward-compatible entrypoint.

Prefer:
  pip install -e .
  handoff init --root .

Or:
  python -m taskhandoff init --root .
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file without installing the package
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from taskhandoff.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
