#!/usr/bin/env python3
"""Stop hook: final sweep for stray print() calls across modified .py files.

Ported idea from the original's Stop-hook console.log sweep. Runs once when
Claude finishes responding, over every file `git diff --name-only HEAD`
reports as changed (not just the last-edited one), catching leftovers from
edits made outside Claude Code's Edit tool (e.g. Bash-applied patches) that
debug_leftover_warn.py never sees.

Contract: never blocks -- Stop hooks in Claude Code CAN block (by exiting
1), but this one deliberately never does, matching the original, since a
stray print() is a lint-severity issue, not a correctness one. Reads stdin
only to fail gracefully on malformed input, exits 0 always.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PRINT_RE = re.compile(r"(?<![\w.])print\s*\(")


def git_dir_present() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def changed_python_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return [
        f
        for f in result.stdout.splitlines()
        if f.endswith(".py") and Path(f).exists()
    ]


def main() -> int:
    raw = sys.stdin.read()
    try:
        json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        pass

    if not git_dir_present():
        return 0

    found_any = False
    for f in changed_python_files():
        try:
            text = Path(f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(PRINT_RE.search(line) for line in text.splitlines()):
            sys.stderr.write(f"[Hook] WARNING: print( found in {f}\n")
            found_any = True

    if found_any:
        sys.stderr.write("[Hook] Remove debug print() statements before committing\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
