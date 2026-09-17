# What happened to `rules/`

The original `rules/` directory (`agents.md`, `coding-style.md`, `git-workflow.md`,
`hooks.md`, `patterns.md`, `performance.md`, `security.md`, `testing.md`) is a
free-floating set of markdown files with no confirmed loading mechanism in Claude Code
— there is no evidence a bare `~/.claude/rules/` folder is something Claude Code reads
automatically the way `.claude/agents/`, `.claude/skills/`, and a project's own
`CLAUDE.md` are. Rather than port it as a sixth parallel directory of unclear standing,
its content has been folded into the two mechanisms that *are* confirmed auto-loaded
for terrace-control-plane: the adapted `terrace/agents/` and `terrace/skills/` files
above, and — for anything that was really a build/process rule rather than a coding
pattern — `fullstack-developer.md` and `CLAUDE.md` themselves, which this repo already
treats as living documents.

## `git-workflow.md` — one piece explicitly NOT adopted, and why

`rules/git-workflow.md` states: *"Note: Attribution disabled globally via
`~/.claude/settings.json`."* **This should not be adopted anywhere in this account's
Terrace setup.** Two standing facts contradict it directly:

1. This session's own attribution instructions require Claude commit/PR co-authorship
   lines (`Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` on commits,
   the Claude Code byline on PR descriptions) — not disabled, required.
2. `terrace-control-plane`'s own worktree/PR workflow (`CLAUDE.md`, "Worktree
   workflow" section, and this account's standing PR-double-review discipline) is
   branch → PR → review the diff → merge, never direct-to-main, with every PR carrying
   real attribution for who (or what) authored it. Silently disabling attribution
   removes information a reviewer relies on when auditing a PR, which cuts directly
   against that discipline.

The rest of `git-workflow.md` (PR summary from full commit history, not just the latest
commit; `git diff [base-branch]...HEAD` before drafting; a test plan with TODOs) is
unobjectionable and is already how this account's PR workflow operates independent of
this file — nothing new needed adopting from it.

## Where each other file's real content landed

| Original file | What was worth keeping | Where it landed |
|---|---|---|
| `agents.md` | "Use code-reviewer proactively after writing code," "use tdd-guide for new features/bug fixes," parallel Task execution for independent work | Preserved as the proactive-use framing in `terrace/agents/code-reviewer.md` and `terrace/agents/tdd-guide.md`'s `description:` fields (`MUST BE USED` / `PROACTIVELY`). The agent roster table itself is superseded by `docs/subagents.md`'s "What we have" table, which is this repo's actual authoritative agent registry. |
| `coding-style.md` | Many-small-files, no-hardcoded-secrets, input validation, comments-carry-why | `terrace/skills/coding-standards/SKILL.md` — rewritten against Python/psycopg3 (no Zod, no spread-operator immutability ceremony; the real immutability rule here is "never mutate a snapshot table row," which is narrower and stack-specific). |
| `testing.md` | TDD mandatory workflow, "fix the implementation not the test" | `terrace/agents/tdd-guide.md` and `terrace/skills/tdd-workflow/SKILL.md`. The 80%-coverage numeric gate was dropped rather than ported — this stack's real test-worthy invariant is the write-tool validate→write→read-back pattern and reader-scope PII stripping, which a coverage percentage doesn't measure. |
| `patterns.md` | API response shape, repository-pattern abstraction | Superseded, not ported: this stack's real response contract is the `_result()` shape (rows/count/source/scope/as-of) in `terrace/skills/backend-patterns/SKILL.md`, which is stricter and already enforced by `CLAUDE.md`'s "every figure carries a source and an as-of" rule. The generic repository-pattern class doesn't apply — there's no ORM to abstract. |
| `performance.md` | Model-selection guidance (Haiku for cheap fan-out, Opus for architecture), context-window awareness | Not re-ported as a separate file: `CLAUDE.md`'s own "Context economics" section already covers this ground with real measurement (86.4% of spend was context re-read) rather than generic advice, and `docs/subagents.md`'s "model" section already covers per-agent model selection guidance. Citing the existing sections beats duplicating them. |
| `security.md` | Pre-commit security checklist, "STOP and use security-reviewer on a finding" | `terrace/agents/security-reviewer.md` and `terrace/skills/security-review/SKILL.md` — completely rewritten around this stack's actual surface (SQL injection via raw psycopg3, Tier R secret shapes, PII scope, read-only-external-systems) rather than relabeled OWASP web items. |
| `hooks.md` | Hook type reference (PreToolUse/PostToolUse/Stop), TodoWrite best practices | Not ported — this describes the original repo's own hook wiring (Prettier, tsc-on-save, a console.log Stop-hook audit), none of which exists in this stack. The parallel hooks/infra task owns whatever this stack's actual hook wiring looks like; the one piece with a real forward reference is `strategic-compact`'s policy (`terrace/skills/strategic-compact/SKILL.md`), which explicitly hands off to that task's `terrace/hooks/` implementation rather than re-describing generic hook mechanics here. |

## Bottom line for a reviewer

Nothing in `rules/` needed a parallel `terrace/rules/` directory — everything worth
keeping already has a more specific, more authoritative home in this stack (an agent
file, a skill file, or `CLAUDE.md`/`fullstack-developer.md` themselves), and the one
piece of explicit advice in `rules/` (disable attribution) is one this account
specifically does not want followed.
