#!/usr/bin/env python3
"""SessionStart hook: report prior session state and current worktree/branch.

Ported from session-start.js, with the package-manager detection dropped
entirely (this stack only ever uses `uv` -- there is nothing to detect) and
a worktree/branch report added in its place, since terrace-control-plane
already runs a worktree-per-session workflow (see its CLAUDE.md) and
"which worktree/branch am I in" is a much more useful thing to surface at
session start here than "which JS package manager is this".

Contract: never blocks (SessionStart doesn't gate a tool call). Reads stdin
JSON (only to fail gracefully on malformed input), writes informational
lines to stderr, exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def state_dir() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    base = Path(project_dir) / ".claude" / "state" if project_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base


def git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def main() -> int:
    raw = sys.stdin.read()
    try:
        json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        pass  # informational hook only; malformed input is not fatal

    # Report recent session-state file, if suggest_compact/pre_compact_note
    # left one behind (state files aren't versioned across days, so "recent"
    # here just means "present").
    log_path = state_dir() / "compaction-log.txt"
    if log_path.exists():
        sys.stderr.write(f"[SessionStart] Prior compaction log found: {log_path}\n")

    # Report worktree/branch, since this repo's own workflow is worktree-based.
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    git_dir = git("rev-parse", "--git-dir")
    toplevel = git("rev-parse", "--show-toplevel")

    if branch:
        sys.stderr.write(f"[SessionStart] Branch: {branch}\n")
        if git_dir and "worktrees" in git_dir.replace("\\", "/"):
            sys.stderr.write(f"[SessionStart] In a git worktree ({toplevel})\n")
        elif toplevel:
            sys.stderr.write(f"[SessionStart] Primary checkout: {toplevel}\n")
    else:
        sys.stderr.write("[SessionStart] Not inside a git repository\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
