---
name: coding-standards
description: Coding standards for terrace-control-plane — Python 3.11+, ruff, no ORM/REST/client framework. Adapted from a TypeScript/React original; only the principles that transfer (naming, immutability-where-practical, no-hardcoded-secrets) survive, rewritten against real files in this stack.
---

# Coding Standards — terrace-control-plane

## Principles that transfer unchanged

- **Readability first, KISS, DRY, YAGNI** — same as any stack. No premature
  abstraction, no speculative generality.
- **Descriptive names, verb-noun functions** — `get_lease_expiry`, `is_blocked`,
  `strip_for_reader`, not `q`, `flag`, `x`.
- **Many small files** — high cohesion, low coupling. `server/read_tools.py` and
  `server/write_tools.py` are short and that's deliberate; match their density rather
  than growing one file past readability.

## Python conventions (this stack's real ones)

- **Python 3.11+, `uv` for the env, `ruff` for lint (line length 100), `pytest` for
  tests.** Type hints on every public function; `from __future__ import annotations`
  at the top of every file.
- **No ORM, no query builder.** psycopg3 with plain, parameterized SQL. There is no
  "use the ORM safely" fallback — a raw query is either parameterized or it's a
  vulnerability (see `terrace/agents/security-reviewer.md`).
- **No REST API.** FastMCP tools are the only public surface; tool names are verbs:
  `get_`, `list_`, `upsert_`, `record_`, `load_`.
- **No client-side framework, no build step, no npm.** `dashboard/app.py` is
  server-rendered Starlette HTML. There is nothing here for a "React best practices"
  section to apply to.

## Immutability — where it's practical here

Python doesn't have the spread-operator idiom the original relied on, and mutation is
sometimes the right call (a loader building up a batch, a row transform in a tight
loop) — don't force `{**dict, "key": value}` everywhere as ceremony. The rule that
actually matters in this stack is narrower and higher-stakes: **never mutate a snapshot
table's row in place.** Append-only tables (`rent_roll_snapshot`, `invoice_snapshot`)
are append-only because the history is the point — a loader that updates a snapshot row
instead of inserting a new one destroys provenance. Derived tables are upserted by
natural key on purpose; snapshots are not.

## No hardcoded secrets — same rule, this stack's shapes

```python
# WRONG
DATABASE_URL = "postgresql://user:hunter2@host/db"

# CORRECT
import os
DATABASE_URL = os.environ["DATABASE_URL"]
```

`.env` is gitignored. Beyond the generic API-key case, this repo's secret scanner
(`tools/history_scan.py`) specifically watches for **Tier R shapes**: SSN/ITIN, bank
account/routing numbers, card numbers, government IDs, private keys, and credentialled
connection strings. Never put a real tenant or applicant name in a fixture, test,
migration comment, prompt file, or commit message either — that's a PII rule, not a
secrets rule, but it's enforced the same way.

## Validation — pure functions in `server/guards.py`, not a schema library

The original used Zod at the API boundary. This stack's equivalent is a pure validator
function in `server/guards.py`, tested without a database:

```python
from __future__ import annotations

def validate_tenancy_payload(payload: dict) -> tuple[bool, str | None]:
    """Returns (is_valid, error_message). No I/O — testable in isolation."""
    if "area_id" not in payload:
        return False, "area_id is required"
    return True, None
```

Every write tool calls its validator before writing, per the
validate → write → read back → return pattern in `.claude/agents/fullstack-developer.md`.

## No `print()` left in committed code

The equivalent of the console.log ban. Structured logging via the existing `run_log` /
audit mechanisms, or nothing.

## Comments carry *why*, not *what*

```python
# WRONG — restates the code
# increment retry count
retry_count += 1

# RIGHT — records why, often with a date and a defect
# 2026-09-04: ¶3C's prorated-first-month case doesn't satisfy the prepaid-full-month
# condition, so the house convention (actual days) applies here, not the lease's 1/30th.
divisor = actual_days_in_month
```

A comment restating the code is noise; one that records what went wrong or why a
decision was made is the most valuable line in the file — don't strip these on sight
the way a generic linter pass might.

## Code smells to watch for (same list, Python-shaped)

- Functions over ~50 lines, files past a few hundred — split them.
- Deep nesting — prefer early returns.
- Magic numbers — name the constant, especially proration/deposit/ceiling values,
  which should live in the owning skill's rules, not be re-derived here at all (see
  `terrace/skills/backend-patterns/SKILL.md`).
