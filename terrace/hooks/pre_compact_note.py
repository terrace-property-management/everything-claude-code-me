#!/usr/bin/env python3
"""PreCompact hook: log a timestamped marker before context compaction.

Ported from pre-compact.js, deliberately lighter: the original scanned
session-transcript .tmp files and appended a marker into whichever one was
active. That machinery isn't needed here -- this just appends one line
(timestamp, trigger, custom instructions if any) to a local compaction log
so there's a record of when/why compaction happened, without trying to
parse or rewrite transcript state.

Contract: never blocks. Reads stdin JSON, appends a line to
<state_dir>/compaction-log.txt, exits 0. Does not echo stdin (PreCompact
does not gate a tool call, so there's nothing to pass through).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
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

    trigger = payload.get("trigger", "unknown")
    custom = payload.get("custom_instructions", "")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = state_dir() / "compaction-log.txt"

    line = f"[{timestamp}] compaction triggered (trigger={trigger})"
    if custom:
        line += f" instructions={custom!r}"
    line += "\n"

    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass

    sys.stderr.write(f"[PreCompact] State noted before compaction ({log_path})\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
