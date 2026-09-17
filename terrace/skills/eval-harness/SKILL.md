---
name: eval-harness
description: Eval-driven development framework for terrace-control-plane, adapted to ground the code-based grader in pytest/ruff exit codes. Cross-references baseline-setup-repo's existing broken/correct fixture-pair pattern for the model-based grader case instead of reinventing it.
---

# Eval Harness — terrace-control-plane

Capability Evals and Regression Evals are a genuinely good framework and transfer
without much change; only the grader mechanics need adapting away from npm/Jest.

## Eval types (unchanged)

**Capability Eval** — can this code do something new:
```markdown
[CAPABILITY EVAL: lease-expiry-window]
Task: get_lease_expiry(entity, days=30) returns only rows within the window
Success Criteria:
  - [ ] Rejects a call below reader scope's PII-stripped shape where applicable
  - [ ] Every row carries as_of and source
  - [ ] row_cap_hit reported when the true result set exceeds ROW_CAP
Expected Output: bounded, sourced result set
```

**Regression Eval** — did this change break something that worked before:
```markdown
[REGRESSION EVAL: reader-pii-stripping]
Baseline: commit SHA before the change
Tests:
  - test_reader_pii_projection.py::test_strips_contact_email: PASS/FAIL
  - test_guards.py::test_min_scope_enforced: PASS/FAIL
Result: X/Y passed (previously Y/Y)
```

## Grader types, this stack's tools

### 1. Code-based grader — ground it in pytest/ruff exit codes

```bash
# Capability check: does the new tool pass its own test?
uv run pytest tests/test_read_tools.py::test_lease_expiry_window -q && echo PASS || echo FAIL

# Regression check: does the full suite still pass?
uv run pytest -q && echo PASS || echo FAIL

# Lint gate as a grader, not just a style check
uv run ruff check . && echo PASS || echo FAIL
```

There is no `npm test` / `npm run build` here — every code-based grader in this repo
should bottom out in `uv run pytest` and `uv run ruff check` exit codes, nothing else.

### 2. Model-based grader — don't reinvent this, it already exists

The original skill's "use Claude to evaluate open-ended outputs" idea is real, but this
account already has a close relative of it, and it's more rigorous than a bare grading
prompt: **`baseline-setup-repo`'s specialist skills pair every finding-detector with a
broken/correct fixture pair specifically so a rule that misfires on correct code gets
caught.** A model-based grader for this repo's own eval harness should follow that
pattern — for any detector-shaped eval (does this reviewer flag the SQL-injection
pattern, does it *not* flag the correctly parameterized version), write both fixtures
and check both directions, rather than writing a single "grade this on a 1-5 scale"
prompt and calling it done. Cross-reference `baseline-setup-repo`'s pattern instead of
drafting a new grading rubric from scratch.

### 3. Human grader — unchanged

Flag for Spencer when the eval concerns a genuine judgment call (a scope floor decision,
a new hard rule) rather than something code or a fixture pair can settle.

## Eval workflow

1. **Define before building** — capability + regression evals, before writing the tool.
2. **Implement.**
3. **Evaluate** — run the pytest/ruff-grounded checks; for a detector-shaped change,
   run both fixtures from the broken/correct pair.
4. **Report** — same format as before, PASS/FAIL counts, pass@k if attempted more than
   once.

## Storage

```
.claude/evals/<feature-name>.md      # definition
.claude/evals/<feature-name>.log     # run history
```

No change needed here from the original.

## Best practices, this stack's version

1. Define evals before coding — same as always.
2. Ground every code-based grader in `uv run pytest` / `uv run ruff check`, never
   invented shell greps standing in for a real test.
3. For any eval judging whether a review/detector correctly flags a pattern, write the
   broken/correct fixture pair rather than a single-sample grading prompt — this is
   what `baseline-setup-repo` already does; reuse the idea.
4. Human review for scope/PII judgment calls — never fully automate those.
