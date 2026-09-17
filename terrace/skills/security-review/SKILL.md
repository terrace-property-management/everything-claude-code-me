---
name: security-review
description: Security review checklist for terrace-control-plane — SQL injection via raw psycopg3, Tier R secret shapes, PII scope, read-only-external-systems. Kept consistent with terrace/agents/security-reviewer.md; this is not an OWASP web checklist because there is no browser-facing surface to check.
---

# Security Review — terrace-control-plane

This is the skill-level companion to `terrace/agents/security-reviewer.md` — same
reasoning, same checklist, kept in sync deliberately. The original skill's OWASP
Top 10 web checklist (XSS, CSRF, CORS, JWT-in-localStorage, RLS policies) targets a
browser-facing app with client-side JS. `dashboard/app.py` is server-rendered Starlette
HTML with no client-side JavaScript — most of that surface doesn't exist here, and a
checklist that pretends it does wastes the review on findings that can't occur while
missing the ones that can.

## When to activate

- Adding or editing a raw SQL query anywhere (loaders, tools, MCP tool bodies).
- Adding a new MCP tool, especially one that can return tenant or applicant data.
- Touching `server/guards.py`'s `TOOL_MIN_SCOPE`, `PII_TOOLS`, or
  `READER_STRIPPED_COLUMNS`.
- Before a PR that touches anything under `server/`, `loaders/`, or `schema/`.

## 1. SQL injection — parameterization discipline

No ORM here, so there's no "use it safely" fallback.

```python
# NEVER
cur.execute(f"SELECT * FROM tenancy WHERE area_id = '{area_id}'")

# ALWAYS
cur.execute("SELECT * FROM tenancy WHERE area_id = %s", (area_id,))
```

Verification: grep every new `cur.execute` / `conn.execute` call in the diff for
f-strings or `%`-formatting anywhere near the SQL text. Treat any hit as CRITICAL
regardless of whether the input looks attacker-controlled today.

## 2. Tier R secret shapes

`tools/history_scan.py` scans for: SSN/ITIN, card numbers, bank routing/account
numbers, government IDs, private keys, API keys, and credentialled connection strings.
Check the diff — including test fixtures and migration comments — for any of these,
plus the ordinary hardcoded-credential case:

```python
# NEVER
DATABASE_URL = "postgresql://user:hunter2@host/db"

# ALWAYS
DATABASE_URL = os.environ["DATABASE_URL"]
```

It no longer scans for tenant names (ordinary working data here per decision #67), but
never put a real tenant or applicant name in a fixture, test, or commit message anyway
— that's a separate PII rule with the same enforcement weight.

## 3. PII scope — this stack's access-control equivalent

There's no user-facing auth surface to review; there is scope. Checklist:

- [ ] Every new tool has a `TOOL_MIN_SCOPE` entry — an omission is a bug, not a
      default.
- [ ] Any tool returning tenant/applicant data or a raw connector payload is in
      `PII_TOOLS`.
- [ ] Any new tenant-bearing column reachable at reader scope is added to
      `READER_STRIPPED_COLUMNS`, and the tool calls `strip_for_reader` on the way out.
- [ ] No new consumer (dashboard page, board, external reader) imports psycopg
      directly — `tcp_readonly` has no column-level restriction, so bypassing the MCP
      bypasses PII stripping entirely.

## 4. Read-only on every external system

Never write to Re-Leased, QBO, DocuSign, Gmail, Outlook, Notion, or Zillow — draft/stage
only. For subagents specifically: `tools` must be enumerated from `LOCAL_TOOLS`
(`Read, Grep, Glob, Bash, Edit, Write, NotebookEdit, TodoWrite, WebFetch, WebSearch`)
with **no `mcp__*` entry** — `tests/test_agent_definitions.py` enforces this. Omitting
the connector makes the write capability *absent*, not merely forbidden; treat any PR
that adds an `mcp__*` grant to an agent's `tools` list as a blocking finding.

## 5. Write-tool correctness as a security property

A write tool that reports success without reading back what it wrote is a security
defect here, not just a quality one — `run_log` refuses `status='ok'` with
`verified=false` by a CHECK constraint for exactly this reason. Check every new write
tool for validate → write → read back → return.

## What this checklist deliberately excludes

CSRF tokens, Content-Security-Policy, XSS sanitization, CORS configuration, rate
limiting on "endpoints", password hashing — none of these apply to a server-rendered
no-JS dashboard with no username/password auth and no HTTP routes (only MCP tool calls
gated by scope). Including them would pad the review with findings that can't fire.

## Pre-merge checklist

- [ ] No unparameterized SQL.
- [ ] No Tier R shape or hardcoded credential in the diff.
- [ ] Every new tool has `TOOL_MIN_SCOPE`, and PII tools have `PII_TOOLS` +
      `READER_STRIPPED_COLUMNS` entries where applicable.
- [ ] No new `mcp__*` grant on any subagent.
- [ ] Every new write tool proves read-back in its tests.
- [ ] `uv run pytest -q` and `uv run ruff check .` both clean.
