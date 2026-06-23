# Proposal: make repo-wiki *prompt* for capture, instead of relying on the human to remember

**For:** the `repo-wiki` skill (upstream).
**Status:** ✅ **Implemented** (commits `b6d2369` groundwork + `f013f3a` the counter) — the
knowledge-debt counter described below shipped, with thresholds **≥ 5 commits / ≥ 18 turns**.
See SKILL.md → "Proactive capture — the knowledge-debt counter" for the shipped behavior and
the existing-install upgrade path. This document is retained as the originating RFC.
**Author context:** written after a ~7-hour session that produced a large amount of durable
knowledge (a new subsystem, several decisions, a non-obvious data gotcha) — and the wiki was
only ever updated when the *user explicitly asked*. The standing "propose a page" instruction
fired zero times on its own.

## Problem

The skill is excellent at detecting **code drift** — `kb status` deterministically intersects
each page's `covers` globs with the git diff since its `verified_against` sha. That half is
mechanical and reliable.

The other half — capturing **chat-borne knowledge** (decisions, gotchas, "why", new
subsystems) — depends on either:
1. the **human remembering** to ask, or
2. **edge-of-session nudges** the human never sees and the agent routinely blows past:
   `SessionStart` (stale delta), `SessionEnd` (catchup), `PreCompact` (extract-before-compaction).

Plus a standing instruction injected at `SessionStart` ("on a cache miss, propose a page").

**Observed failure mode:** over a long session, the standing instruction is forgotten — the
model's attention to a one-shot system prompt decays as the context fills with task work. The
edge nudges fire at moments outside the user's view. Net result: the user has to be the wiki's
conscience, which is exactly the complaint.

## Root cause

> A *standing instruction* to the agent is too weak over a long session. Capture has to be
> driven by a **recurring, mechanical signal**, not by the agent's (or the user's) memory.

The skill already proves this works for code drift (git-driven, deterministic, re-checked every
session). The same discipline isn't applied to the *chat → knowledge* stream **during** a
session.

## Proposed changes (ranked)

### 1. A "knowledge-debt" counter that nudges *mid-session* (primary)

Track, in `repo-wiki/.ingest/state.json`, how much has happened since the last `repo-wiki/`
write:

```json
"knowledge_debt": { "commits": 0, "turns": 0, "since_sha": "<sha>", "since_ts": "<iso>" }
```

- **`post-commit` hook** (`kb.py post-commit`): `commits += 1`. If the commit's diff touches any
  `repo-wiki/**` file, **reset the counter to zero**.
- **`UserPromptSubmit` hook**: `turns += 1`. Reset if any `repo-wiki/**` file's mtime is newer
  than `since_ts` (the hook can't see commits, so use file mtimes).
- When `commits >= C` (e.g. 5) **or** `turns >= T` (e.g. 15–20), inject a **visible, escalating,
  agent-directed** line:

  > ⚠ repo-wiki: 8 commits / 22 turns since the last wiki update. Review what durable knowledge
  > this work produced (decisions, gotchas, new subsystems) and **proactively OFFER** to capture
  > it — one line, propose-not-apply. (Resets when you touch `repo-wiki/`.)

This is deterministic to *fire* (no LLM judgment needed), recurs *during* the session in front
of the agent, and resets itself when the agent actually writes — so it can't nag forever and
it targets the agent's behavior. Escalate the wording as the counter climbs so it's not
ignorable.

### 2. Turn the `post-commit` hook from drift-only into capture-also

It already runs on every commit and the agent sees its output — the natural moment, because a
commit usually means a decision was just made. Add:
- *"You committed code under `X/` that has **no covering wiki page** — document the subsystem?"*
  (detect: changed paths not matched by any page's `covers`).
- *"N commits since the last wiki write."* (from the counter above).

### 3. Reframe the standing instruction as a behavior (and pair it with #1)

Change the `SessionStart` injection from the cache-miss phrasing to an explicit behavioral rule:

> After any turn that **settles a decision, discovers a non-obvious fact, or changes how the
> system works**, proactively offer a one-line wiki capture — don't wait to be asked.

On its own this is weak (see Problem). Its job is to be the *phrasing* the agent reaches for
when signal #1 fires. Keep it, but don't rely on it alone.

## Design principle

The skill's own SKILL.md states its "honest limit": it can't make a human author knowledge,
only *surface the opportunity*. Today that surfacing happens **once, at the edges**. Make it
**recurring and escalating off a cheap git/turn counter**, and "remember to update the wiki"
stops being the human's job.

## Preserve

- **Propose-not-apply** stays intact — the nudge asks the agent to *offer*, never to auto-write
  `canonical` pages.
- **No new gates** — like `kb status`, the nudge is a soft signal, never a commit blocker
  (hard gates breed `--no-verify` habits).
- **Self-resetting** — touching `repo-wiki/` zeroes the counter, so a diligent session is never
  nagged.

## Rough implementation surface

- `kb.py`: add counter read/update helpers; extend `cmd_post_commit` (increment + uncovered-path
  detection + threshold print); add a `cmd_turn_tick` (or fold into the `UserPromptSubmit`
  comments hook) for the turn counter + mtime-based reset; tweak the `SessionStart` injection
  string in `cmd_session_start`.
- `.claude/settings.json`: the `UserPromptSubmit` hook already exists (comments) — append the
  turn-tick call, or have the comments command also emit the debt nudge.
- State lives in the already-present `repo-wiki/.ingest/state.json`.

## As-built notes (deviations from this RFC)

- **Turn tick folded into the existing `UserPromptSubmit` comments hook** (not a new hook) — the
  SessionStart self-heal rewrites that hook in place when its desired command changes, so
  existing installs upgrade with no re-init.
- **The mtime-based reset excludes `.ingest/`** so the `search.db` FTS cache and `state.json`
  itself can't trigger a false reset; it counts only tracked pages (`iter_pages` semantics).
- **Uncovered-path hint keys on the first two path segments** (e.g. `src/payments`) so it names
  the subsystem rather than the language root.
- **Thresholds:** `C = 5` commits, `T = 18` turns; nudge escalates `•` → `⚠` → `⚠⚠`.
