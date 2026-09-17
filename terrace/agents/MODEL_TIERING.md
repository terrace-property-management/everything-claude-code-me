# Model tiering for the adapted agents

All eight agents under `terrace/agents/` were carried over from the original
fork hardcoded to `model: opus` — that repo's own convention (`rules/performance.md`)
actually argues against this: Haiku for high-frequency worker agents, Sonnet
for main dev work, Opus for architecture/research. The port initially missed
applying that rule to itself. Fixed here:

| Agent | Model | Why |
|---|---|---|
| `architect.md` | `opus` | System-design reasoning, routes real schema work elsewhere — worth the cost. |
| `planner.md` | `opus` | Implementation planning across the 5-layer vertical slice is architecture-adjacent reasoning, not mechanical work. |
| `security-reviewer.md` | `opus` | Findings are CRITICAL-severity by nature (SQL injection, Tier R secrets, PII scope) — false negatives here are the expensive failure mode. |
| `code-reviewer.md` | `sonnet` | Runs on every code change ("MUST BE USED"), needs real correctness reasoning, but doesn't need architecture-tier depth. |
| `tdd-guide.md` | `sonnet` | Same reasoning as code-reviewer — frequent, but judgment-heavy (the validate→write→read-back invariant isn't a checklist). |
| `build-error-resolver.md` | `haiku` | High-frequency, narrow, mechanical: read a `pytest`/`ruff` failure, make the minimal fix. Explicitly forbidden from architectural changes, so it doesn't need architecture-tier reasoning. |
| `refactor-cleaner.md` | `haiku` | High-frequency, mechanical: run `ruff --select F401,F841`, remove what it flags. |
| `doc-updater.md` | `haiku` | High-frequency, mechanical: keep `docs/decisions.md`/`docs/lessons.md` in sync with a change already made. |

If a `model:` field is unfamiliar to whichever Claude Code version reads
these — most agent frontmatter schemas support it, but confirm before relying
on the tiering actually taking effect once these are copied into a real
`.claude/agents/` directory.
