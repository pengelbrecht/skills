# Intake: two streams, watermark-based

Knowledge enters the wiki from exactly two sources. They map onto the two knowledge
types: git is the truth for the *derivable* side, chats for the *non-derivable*.

| Stream | Source of truth for | Produces | Watermark | Catch-up |
|---|---|---|---|---|
| **git** (file changes) | the derivable side — what the code *is* | staleness signal + from-code refresh | last commit `sha` | diff `sha..HEAD` |
| **chats** (conversations) | the non-derivable side — the *why* | proposed pages via the resolver | last `session-id` | sessions since the cursor |

## Correctness lives in the watermark, not in events

A session-end hook is best-effort — crashes, `/clear`, a closed window all drop chat
knowledge. So **don't depend on any live event firing.** Persist a cursor; at the next
session-start, compare it against the sessions/commits that actually exist and backfill
the gap. Live hooks (post-commit, session-end) are the warm fast-path; the watermark +
catch-up reconciliation is the guarantee. This mirrors git itself: you never "watch"
commits, you diff against a ref.

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

## Watermarks are local

Chat streams are per-developer, per-machine (each person's transcripts are on their own
disk); the wiki is shared via git. So the ingest watermark is **local — gitignored**
(`repo-wiki/.ingest/state.json`). Only the resulting wiki edits are committed. A
committed watermark would wrongly tell teammate B they're "caught up" on A's chats.

State file shape:

```json
{ "git_sha": "a1b2c3d", "chat_session_id": "1f794dc0-…", "ts": "2026-06-13T16:41:00Z" }
```

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
local-watermark model. Only wiki edits are committed.

## Code-synthesis on git change

When a `from-code` page's `covers` paths change, the same git diff that flags it can
trigger a **re-synthesis**: re-trace the code, propose the updated Compiled Truth. This
is the one place auto-regeneration is safe (re-reading code can't fabricate). `kb
status` surfaces these alongside canonical drift; the difference is the suggested action
(re-synthesize vs flag-for-review).
