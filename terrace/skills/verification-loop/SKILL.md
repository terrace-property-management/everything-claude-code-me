---
name: verification-loop
description: Phase-gate verification policy for terrace-control-plane, the SKILL.md companion to the /verify command the parallel hooks/commands task is building. Describes the schema_drift --offline / estate.py / pytest / ruff check / Tier R scan sequence; the actual command file lives under the parallel task's ownership.
---

# Verification Loop — terrace-control-plane

This is a policy description, kept in sync with the `/verify` slash command the
parallel hooks/commands task owns (not built here — see the boundary note at the
bottom). The original skill's phases (npm build, tsc, eslint, Jest coverage, a grep for
`console.log`) don't apply to a stack with no build step and no client-side lint
surface; this describes the phase-gate sequence that actually matters here.

## When to run it

- Before creating a PR.
- After any change to `server/`, `loaders/`, or `schema/`.
- Before citing any Render or Neon figure — the estate check below exists specifically
  to catch a session that's been enumerating the wrong estate and reporting it healthy.

## Phase gates, in order — STOP and fix before continuing on any failure

### Phase 1: schema drift (offline, no DB needed)
```bash
python tools/schema_drift.py --offline
```
Catches migration numbering collisions after a `git fetch --all` before they reach a
database. This replaces the original's "build" phase — there is no compile step, but a
numbering collision is this stack's equivalent of a build break.

### Phase 2: estate confirmation
```bash
python tools/estate.py
```
Confirms which estate (`terrace-production` vs. the scratch estate) the connectors
actually reach. `CLAUDE.md` declares which one this is; this step proves it against
the database rather than trusting the declaration blindly. Skipping this is how a
session ends up enumerating a healthy scratch estate and reporting on a system it never
touched.

### Phase 3: test suite
```bash
uv run pytest -q
```
Fast — run it before and after, not just at the end. This replaces the original's
Jest-coverage phase; there's no fixed coverage percentage gate here, the suite passing
is the gate.

### Phase 4: lint
```bash
uv run ruff check .
```
Line length 100. Replaces the original's ESLint phase.

### Phase 5: Tier R secret scan
```bash
python tools/history_scan.py
```
Scans for Tier R shapes (SSN/ITIN, bank/routing, card numbers, government IDs, private
keys, credentialled connection strings) — this repo's real secret-scanning surface,
run before every push per `CLAUDE.md`'s version-control section. This replaces the
original's ad hoc `grep -rn "sk-"` — there's an actual maintained scanner here, use it
instead of re-deriving a weaker grep.

## Output format

```
VERIFICATION REPORT
====================
Schema drift:   [PASS/FAIL]
Estate:         [confirmed: terrace-production / MISMATCH]
Tests:          [PASS/FAIL] (X passed, Y failed)
Lint:           [PASS/FAIL] (X findings)
Secret scan:    [PASS/FAIL] (X hits) — exit 2 means "could not scan," not "clean"
Diff:           [X files changed]

Overall:        [READY/NOT READY] for PR
```

## Diff review — unchanged in spirit

```bash
git diff --stat
git diff [base-branch]...HEAD
```

Review for: a missing `TOOL_MIN_SCOPE` entry on a new tool, a write tool with no
read-back, a real tenant/applicant name introduced anywhere, an `mcp__*` grant added to
a subagent's `tools` list.

## Boundary note

This file describes the *policy*. The runnable `/verify` command wiring these five
phases together is being built by the parallel task that owns `hooks/`, `commands/`,
and `mcp-configs/` in this adaptation effort — don't duplicate that implementation
here; update this file to reference its actual path once it lands.
