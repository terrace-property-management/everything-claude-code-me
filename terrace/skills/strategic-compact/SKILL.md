---
name: strategic-compact
description: Policy for nudging manual context compaction in terrace-control-plane sessions, informed by this stack's own context-economics rules. The working Python hook is being built by the parallel hooks/infra task under terrace/hooks/ — this file describes the policy only, not the implementation.
---

# Strategic Compact — terrace-control-plane

This is a policy description, not an implementation. The original skill shipped a
`suggest-compact.sh` bash script wired to a PreToolUse hook; the working equivalent for
this stack is a Python hook, owned by the parallel hooks/statusline/MCP-config task and
living under `terrace/hooks/` once it lands. This file exists so the policy this repo
actually wants is written down and doesn't get re-derived generically from the
original's arbitrary 50-call threshold.

## Why strategic compaction, in this repo's own terms

`CLAUDE.md`'s context-economics section is not a generic FinOps aside — it's measured:
86.4% of a recent quarter's spend was context being cached and re-read, not answers
being written (`docs/token_audit_2026-09-14.md`). The rules that follow from that
measurement are specific and already written down; this skill's job is to fold the
compaction trigger into them rather than invent a separate arbitrary threshold.

## The actual triggers, not an arbitrary tool-call count

- **Turns-per-request above ~2x the 33.8 mean, or above ~10% byte-identical repeat
  calls** — this is this stack's own definition of "looping," from `CLAUDE.md`. That's
  the signal to write state and continue fresh, not a fixed count of Edit/Write calls.
- **Past ~250k tokens of context** — `CLAUDE.md`'s own carve-out for "write state and
  continue in a fresh session," independent of how the work is going.
- **After exploration, before execution** — still a good boundary in this repo
  specifically because multi-file exploration here is supposed to go to a subagent that
  returns a conclusion (per the Delegation section of `CLAUDE.md`), not accumulate in
  the main session's context in the first place. If a session is accumulating
  exploration context past that point, that's itself a sign the work should have been
  delegated, and the nudge should say so.
- **One session per workstream. When the deliverable lands, stop.** — a nudge to
  compact mid-deliverable is generally wrong here; the right move at that point is
  usually "the session should have already ended," not "compact and continue."

## What the hook should say, not just when

The original's hook fired a generic "consider compacting" message. This stack's version
should say *why*, citing the specific rule that triggered it (turns-per-request ratio,
byte-identical repeats, the 250k mark) — a bare threshold notice doesn't teach the
session anything about which of its own behaviors caused it, and `docs/lessons.md`
#92-#101 exist specifically to make this reasoning durable rather than re-discovered
each time.

## The one carve-out

A cost/context rule never sits in front of a safety gate. The STOP-at-login/MFA/CAPTCHA
rule outranks this section; a compaction nudge should never fire in a way that
interrupts a safety check mid-flight.

## Where this lives

The policy is here. The Python `PreToolUse`/turn-count implementation, wired into
`settings.json`, is the parallel hooks task's deliverable under `terrace/hooks/` — this
file should be updated to point at the specific script path once that lands, rather
than duplicating its logic here.
