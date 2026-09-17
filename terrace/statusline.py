#!/usr/bin/env python3
"""Claude Code statusline, rewritten from examples/statusline.json (bash+jq)
as a stdlib-only Python script.

Why: the original is a one-line bash script that shells out to `jq` for
every field and to `date`/`git`/`grep` for the rest. `jq` isn't guaranteed
to be installed on this Windows dev machine, and bash-vs-PowerShell is a
portability problem Claude Code hooks/statuslines don't need to have --
Claude Code invokes the configured `command` directly regardless of shell,
so a `python "<path>"` command sidesteps both issues. This keeps the exact
same visual design (colored segments: cwd, git branch + dirty marker,
context-remaining %, model, time, live todo count) and reads the same
stdin JSON contract.

Contract: reads one JSON object from stdin (the statusline payload Claude
Code provides), writes one line to stdout, always exits 0 -- a broken
statusline should degrade to something readable, never crash and leave the
UI blank.
"""

from __future__ import annotations

import getpass
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 24-bit ANSI colors, same palette as the original statusline.json.
BLUE = "\033[38;2;30;102;245m"      # cwd
GREEN = "\033[38;2;64;160;43m"      # git branch
YELLOW = "\033[38;2;223;142;29m"    # dirty marker, time
MAGENTA = "\033[38;2;136;57;239m"   # context remaining
CYAN = "\033[38;2;23;146;153m"      # username, todos
GRAY = "\033[38;2;76;79;105m"       # model name
RESET = "\033[0m"

TODO_RE = re.compile(r'"type"\s*:\s*"todo"')


def safe_get(d: dict, *path, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def git_info(cwd: str) -> tuple[str, bool]:
    """Return (branch, is_dirty). Empty branch means "not a git repo"."""
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "", False

    if branch_result.returncode != 0:
        return "", False

    branch = branch_result.stdout.strip()

    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False
    except (OSError, subprocess.TimeoutExpired):
        dirty = False

    return branch, dirty


def todo_count(transcript_path: str) -> int:
    if not transcript_path:
        return 0
    try:
        text = Path(transcript_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return len(TODO_RE.findall(text))


def shorten_home(path_str: str) -> str:
    if not path_str:
        return path_str
    home = str(Path.home())
    if home and path_str.startswith(home):
        return "~" + path_str[len(home):]
    return path_str


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    cwd = safe_get(payload, "workspace", "current_dir", default="") or ""
    model = safe_get(payload, "model", "display_name", default="") or ""
    remaining = safe_get(payload, "context_window", "remaining_percentage", default=None)
    transcript_path = safe_get(payload, "transcript_path", default="") or ""

    try:
        user = getpass.getuser()
    except Exception:
        user = ""

    display_cwd = shorten_home(cwd)
    branch, dirty = git_info(cwd)
    todos = todo_count(transcript_path)
    now = datetime.now().strftime("%H:%M")

    parts = [f"{CYAN}{user}{RESET}:{BLUE}{display_cwd}{RESET}"]

    if branch:
        marker = "*" if dirty else ""
        parts.append(f"{GREEN}{branch}{YELLOW}{marker}{RESET}")

    if remaining is not None:
        parts.append(f"{MAGENTA}ctx:{remaining}%{RESET}")

    parts.append(f"{GRAY}{model}{RESET} {YELLOW}{now}{RESET}")

    if todos > 0:
        parts.append(f"{CYAN}todos:{todos}{RESET}")

    sys.stdout.write(" ".join(parts) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # last-resort: never crash the statusline
        sys.stdout.write(f"[statusline error: {exc}]\n")
        sys.exit(0)
