---
name: tdd-workflow
description: pytest-based TDD workflow for terrace-control-plane. Consistent with terrace/agents/tdd-guide.md — read that for the agent framing; this is the skill-level reference. No 80% coverage gate; the real invariant is validate-write-readback coverage on every write tool.
---

# TDD Workflow — terrace-control-plane

Same red-green-refactor discipline as any TDD practice; different tools, different
gate. Kept consistent with `terrace/agents/tdd-guide.md` — if you're editing one, check
the other still agrees.

## When to activate

- Adding a loader function, an MCP tool, or a producer.
- Fixing a bug in `server/guards.py`, `server/read_tools.py`, or `server/write_tools.py`.
- Any change to the reader-scope PII stripping path.

## The workflow

1. **RED** — write the test first, run it, confirm it fails.
   ```bash
   uv run pytest tests/test_write_tools.py::test_new_thing -q
   ```
2. **GREEN** — minimal implementation to pass.
3. **REFACTOR** — clean up while green.
4. **Verify the suite, not just the new test:**
   ```bash
   uv run pytest -q
   uv run ruff check .
   ```

There is no coverage-percentage gate enforced here the way the original's Jest config
had one (`branches: 80, functions: 80, ...`). The real gate is narrower and stricter in
a different way: every write tool must have a test proving the read-back check works,
and every reader-scope tool must have a test proving PII stripping works. A 95%-covered
codebase that never tests a read-back mismatch has not covered the thing that matters.

## Test types, this stack's shape

- **Unit** — pure functions in `loaders/` and `server/guards.py`. No I/O, no database,
  fast. Validators belong here and should be tested exhaustively since they're cheap.
- **Integration** — the tool + database, in `tests/test_write_tools.py` and the
  matching read-tool tests. **Always `TCP_TEST_DATABASE_URL`, never `DATABASE_URL`** —
  these tests create and drop databases.
- **No E2E tier.** There is no browser-driven UI. If `dashboard/app.py` needs a
  request-level test, use Starlette's test client directly — that's still an
  integration test, not an E2E one.

## The pattern every write-tool test must cover

```python
def test_upsert_write_readback_mismatch_is_error(test_db):
    result = upsert_tenancy(malformed_payload, scope="producer")
    assert "error" in result

def test_upsert_write_readback_success(test_db):
    result = upsert_tenancy(good_payload, scope="producer")
    assert result["count"] == 1
    assert "as_of" in result

def test_upsert_rejects_below_min_scope(test_db):
    result = upsert_tenancy(good_payload, scope="reader")
    assert "error" in result  # gate() denies before the write happens
```

## Mocking — narrower than the original's Redis/Supabase/OpenAI mocks

There's no vector search, no cache layer, no third-party SDK client to mock in the
core server code. The one thing worth stubbing is an external connector call inside a
producer (Re-Leased, QBO) when testing the producer's control flow rather than the
live integration — and even then, prefer testing against recorded fixtures over mocking
the client, since this repo has no ORM/SDK abstraction layer to mock against cleanly.

## Anti-patterns, same as ever

Tests coupled to internal state instead of the tool's returned `_result()` shape, tests
that depend on execution order, and — this stack's aggravated version of "don't hit
real infrastructure in a test" — a test that touches `DATABASE_URL` instead of
`TCP_TEST_DATABASE_URL`, which risks the live database rather than merely being flaky.

## Success criteria

- `uv run pytest -q` green.
- `uv run ruff check .` clean.
- Every new write tool has a read-back-mismatch test and a below-min-scope test.
- Every new reader-scope column addition has a stripping test.
