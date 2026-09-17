# Test Coverage

Analyze test coverage and generate missing tests for terrace-control-plane.

**Note:** `pytest-cov` is not currently a declared dependency in this repo's
`pyproject.toml` (checked 2026-09-17). Run it ad hoc without touching the
project's dependency set:

```
uv run --with pytest-cov pytest --cov=. --cov-report=term-missing -q
```

If coverage tracking becomes a repeated habit rather than a one-off check,
add `pytest-cov` to the `dev` group in `pyproject.toml` instead of running
it ad hoc every time.

1. Run tests with coverage (command above). `testpaths = ["tests", "producers"]`
   per `pyproject.toml`, so this already covers both.

2. Read the terminal coverage report (`--cov-report=term-missing` prints
   uncovered line ranges directly; skip generating an HTML/XML report unless
   asked, since a spot-check on the same terminal output is cheaper than
   re-reading a coverage.xml or opening htmlcov/ file by file).

3. Identify files below 80% coverage.

4. For each under-covered file:
   - Read the uncovered line ranges reported above -- do not re-read the
     whole file to find them
   - Generate `pytest` unit tests for uncovered functions, following this
     repo's existing test conventions in `tests/`
   - For FastMCP tools, add a test that exercises the tool through
     `tests/` fixtures the same way existing tool tests do, not a fresh
     harness
   - For anything touching `psycopg3`/migrations, mock or use the existing
     test-database fixture -- never point a generated test at a live
     Postgres connection

5. Run `uv run pytest -q` to verify new tests pass (no need to re-run with
   `--cov` again unless checking the improved percentage).

6. Show before/after coverage metrics for only the files that changed.

7. Target 80%+ per file for files you touched; do not chase 80% overall in
   one pass if that means writing shallow tests across unrelated files.

Focus on:
- Happy path scenarios
- Error handling (this stack raises/returns explicit errors more than it
  raises generic exceptions -- match the existing error-handling style)
- Edge cases (None, empty string/list, boundary conditions)
- Idempotency where relevant (loaders and migrations in this repo are
  expected to be safely re-runnable)
