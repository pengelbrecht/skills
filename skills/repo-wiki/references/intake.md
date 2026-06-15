# Intake: two streams, watermark-based

Knowledge enters the wiki from exactly two sources. They map onto the two knowledge
types: git is the truth for the *derivable* side, chats for the *non-derivable*.

| Stream | Source of truth for | Produces | Watermark | Catch-up trigger |
|---|---|---|---|---|
| **git** (file changes) | the derivable side — what the code *is* | staleness signal + from-code refresh | last commit `sha` | post-commit hook (diff-scoped nudge), SessionStart (cached summary) |
| **chats** (conversations) | the non-derivable side — the *why* | proposed pages via the resolver | last `session-id` | **auto**: PreCompact, SessionEnd, SessionStart (count via background reconcile); **manual**: `kb catchup` |

## Auto-triggered chat catch-up

Chat catch-up is now wired into three automatic hooks (not just `kb catchup`):

- **PreCompact** — fires before context is compacted. Prints a directive to mine the
  current window for durable knowledge before it is lost.
- **SessionEnd** — fires when the session ends. Nudges the agent to run `kb catchup`
  before the session window is gone.
- **SessionStart** — reads the cached count of un-ingested chat sessions (written by the
  background `reconcile`). If sessions are pending, surfaces the count as a prompt
  to run `kb catchup`. The count is cached so session start stays fast.

`kb catchup` remains the explicit command for manual or batch catch-up. The auto hooks
are warm-path reminders; the watermark + reconcile guarantee correctness even if all live
hooks miss.

## Correctness lives in the watermark, not in events

A session-end hook is best-effort — crashes, `/clear`, a closed window all drop chat
knowledge. So **don't depend on any live event firing.** Persist a cursor; at the next
session-start, compare it against the sessions/commits that actually exist and backfill
the gap. Live hooks (post-commit, session-end, precompact) are the warm fast-path; the
watermark + catch-up reconciliation is the guarantee. This mirrors git itself: you never
"watch" commits, you diff against a ref.

## Git-aware chat triage

The two streams are strongest together, so feed the session's diff into the chat
triage: "these files changed this session — what durable knowledge about them did we
establish?" This **scopes** the capture (mine what's grounded in the change, not the
whole transcript) and **auto-stamps `covers`** from the changed paths, so a captured
constraint is born already wired into the staleness system.

The concrete, verbatim triage prompt — taking the transcript **and** the diff, with the
non-derivable/durable/grounded filter and the two-pass (tacit capture + code-synthesis)
structure — lives in `references/extraction.md`. That's the actual extraction logic;
this file just covers the plumbing around it.

## Watermarks: a local cursor + a committed seed baseline

Chat streams are per-developer, per-machine (each person's transcripts are on their own
disk); the wiki is shared via git. So the **per-machine ingest cursor is local —
gitignored** (`repo-wiki/.ingest/state.json`). A committed *session-id* cursor would
wrongly tell teammate B they're "caught up" on A's chats — session ids only exist on the
machine that produced them.

Local cursor shape (gitignored):

```json
{ "git_sha": "a1b2c3d", "chat_session_id": "1f794dc0-…", "ts": "2026-06-13T16:41:00Z" }
```

But there is one piece of ingest state that IS legitimately shared: the **seed
baseline** (`repo-wiki/.ingest/seed.json`, *tracked*). When a wiki is seeded it mines
the pre-seed chat history into committed pages — so "history up to the seed time is
accounted for" is a fact about the *committed wiki*, true for everyone. The seed baseline
records only portable fields — `{ "git_sha", "ts" }`, **no** machine-specific session id:

```json
{ "git_sha": "f00dbabe", "ts": "2026-06-15T16:40:00Z" }
```

`kb watermark --seed` writes both (local cursor with the seed machine's newest session
id, plus this committed baseline). The boundary used by the heartbeat counter and
`kb catchup` (`uningested_sessions`) is the local cursor overlaid on the seed baseline:
prefer the local session id when it's present in the listing; otherwise fall back to the
baseline's `ts` (date boundary). That date fallback is what stops a **fresh clone** —
empty local cursor, seed id from another machine — from re-reporting the entire pre-seed
history. The counter and catchup read the same boundary, so they always agree.

A single id/timestamp cursor handles the normal "all sessions after it" case. To
survive true holes (session 5 ingested but 4 wasn't), also keep an `ingested.log` of
processed session IDs and diff against the available set.

## The chat engine — vendored recall (no skill dependency)

`scripts/vendor/recall/` holds two pure-stdlib scripts copied from the `recall` skill
(see `PROVENANCE.md` for the pinned version). They are the catch-up engine:

- `recall.py` in **list-mode** (`--project <repo> --days N`, no query) enumerates every
  session in the window, newest first — across **Claude Code, Codex, and pi** (so the
  wiki is agent-agnostic). With a query it does BM25 full-text search, useful to dedup a
  captured constraint against past sessions before proposing it.
- `read_session.py <file>` reads a raw transcript, auto-detecting the format.

`scripts/kb.py catchup` wraps them: enumerate sessions since the watermark → read each
un-ingested one → run the git-aware triage → propose pages → advance the watermark.

```bash
# under the hood, roughly:
python3 scripts/vendor/recall/recall.py --project "$(pwd)" --days 14
python3 scripts/vendor/recall/read_session.py <transcript-path>
```

The recall index (`~/.recall.db`) is machine-local cache — consistent with the
local-cursor model. Committed artifacts are the wiki edits plus the portable seed
baseline (`repo-wiki/.ingest/seed.json`); the per-machine cursor stays gitignored.

## Code-synthesis on git change

When a `from-code` page's `covers` paths change, the same git diff that flags it can
trigger a **re-synthesis**: re-trace the code, propose the updated Compiled Truth. This
is the one place auto-regeneration is safe (re-reading code can't fabricate). `kb
status` surfaces these alongside canonical drift; the difference is the suggested action
(re-synthesize vs flag-for-review).
