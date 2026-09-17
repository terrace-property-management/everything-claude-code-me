#!/usr/bin/env python3
"""PostToolUse hook (Edit): auto-format .py files with `ruff format`.

Ported idea from the original's Prettier-on-edit hook, swapped for this
stack's formatter. Same best-effort contract as the original: if ruff isn't
on PATH, or formatting fails for any reason, swallow the error and never
block -- an edit that already landed should not be undone by a formatter
hiccup.

Contract: always allow. Reads stdin JSON, and if tool_input.file_path ends
in .py and exists on disk, runs `ruff format <file>` (best effort). Echoes
stdin back to stdout, exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        sys.stdout.write(raw)
        return 0

    file_path = (payload.get("tool_input") or {}).get("file_path") or ""

    if file_path.endswith(".py") and Path(file_path).exists():
        try:
            subprocess.run(
                ["ruff", "format", file_path],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass  # best-effort only, same as the original's try/catch around prettier

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
