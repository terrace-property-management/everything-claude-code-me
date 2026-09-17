#!/usr/bin/env python3
"""PostToolUse hook (Edit): lint .py files with `ruff check` after edits.

Ported idea from the original's tsc-on-edit hook. There's no repo-wide
mypy config in terrace-control-plane (checked: no mypy.ini/setup.cfg
[mypy]/pyproject [tool.mypy] section anywhere in that repo as of
2026-09-17), so this only runs `ruff check`, skipping mypy entirely rather
than guessing at config that doesn't exist.

Unlike the original -- which had to grep a whole-project tsc run for lines
mentioning the edited file (tsc has no single-file mode that respects
project config) -- `ruff check <file>` is already scoped to just that file,
so the "filter for lines mentioning this file" step is close to a no-op
here. It's kept anyway as a defensive filter in case ruff's output ever
includes other paths (e.g. via noqa/config diagnostics). Runs with
`--output-format=concise` (one line per diagnostic, each prefixed with the
file path) rather than ruff's newer multi-line default format, since a
multi-line diagnostic would otherwise get shredded by that per-line filter.

Contract: always allow, never blocks. Reads stdin JSON, runs `ruff check
<file>` for edited .py files, prints up to 10 matching lines to stderr,
echoes stdin back to stdout, exits 0.
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
            result = subprocess.run(
                ["ruff", "check", "--output-format=concise", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            combined = (result.stdout or "") + (result.stderr or "")
            lines = [line for line in combined.splitlines() if file_path in line]
            if lines:
                sys.stderr.write("\n".join(lines[:10]) + "\n")
        except (OSError, subprocess.TimeoutExpired):
            pass  # best-effort only; never block on a lint-runner failure

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
