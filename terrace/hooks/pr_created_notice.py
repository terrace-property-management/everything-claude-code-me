#!/usr/bin/env python3
"""PostToolUse hook (Bash): log the PR URL and review command after `gh pr create`.

Ported directly from the original's regex-on-stdout idea. Adapted: the
suggested follow-up is still `gh pr review <n> --repo <owner/repo>` (that
part is stack-agnostic), but this also mentions this repo's actual
close-the-loop step (`gh pr merge --squash --delete-branch` after review, per
CLAUDE.md's worktree workflow), so the reminder matches how PRs are actually
closed out here instead of just how they're reviewed.

Contract: never blocks. Reads the PostToolUse payload, looks for a GitHub PR
URL in the command's output (tries a few plausible field shapes since the
exact key name for tool output has changed across Claude Code versions),
prints a notice to stderr if found, echoes stdin back to stdout, exits 0.
"""

from __future__ import annotations

import json
import re
import sys

PR_URL_RE = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)")


def extract_output_text(payload: dict) -> str:
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "gh pr create" not in command:
        return ""

    response = payload.get("tool_response")
    if response is None:
        response = payload.get("tool_output")

    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        for key in ("output", "stdout", "content", "text"):
            value = response.get(key)
            if isinstance(value, str):
                return value
    return ""


def main() -> int:
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        sys.stdout.write(raw)
        return 0

    text = extract_output_text(payload)
    match = PR_URL_RE.search(text)

    if match:
        url = match.group(0)
        repo = match.group(1)
        pr_number = match.group(2)
        sys.stderr.write(f"[Hook] PR created: {url}\n")
        sys.stderr.write(f"[Hook] To review: gh pr review {pr_number} --repo {repo}\n")
        sys.stderr.write(
            f"[Hook] After review is green: gh pr merge {pr_number} --repo {repo} "
            "--squash --delete-branch\n"
        )

    sys.stdout.write(raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
