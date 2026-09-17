# Refactor Clean

Safely identify and remove dead code with test verification.

1. Run dead-code analysis:
   - `uv run ruff check --select F401,F841 .` -- unused imports (F401) and
     unused local variables (F841). This is the fast, always-available pass;
     run it first.
   - Optional, deeper pass: `uvx vulture .` (or `uv run --with vulture
     vulture .`) -- Python's rough equivalent of the JS ecosystem's
     knip/depcheck/ts-prune, finding unused functions, classes, and
     attributes that ruff's F401/F841 don't catch. There's no
     dependency-graph tool for Python as mature as those JS tools, so
     vulture's confidence scores need a human read, not a blind sweep --
     treat anything below its default 60% confidence as a hint, not a
     finding.

2. Categorize findings by severity:
   - SAFE: unused imports, unused local variables, unused private helpers
     in `tests/`
   - CAUTION: unused functions/classes in `tools/`, `loaders/`, `producers/`
     -- some of these are invoked only from `schedules/*.yaml` cron
     entries or FastMCP tool registration, not from Python call sites, so
     "vulture says unused" is not sufficient evidence on its own; grep
     `schedules/` and the MCP tool registry before proposing removal
   - DANGER: anything in `schema/` (migrations are historical record, never
     delete even if unreferenced), `dashboard/app.py` route handlers, and
     anything `tools/estate.py` or `tools/history_scan.py` import

3. Propose SAFE deletions only, unless the user explicitly asks to review
   CAUTION items too.

4. Before each deletion:
   - Run `uv run pytest -q`
   - Verify tests pass
   - Apply the change
   - Re-run `uv run pytest -q`
   - Roll back if tests fail

5. Show a summary of what was removed.

Never delete code without running tests first, and never delete anything
under `schema/` regardless of what any dead-code tool reports.
