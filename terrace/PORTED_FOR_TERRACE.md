# Terrace adaptation of everything-claude-code

`everything-claude-code-me` is an unmodified fork of a public repo
(`affaan-m/everything-claude-code`, MIT license) written for an
npm/pnpm/tsc/Prettier/Playwright/Supabase/React stack. Nothing in the original
tree is Terrace-specific, and most of its concrete tooling doesn't run as-is
against `terrace-control-plane`'s actual stack: Python 3.11+, `uv`, `ruff`,
`pytest`, psycopg3 + plain numbered SQL (no ORM), FastMCP tools (no REST),
server-rendered Starlette HTML (no React/npm/build step), on a Windows dev
machine.

This directory (`terrace/`) is a parallel, working, Python-native adaptation.
**Nothing under the original `agents/`, `skills/`, `rules/`, `hooks/`,
`examples/`, `mcp-configs/`, `commands/`, or `scripts/` was modified** — the
fork stays diffable against upstream. Everything here is new.

To use any of it in a real repo (e.g. `terrace-control-plane`), copy the
relevant files into that repo's `.claude/` tree (see per-section notes below)
and adjust paths as needed — this directory is the source, not a live
installation.

## Hooks (`terrace/hooks/`)

Ten Python 3 scripts (stdlib only, no pip dependencies), wired by
`terrace/hooks/hooks.json`. Each was tested by piping a synthetic stdin JSON
payload matching Claude Code's real hook contract and checking exit code,
stdout passthrough, and behavior on malformed input.

| Script | Ported from | Notes |
|---|---|---|
| `block_stray_docs.py` | inline PreToolUse rule | Same allowlist (README/CLAUDE/AGENTS/CONTRIBUTING exempt). Enforces the already-written "no stray planning docs" house rule mechanically. |
| `suggest_compact.py` | `suggest-compact.js` | Threshold raised to ~68 tool calls (≈2x the measured 33.8 mean turns/request); nudge cites the 86.4%-context-re-read finding. `COMPACT_THRESHOLD` env var overrides — 68 is a heuristic unit conversion (tool-calls, not turns), not a derived constant. |
| `pre_compact_note.py` | `pre-compact.js` | Lighter than the original: one timestamped line per compaction, no transcript parsing. |
| `session_start_note.py` | `session-start.js` | Package-manager detection dropped (only `uv` exists here). Reports current branch and worktree-vs-primary-checkout instead. |
| `pr_created_notice.py` | inline PostToolUse rule | Same PR-URL regex idea; now also prints the `gh pr merge --squash --delete-branch` step to match this repo's actual close-the-loop workflow. |
| `post_edit_format.py` | Prettier auto-format hook | Runs `ruff format` on edited `.py` files; degrades silently if `ruff` isn't on PATH. |
| `post_edit_lint.py` | tsc typecheck hook | Runs `ruff check --output-format=concise` (concise format chosen deliberately — the newer multi-line default breaks a per-line filter), filtered to the edited file. No mypy: confirmed absent from `terrace-control-plane`'s `pyproject.toml`. |
| `debug_leftover_warn.py` | console.log warn hook | Warns (never blocks) on stray `print(` in an edited `.py` file. |
| `stop_debug_sweep.py` | Stop console.log sweep | Same check, swept over `git diff --name-only HEAD` at Stop. |
| `git_push_reminder.py` | git-push reminder hook | Message rewritten to name the real workflow: commit → push → `gh pr create` (`phase-N: what changed`) → `gh pr merge --squash --delete-branch`. |

**Dropped, no replacement:**
- Dev-server-outside-tmux block + tmux reminder — nothing here runs an npm
  dev server or uses a tmux workflow.
- `session-end.js` (SessionEnd persist) — only scaffolded an empty markdown
  template; `pre_compact_note.py` already gives a comparable continuity
  marker.
- `evaluate-session.js` (continuous-learning trigger) — this account already
  runs a structured, actively-used memory system for pattern extraction; a
  second cruder mechanism would fragment it.

Hook state (compaction counters, logs) is written under `.claude/state/` in
the consuming repo — gitignored, per-repo, never committed.

## Statusline (`terrace/statusline.py`)

Full Python rewrite of `examples/statusline.json` (bash + `jq`). `jq` isn't
guaranteed on this Windows machine and bash-vs-PowerShell portability is a
problem Claude Code statuslines don't need — a `python "<path>"` command
sidesteps both. Same visual design (cwd, git branch + dirty marker,
context-remaining %, model, time, live todo count), same ANSI palette.
Context-remaining % is kept front and center given the context-economics
rule in `terrace-control-plane`'s `CLAUDE.md`. Wrapped in a top-level
try/except so a crash degrades to an error string, never a blank statusline.
`terrace/statusline.settings-snippet.json` has the exact block to paste into
a real `settings.json`.

## MCP config (`terrace/mcp-servers.json`)

Kept: `github`, `context7` (already installed at Terrace), `filesystem`,
`sequential-thinking` (optional, currently unused).

Dropped (each with a `_dropped` reason in the file): `supabase`, `vercel`,
`railway`, all four `cloudflare-*` entries, `clickhouse`, `magic` — none are
part of the Terrace stack. `memory` — Terrace already has its own memory
system; a generic MCP memory server would duplicate/conflict. `firecrawl` —
no web-scraping workflow exists in `terrace-control-plane` today; **this one
was a judgment call, not a named instruction — reconsider if that's wrong.**

Kept verbatim: the original's own guidance to stay under 10 active MCPs per
project — directly relevant, since this Claude Code account runs dozens of
MCP tools across many connectors today (see the adoption report's Track S
item on auditing active MCP count).

## Commands (`terrace/commands/`)

- **`verify.md`** — chains the exact orientation sequence
  `terrace-control-plane`'s own `CLAUDE.md` already documents, stop-on-fail:
  `python tools/schema_drift.py --offline` → `python tools/estate.py` →
  `uv run pytest -q` → `uv run ruff check .` → `python tools/history_scan.py`
  (pre-push/pre-PR). Cross-checked against those tools' real `--help` output.
- **`build-fix.md`** — fixes `pytest`/`ruff` failures with minimal diffs;
  explicitly forbids touching `schema/` or `tools/estate.py` gate logic to
  force a pass.
- **`test-coverage.md`** — `uv run --with pytest-cov pytest --cov=. --cov-report=term-missing -q`.
  `pytest-cov` is **not** currently a declared dependency in
  `terrace-control-plane`'s `pyproject.toml` (confirmed by grep) — the
  command installs it ad hoc via `--with` rather than assuming it's present.
- **`refactor-clean.md`** — `uv run ruff check --select F401,F841 .` as the
  primary pass (confirmed currently green on `terrace-control-plane`), `vulture`
  noted as an optional deeper pass. Python has no tool as mature as
  knip/depcheck/ts-prune for dead-code detection — this doc says so plainly
  rather than overclaiming parity.

## Agents (`terrace/agents/`)

All eight adapted agents carry an enumerated `tools:` list with zero
`mcp__*` entries, matching `terrace-control-plane`'s own
`docs/subagents.md` house rule (verified against `tests/test_agent_definitions.py`).
Model tiering by role (Haiku/Sonnet/Opus) is applied per `terrace/agents/MODEL_TIERING.md`
— the original fork had all nine agents hardcoded to `opus`, which its own
`rules/performance.md` argues against.

| Agent | Verdict |
|---|---|
| `architect.md` | Adapted — vertical-slice design (pure module → schema → MCP tool → producer → consumer), routes schema work to `database-expert`, refuses ORM/REST/React defaults. |
| `planner.md` | Adapted — plans in the 5-layer build order; flags missing-read-back as a risk. |
| `code-reviewer.md` | Adapted — `ruff`/type-hints instead of ESLint/tsc; folds in the `TOOL_MIN_SCOPE`/`PII_TOOLS`/`READER_STRIPPED_COLUMNS`/read-back checklist. |
| `security-reviewer.md` | Adapted — rewritten around SQL injection via raw psycopg3, Tier R secrets, PII scope, read-only-external-systems; explicitly lists what NOT to flag (CSRF/XSS/CORS/rate-limiting — no browser surface exists). |
| `tdd-guide.md` | Adapted — `pytest`/`uv run pytest --cov`; centers the validate→write→read-back invariant instead of a coverage percentage. |
| `build-error-resolver.md` | Adapted — `pytest`/`ruff` failures instead of `tsc`; same minimal-diff discipline. |
| `refactor-cleaner.md` | Adapted — states plainly there's no Python equivalent of knip/ts-prune; `ruff --select F401,F841` primary, `vulture` optional. |
| `doc-updater.md` | Adapted — real doc surface is `docs/decisions.md`, `docs/lessons.md`, `docs/subagents.md`, and `CLAUDE.md` itself as a versioned artifact. |
| `e2e-runner.md` | **Dropped** — no browser-driven UI exists in this stack (server-rendered, no client JS). |

## Skills (`terrace/skills/`)

| Skill | Verdict |
|---|---|
| `coding-standards` | Adapted — Python/psycopg3 conventions; immutability narrowed to "never mutate a snapshot table row." |
| `backend-patterns` | Adapted (rewritten) — FastMCP tools, scope ordering, the fixed write-tool pattern, `_result()` shape, bounded/reported-cap reads. |
| `tdd-workflow` | Adapted — pytest-based, kept consistent with `agents/tdd-guide.md`. |
| `security-review` | Adapted — same reasoning as `agents/security-reviewer.md`, kept in sync with it. |
| `strategic-compact` | Adapted (policy only) — the working hook is `terrace/hooks/suggest_compact.py`; this SKILL.md describes the policy. |
| `eval-harness` | Adapted — code-based grader grounded in `pytest`/`ruff` exit codes; cross-references `baseline-setup-repo`'s existing broken/correct fixture-pair pattern instead of reinventing it. |
| `verification-loop` | Adapted (policy only) — the runnable command is `terrace/commands/verify.md`. |
| `frontend-patterns` | **Dropped** — no client-side framework in this stack. |
| `continuous-learning` | **Dropped** — duplicates this account's existing memory system. |
| `clickhouse-io` | **Dropped** — no ClickHouse anywhere in the stack (Postgres/Neon throughout). |
| `project-guidelines-example` | **Dropped** — a filled-in template for the original author's own SaaS product; `fullstack-developer.md` already is this stack's real project-guidelines doc. |

## Rules (`rules/` → `terrace/rules-note.md`)

No `terrace/rules/` directory was created — a bare `~/.claude/rules/` folder
has no confirmed Claude Code auto-load mechanism, so the content was folded
into the agents/skills above (the mechanisms this stack actually loads) or
superseded by files that already exist in `terrace-control-plane`
(`docs/subagents.md`, `CLAUDE.md`'s context-economics section). See
`terrace/rules-note.md` for the full per-file trace.

**Explicitly not adopted:** `rules/git-workflow.md` states attribution is
disabled globally via `~/.claude/settings.json`. This conflicts with this
account's standing Claude attribution requirement and its branch → PR →
review-diff → merge double-review discipline. Do not import that setting
anywhere.

## Skipped entirely, no verdict needed

`.claude-plugin/`, `CONTRIBUTING.md`, `WORLDFLOWAI.md`, `contexts/*.md`,
`plugins/README.md`, `scripts/lib/package-manager.js`,
`scripts/setup-package-manager.js`, `tests/*` — packaging/meta files, a
different company's cheat sheet, or Node-ecosystem tooling (package-manager
auto-detection) with no equivalent need in a `uv`-only stack.

## Known side effects from building this

- `ruff` was installed globally on the machine that built this
  (`uv tool install ruff`), needed to test the happy path of
  `post_edit_format.py`/`post_edit_lint.py` since it wasn't already on PATH.
  Harmless, but not itself a deliverable — remove it if you don't want a
  standalone `ruff` outside project-scoped `uv` environments.

## Suggested next step

None of this is wired into `terrace-control-plane` yet. Copying it in is a
separate, deliberate decision — start with `terrace/hooks/block_stray_docs.py`
and `terrace/statusline.py` (lowest risk, immediate value per the earlier
adoption report), then the rest as they prove out.
