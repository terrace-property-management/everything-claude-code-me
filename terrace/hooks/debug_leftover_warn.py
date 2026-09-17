#!/usr/bin/env python3
"""PostToolUse hook (Edit): warn about stray print() calls in edited .py files.

Ported idea from the original's console.log warning hook, swapped to
Python's equivalent debug leftover (bare `print(...)` calls). Pairs with
stop_debug_sweep.py, which does the same check as a final sweep over the
whole diff -- this one gives per-edit feedback, the Stop hook catches
anything missed across a multi-edit session.

Contract: always allow, never blocks (informational only -- like the
original, this warns rather than blocks, since a print() call is often
intentional CLI output in this stack's tools/ scripts and false positives
would be common).

Reads stdin JSON, and if tool_input.file_path is a .py file that exists,
scans it for print( calls and prints up to 5 matches with line numbers to
stderr. Echoes stdin back to stdout, exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PRINT_RE = re.compile(r"(?<![\w.])print\s*\(")


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
            text = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""

        matches = [
            f"{i + 1}: {line.strip()}"
            for i, line in enumerate(text.splitlines())
            if PRINT_RE.search(line)
        ]

        if matches:
            sys.stderr.write(f"[Hook] WARNING: print( found in {file_path}\n")
            for m in matches[:5]:
                sys.stderr.write(f"{m}\n")
            sys.stderr.write("[Hook] Remove debug print() calls before committing\n")

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
