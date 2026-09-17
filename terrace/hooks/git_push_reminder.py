#!/usr/bin/env python3
"""PreToolUse hook (Bash): reminder before `git push`.

Ported in spirit from the original's git-push reminder. The original's
message was generic ("review changes before push... remove this hook to add
interactive review"); this one names the actual workflow this repo uses
(terrace-control-plane's CLAUDE.md worktree section): commit in the
worktree, push, `gh pr create` with a `phase-N: what changed` message, then
`gh pr merge --squash --delete-branch` after review is green -- and it
never pushes straight to main.

Contract: never blocks (a reminder, not a gate -- same as the original).
Reads stdin JSON, and if the Bash command contains `git push`, prints the
reminder to stderr. Echoes stdin back to stdout, exits 0.
"""

from __future__ import annotations

import json
import re
import sys

GIT_PUSH_RE = re.compile(r"\bgit\s+push\b")


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        sys.stdout.write(raw)
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""

    if GIT_PUSH_RE.search(command):
        sys.stderr.write(
            "[Hook] Reminder: never push straight to main. Push the branch, then "
            "`gh pr create` (message convention: `phase-N: what changed`), review "
            "the diff before AND after checks go green, then `gh pr merge --squash "
            "--delete-branch`.\n"
        )

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
