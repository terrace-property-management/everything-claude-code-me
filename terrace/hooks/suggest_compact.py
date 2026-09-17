#!/usr/bin/env python3
"""PreToolUse hook (Edit|Write): nudge /compact at a tool-call threshold.

Ported from the original suggest-compact.js. Behavior change from the
original: the default threshold is 68 instead of 50, and the nudge message
cites the Terrace context-economics finding (86.4% of a recent quarter's
spend was context re-read, not answers written; the measured mean was 33.8
turns/request, so ~2x that is used as the "you're past a normal request's
length" line) instead of a generic "consider /compact" message. This keeps
the same non-blocking, counter-file mechanism as the original -- it never
gates the tool call, it only prints a stderr nudge.

Contract: always allow. Reads stdin JSON, increments a per-session counter
file under the state dir, prints a nudge to stderr at the threshold and
every 25 calls after, echoes stdin back to stdout, exits 0.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


def state_dir() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    base = Path(project_dir) / ".claude" / "state" if project_dir else Path(tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    return base


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    session_id = payload.get("session_id") or str(os.getppid())
    threshold = int(os.environ.get("COMPACT_THRESHOLD", "68"))

    counter_file = state_dir() / f"tool-count-{session_id}.txt"

    try:
        existing = counter_file.read_text(encoding="utf-8").strip()
        count = int(existing) + 1 if existing else 1
    except (OSError, ValueError):
        count = 1

    try:
        counter_file.write_text(str(count), encoding="utf-8")
    except OSError:
        pass

    if count == threshold:
        sys.stderr.write(
            f"[StrategicCompact] {threshold} tool calls this session -- "
            "context re-read (not new work) was 86.4% of a recent quarter's spend "
            "here. If you're between phases, /compact now or write state to a file "
            "and continue fresh.\n"
        )
    elif count > threshold and count % 25 == 0:
        sys.stderr.write(
            f"[StrategicCompact] {count} tool calls -- good checkpoint for /compact "
            "if context is stale.\n"
        )

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
