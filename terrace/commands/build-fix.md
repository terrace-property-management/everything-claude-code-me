# Build and Fix

Incrementally fix `pytest` and `ruff` failures with minimal diffs. There is
no build/compile step in this stack (no tsc, no bundler) -- "the build" here
means "the test suite and the linter both pass."

1. Run: `uv run pytest -q` and `uv run ruff check .`

2. Parse the combined output:
   - Group failures by file
   - Sort by severity (a failing test that asserts real behavior outranks a
     lint style nit)

3. For each failure:
   - Show error context (the failing assertion / traceback, or the ruff
     rule + surrounding lines)
   - Explain the issue
   - Propose the smallest fix that makes it pass -- don't refactor
     architecture, don't rename things, don't "improve" adjacent code while
     you're in there
   - Apply the fix
   - Re-run the specific test file or `ruff check <file>` to verify just
     that failure is resolved before moving to the next

4. Stop if:
   - A fix introduces a new failure elsewhere
   - The same failure persists after 3 attempts
   - The user requests a pause

5. Show a summary:
   - Failures fixed
   - Failures remaining
   - New failures introduced (should be zero)

6. Finish with `uv run pytest -q && uv run ruff check .` run once more,
   clean, before calling it done.

Fix one failure at a time for safety. Never touch `schema/` migrations or
`tools/estate.py`'s gate logic to make a test pass -- if a fix requires
changing either of those, stop and flag it instead of applying it.
