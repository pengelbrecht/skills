# Activation: making the mechanics actually run

The mechanics (staleness check, chat catch-up, synthesis) are worthless if nothing
fires them. The key reframe: **this is an install problem, not a per-use-discipline
problem.** You don't ensure usage by hoping the agent remembers; you install reliable
triggers once, prefer committed/shared config, and make drift visible.

## Triggers, by reliability

| Trigger | Reliability | Fires | Drives |
|---|---|---|---|
| **SessionStart hook** (`.claude/settings.json`, committed) | high — unconditional | every session begins | **the heartbeat**: inject the wiki + `covers`-scoped pages, report drift, run/prompt catch-up + staleness reconcile |
| Git hooks (committed via pre-commit / husky) | medium — bypassable | commit / push | advance git-watermark, fast staleness flag |
| **CI check on PR** | high — server-side | every PR | **ungameable backstop**: comment / soft-fail on stale pages |
| SessionEnd / Stop hook | low — best-effort | session ends | warm-path chat capture |
| SKILL.md instructions / `kb` CLI | discretionary / manual | during work / on demand | inline capture, on-demand control |

## How usage is ensured

1. **Bootstrap installs the triggers.** `kb.py init` writes the SessionStart hook into
   `.claude/settings.json`, gitignores the watermark, and (optionally) installs git
   hooks. One-time setup, not recurring willpower.
2. **Prefer committed/shared config.** `.claude/settings.json` and a committed
   `pre-commit`/husky config are inherited by everyone on clone — usage isn't
   per-developer opt-in.
3. **SessionStart is load-bearing and mechanical.** It fires every session regardless
   of agent cooperation; combined with watermarks it *reconciles*, catching whatever the
   best-effort hooks missed. Correctness never depends on a live event firing.
4. **Visible drift is the flywheel.** Because SessionStart both injects the wiki (used
   every session) and reports drift, rot is felt immediately and constantly — the same
   pressure that gets failing CI fixed.
5. **CI backstops** the bypassed-hook and no-agent paths (pure-git commits with no
   session) server-side, where it can't be skipped.

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
