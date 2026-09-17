#!/usr/bin/env python3
"""PreToolUse hook: block stray .md/.txt file creation via Write.

Ported directly from the original Node hook (scripts/hooks in the upstream
fork) with the same allowlist logic. This is the one hook in the set that
enforces an already-written Terrace house rule ("don't create planning /
decision docs unless asked") that otherwise has zero mechanical enforcement.

Contract: reads the PreToolUse JSON payload from stdin. If the Write call's
file_path is a .md/.txt file NOT named README.md, CLAUDE.md, AGENTS.md or
CONTRIBUTING.md (anywhere in the path), print a reason to stderr and exit 1
(block). Otherwise echo the original stdin back to stdout and exit 0 (allow).
"""

from __future__ import annotations

import json
import re
import sys

ALLOWED = re.compile(r"(README|CLAUDE|AGENTS|CONTRIBUTING)\.md$")
BLOCKED_EXT = re.compile(r"\.(md|txt)$")


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed payload: fail open rather than block an unrelated tool call.
        sys.stdout.write(raw)
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""

    if BLOCKED_EXT.search(file_path) and not ALLOWED.search(file_path):
        sys.stderr.write("[Hook] BLOCKED: Unnecessary documentation file creation\n")
        sys.stderr.write(f"[Hook] File: {file_path}\n")
        sys.stderr.write(
            "[Hook] Only ask if this doc was explicitly requested; otherwise fold "
            "notes into README.md/CLAUDE.md or skip the file.\n"
        )
        return 1

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
