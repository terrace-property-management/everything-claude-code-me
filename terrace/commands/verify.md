# Verification Command

Run comprehensive verification on the current terrace-control-plane checkout.

## Instructions

Execute verification in this exact order. Each step must pass before moving
to the next -- **stop on the first failure** and report it rather than
continuing to run later steps against a checkout already known to be broken.

1. **Schema drift (offline)**
   - `python tools/schema_drift.py --offline`
   - Checks migration numbering and cross-branch collisions without hitting
     the database. If it fails, report the collision/gap and STOP.

2. **Estate gate**
   - `python tools/estate.py`
   - Confirms this checkout and its connectors are pointed at the estate
     they claim to be (Estate A vs. Estate B -- see CLAUDE.md). If it fails,
     report which estate check failed and STOP: nothing downstream should
     run against the wrong estate.

3. **Test suite**
   - `uv run pytest -q`
   - Report pass/fail count. If it fails, report the failing tests and STOP.

4. **Lint**
   - `uv run ruff check .`
   - Report all findings (file:line, rule code).

5. **Secret scan (pre-push only)**
   - Before the FIRST push after any history rewrite (or whenever `$ARGUMENTS`
     includes `pre-push` or `pre-pr`): `python tools/history_scan.py`
   - Exit 0 = clean, 1 = findings (report them, STOP -- do not push), 2 =
     INCOMPLETE (could not scan; report and treat as a failure, not a pass).

## Output

Produce a concise verification report:

```
VERIFICATION: [PASS/FAIL]

Schema drift:  [OK/FAIL - detail]
Estate gate:   [OK/FAIL - detail]
Tests:         [X/Y passed]
Lint (ruff):   [OK/X issues]
Secret scan:   [OK/N/A/X findings]

Ready for PR: [YES/NO]
```

If any step failed, list the concrete errors with fix suggestions -- not just
the pass/fail table.

## Arguments

`$ARGUMENTS` can be:
- `quick` - schema drift + estate gate only
- `full` - all checks except the secret scan (default)
- `pre-commit` - schema drift + tests + lint
- `pre-push` / `pre-pr` - full checks plus the secret scan (mandatory before
  the first push after any history rewrite; cheap enough to run every time)
