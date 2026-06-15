# Activation: making the mechanics actually run

The mechanics (staleness check, chat catch-up, synthesis) are worthless if nothing
fires them. The key reframe: **this is an install problem, not a per-use-discipline
problem.** You don't ensure usage by hoping the agent remembers; you install reliable
triggers once, prefer committed/shared config, and make drift visible.

## Triggers — wired and running

| Trigger | Status | Fires | Drives |
|---|---|---|---|
| **SessionStart hook** (`.claude/settings.json`, committed) | **WIRED** | every session begins | heartbeat: inject wiki + `covers`-scoped pages, announce new-stale delta, self-heal git hook, spawn detached reconcile |
| **post-commit git hook** (`.git/hooks/post-commit`, self-healed) | **WIRED** | every git commit | diff-scoped nudge: lists pages whose `covers` paths overlap THIS commit's changes; exits 0 always |
| **PreCompact hook** (`.claude/settings.json`, committed) | **WIRED** | before context compaction | prints an extract-before-compaction directive so the agent mines context from the about-to-be-lost window |
| **SessionEnd hook** (`.claude/settings.json`, committed) | **WIRED** | session ends | catch-up nudge: reminds agent to run `kb catchup` before the session is gone |
| `kb status --new` / `kb session-start` (delta cursor) | **WIRED** | session-start + explicit call | surfaces staleness exactly once per fresh→stale transition (delta/surfaced cursor) |
| **CI check on PR** | recommended | every PR | server-side backstop: comment / soft-fail on stale pages — ungameable |
| SKILL.md instructions / `kb` CLI | discretionary | during work / on demand | inline capture, on-demand control |

## How usage is ensured

1. **Bootstrap installs the triggers.** `kb.py init` (new/empty repo one-shot) or
   `kb.py plumbing` (standalone, order-independent) writes four hooks into
   `.claude/settings.json` (SessionStart, UserPromptSubmit, PreCompact, SessionEnd),
   installs `.git/hooks/post-commit`, and gitignores the local ingest watermark.
   Plumbing is fully independent of wiki structure — run it before or after `kb scaffold`.
   One-time setup, not recurring willpower.
2. **Prefer committed/shared config.** `.claude/settings.json` hooks (SessionStart,
   UserPromptSubmit, PreCompact, SessionEnd) are committed and cloned automatically.
   Everyone on the team gets them with no extra step.
3. **SessionStart is load-bearing and mechanical.** It fires every session regardless
   of agent cooperation. It announces newly-stale pages, self-heals the git hook, and
   reconciles the chat watermark — catching whatever the best-effort hooks missed.
   Correctness never depends on a live event firing.
4. **Visible drift is the flywheel.** Because SessionStart both injects the wiki (used
   every session) and reports drift, rot is felt immediately and constantly — the same
   pressure that gets failing CI fixed.
5. **CI backstops** the bypassed-hook and no-agent paths (pure-git commits with no
   session) server-side, where it can't be skipped.

## The delta / surfaced cursor

`kb status --new` (and `kb session-start`) announce staleness **once per
fresh→stale transition**, not as a standing count. The mechanism:

- A file `.ingest/surfaced.json` tracks `{page|verified_against: true}` keys for every
  page that has been surfaced to the agent.
- `newly_stale()` filters the stale list to entries whose key is absent from
  `surfaced.json`. These are announced, then immediately written into `surfaced.json`.
- On the **next** call, the same pages are already in `surfaced.json` → silent.
- The cursor is cleared for a page when `kb verify <page>` runs (bumps
  `verified_against` to HEAD, writes a new key), so the old key is no longer present
  and the page can be surfaced again if it drifts once more.

This means: stale pages are announced **once** when they become stale. Re-running
`kb status --new` in the same session is silent. After a `kb verify` clears the cursor,
a subsequent drift will surface the page again exactly once.

## The SessionStart hook — must never block

Hook output is injected synchronously, so it **gates session start**. A full freshness
scan (a `git diff` per page) over a large wiki, or enumerating long chat sessions, would
make the user wait. So the startup path is split:

- **`kb.py session-start` (blocking)** does *no* git scan. It counts pages (a cheap
  filesystem walk), prints the cached drift summary ("as of <ts>: 3 stale"), and **spawns
  a detached `kb.py reconcile`** to refresh the cache for next time. It returns in
  milliseconds.
- **`kb.py reconcile` (detached / background)** does the heavy scan and writes
  `repo-wiki/.ingest/status.json`. The next session-start reads it instantly.

So freshness is always *one session stale* in the worst case — a deliberate trade to keep
startup instant. Run `kb.py status` anytime for a live scan. The hook also **shim-lints**
(nudges a CLAUDE.md/AGENTS.md migration if knowledge re-accreted). See
`assets/templates/sessionstart-hook.json` for the snippet `init` installs.

## The self-heal bootstrap

`.git/hooks/post-commit` is **never inherited by a `git clone`** — git intentionally
excludes local hooks from version control. The committed `.claude/settings.json` hooks
(SessionStart etc.) are cloned, but the git hook is not.

`kb session-start` self-heals this: every time it runs, it checks whether
`.git/hooks/post-commit` exists and already calls `kb.py post-commit`. If not, it
recreates the hook from scratch. This means:

- A fresh clone gets the git hook automatically on the first `SessionStart` (first
  Claude Code session in that clone).
- If the hook file is accidentally deleted, it is silently recreated on the next session.
- No manual step is needed after a clone — but the first session's SessionStart hook
  approval prompt IS required (see onboarding section below).

## Heavy work runs off the main thread

The same principle applies beyond startup — long transcripts, large diffs, and
multi-session catch-up are slow and token-heavy, so don't run them inline in the user's
session:

- **Extraction** (the prompts in `references/extraction.md`) — dispatch to a **subagent**
  with the `kb.py outline` + transcript + diff. It runs in isolated context, in parallel,
  and returns proposed diffs without bloating the main thread.
- **`kb catchup`** over many sessions — process sessions in **parallel subagents**, or run
  the whole catch-up as a **background job** and surface the proposed diffs when it
  finishes. Each session's triage is independent, so they fan out cleanly.
- **`reconcile`** — already detached by the hook; you can also schedule it (e.g. a
  post-commit background run) so the cache is always warm.

## CI backstop (recommended)

A PR job that runs `kb status` against the PR diff and **comments** (default) or
**soft-fails** when pages covering changed paths are stale. Keep it a comment, not a
hard fail — the goal is visibility, not friction. This catches drift introduced by
commits made without an agent session, and bypassed local hooks.

## What you can and cannot guarantee

Guaranteed: **detection, reconciliation, and prompting.** Not guaranteed: that a human
authors *good* knowledge — that judgment stays human. The system's job is to surface the
opportunity at near-zero cost (a pre-drafted, git-scoped, propose-not-apply diff) and
make ignoring it visible every session. Running the engine is mechanical; acting on its
output is made cheap and visible, not forced.
