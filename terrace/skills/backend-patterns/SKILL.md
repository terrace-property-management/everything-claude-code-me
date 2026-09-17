---
name: backend-patterns
description: Backend patterns for terrace-control-plane — FastMCP tools, not REST; the fixed write-tool pattern; scope ordering; the _result() response shape. Rewritten from scratch against this stack rather than adapted from the Express/Next.js original, which had no equivalent surface.
---

# Backend Patterns — terrace-control-plane

The original skill's REST conventions (resource URLs, repository classes, Express
middleware) don't map here — there are no routes. This stack's backend surface is a
FastMCP server exposing named tools over one MCP, backed by psycopg3 and plain SQL.
Everything below comes straight from `.claude/agents/fullstack-developer.md`; this
skill exists so the same invariants are reachable without re-deriving them from that
agent file each time.

## The tool surface

Two modules, split by intent:
- `server/read_tools.py` — tools named `get_`, `list_`. No side effects.
- `server/write_tools.py` — tools named `upsert_`, `record_`, `load_`. Narrow and
  enumerated. **There is no generic write tool** — every write path is its own named,
  reviewed function.

## Scope ordering

```python
SCOPE_ORDER = {"reader": 0, "producer": 1, "admin": 2}
```

Every tool has an entry in `TOOL_MIN_SCOPE`. Pick the honest floor:
- **reader** — Ivania, Darlynn, dashboards. Never a raw connector payload, never a
  tenant-bearing row.
- **producer** — anything returning tenant/applicant data or a raw connector payload,
  at minimum.
- **admin** — reserved for genuinely destructive or cross-entity operations.

An omitted `TOOL_MIN_SCOPE` entry is not a safe default. It's a bug, and it's caught by
`tests/test_guards.py`.

## PII handling

- **`PII_TOOLS`** — any tool whose rows can carry tenant or applicant data goes here.
  Membership refuses credentials presented in the URL, because host logs capture query
  strings.
- **`READER_STRIPPED_COLUMNS`** — any tenant-bearing column added to a table that a
  reader-scope tool can reach goes here, and the tool calls `strip_for_reader(rows,
  scope)` on the way out. This is tested once, at the boundary
  (`tests/test_reader_pii_projection.py`) — reuse it, never re-derive the stripping
  logic in a new tool.

## The fixed write-tool pattern

```python
from __future__ import annotations

def upsert_tenancy(payload: dict, scope: str) -> dict:
    gate("upsert_tenancy", scope)  # first call, every exit path logs via log_call()

    is_valid, error = validate_tenancy_payload(payload)  # pure function, server/guards.py
    if not is_valid:
        log_call("upsert_tenancy", scope, ok=False, reason=error)
        return {"error": error}

    write_row(payload)  # the actual write

    row = read_back(payload["tenancy_id"])  # never skip this
    if row is None or not matches(row, payload):
        log_call("upsert_tenancy", scope, ok=False, reason="read-back mismatch")
        return {"error": "write did not land — read-back mismatch"}

    log_call("upsert_tenancy", scope, ok=True)
    return {"rows": [row], "count": 1, "source": "tenancy", "scope": scope,
            "as_of": row["updated_at"]}
```

**Never return success from an unread-back write.** This is the single most
enforced invariant in this codebase — a `run_log` row with `status='ok'` and
`verified=false` is refused by a CHECK constraint on purpose, and the same discipline
applies at the tool level even where no CHECK constraint exists to catch it
mechanically.

## The `_result()` response shape — every read tool

```python
def _result(rows: list[dict], source: str, scope: str, as_of: str) -> dict:
    return {"rows": rows, "count": len(rows), "source": source, "scope": scope,
            "as_of": as_of}
```

A figure without a source and an as-of is not a figure — this is `CLAUDE.md`'s rule,
and every tool carries it. A new read tool that returns a bare list instead of this
shape does not ship.

## Bounded output, reported bound

A list/query tool that can return a whole table does not ship either. The house
pattern:

```python
ROW_CAP = 500

def query_readonly(...) -> dict:
    rows = fetch(limit=ROW_CAP + 1)
    truncated = len(rows) > ROW_CAP
    rows = rows[:ROW_CAP]
    return {"rows": rows, "returned": len(rows), "row_cap_hit": truncated, ...}
```

Never a silent `LIMIT` — the cap is part of the contract, not an implementation detail.

## Producers, not background job queues

There's no in-memory job queue pattern here — a producer is a CLI in `tools/` or a
committed lane prompt in `schedules/prompts/`, and its shape is fixed:

```
start_run(producer, runtime) → do the work → verify the destination → finish_run(...)
```

Write the `run_log` row on failure too — a lane that fails silently is
indistinguishable from one that never fired. Exit 0 having moved nothing is
`PRODUCED_NOTHING`, a failure graded at declared outputs, not a pass.

## Routing rule — which substrate reaches the database

`tools/` CLI producers use psycopg directly, where `DATABASE_URL` exists. Cloud lanes
have no filesystem and no `DATABASE_URL` — they reach the database only through scoped
MCP tools. `dashboard/` never imports psycopg; it's a client of the MCP at reader scope,
same as any non-Claude consumer must be.

## What this replaces from the original skill

No repository-pattern classes, no Express middleware, no Redis cache-aside layer, no
JWT verification, no rate limiter — none of that surface exists here. The nearest
things this stack has to "caching" and "auth" are the read tool's `as_of` freshness
contract and the scope-token gate, respectively, both covered above.
