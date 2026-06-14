---
name: repo-wiki
description: >
  Build and maintain a living, agent-first knowledge base for a git repo — a
  "repo-wiki" of architecture, decisions, constraints, product context, and
  glossary that stays trustworthy because staleness is detected by git and tacit
  knowledge is captured from chats. Use this skill whenever a project's docs are
  sprawling or out of date, when onboarding context lives only in people's heads,
  or when the user wants to "set up a knowledge base", "document the
  architecture", "write an ADR / decision record", "capture why we did X", "stop
  the docs from rotting", "keep docs in sync with the code", or "create a repo
  wiki". Also trigger when an agent needs durable project context across sessions,
  when CLAUDE.md / AGENTS.md has become a junk drawer, or after a substantial
  design discussion whose reasoning would otherwise be lost. Even a vague "our
  docs are a mess" or "how do we keep track of decisions" should pull this in.
metadata:
  version: 0.1.0
---

# repo-wiki

A living, **agent-first** knowledge base that lives in a git repo at `repo-wiki/`.
It stays trustworthy because of two commitments: **store only what the code can't
regenerate**, and **capture the reasoning that otherwise dies at the end of every
chat**. Staleness is detected deterministically by git; tacit knowledge is mined
from conversations. Nothing is auto-applied — every change is proposed for a human's
quick yes/no.

> Full design rationale: see `docs/ideas/repo-wiki.md` in this repo if present.
> This SKILL.md is the operating manual; depth lives in `references/`.

## When to use this skill

- **Setting up** a knowledge base for a repo → run `init` (below).
- **Capturing knowledge** during/after a session — a decision settled, a constraint
  learned, a gotcha hit. This is the highest-value, most frequent action.
- **Checking freshness** — which pages drifted from the code (`kb status`).
- **Catching up** on chats the live hook missed (`kb catchup`).
- **Hollowing out** a bloated `CLAUDE.md` / `AGENTS.md` into a thin shim.

## The two ideas that make this work

1. **Recoverability.** Knowledge that can be regenerated from the code (file tree,
   API surface, "what the code does") is the fastest-rotting, lowest-value kind —
   **don't persist it; generate it on demand.** Persist only the *non-derivable*:
   the why, the gotchas, the mental models, the constraints, the product context.
   (Exception: an expensive-and-hot derivation may be *cached* as a `from-code`
   page that auto-refreshes — see `references/pages.md`.)

2. **Chat is the primary intake.** Most non-derivable knowledge is *tacit* — it
   surfaces in conversation and is then thrown away. Code→docs is the cheap cache;
   **chat→knowledge is the precious, capture-or-lose-forever stream.**

If you internalize nothing else: **persist only the non-derivable, and mine the
chats.**

## Quickstart — `init`

Scaffold the wiki, install the activation hook, and create the shim:

```bash
python3 scripts/kb.py init        # run from the repo root
```

This creates `repo-wiki/` with a root `INDEX.md` (the resolver + manual) and the
recommended category folders, installs a `SessionStart` hook into
`.claude/settings.json`, gitignores the local ingest watermark, and — if a
`CLAUDE.md`/`AGENTS.md` exists — offers to migrate its *knowledge* into the wiki and
leave a thin shim behind.

Then read `references/structure.md` and seed the obvious pages (product, a couple of
constraints, any decisions you already know). A new wiki is small — `INDEX.md` plus a
few real pages — not a tree of empty folders.

## Structure (recommended, not prescribed)

MECE at level 1, free below it. **Everything is a folder.** Every folder has a short
`INDEX.md` (purpose + local convention — never a file listing; that's what `ls` is
for).

```
repo-wiki/
  INDEX.md         # root: purpose + the MECE resolver + the manual
  product/         # PROBLEM   — who it's for, why, requirements, non-goals, metrics
  glossary/        # LANGUAGE  — ubiquitous language
  architecture/    # SOLUTION  — how it's built; from-code traversal caches
  constraints/     # RULES     — invariants, NFRs, gotchas (what must stay true)
  decisions/       # RATIONALE — choices + rejected paths (NNNN-slug.md)
  # optional: operations/  roadmap/  conventions/
  inbox/           # raw captures awaiting triage
  archive/         # superseded pages (retired, not deleted)
```

The **resolver** ("what is the primary subject?") and the disambiguation rules that
keep level-1 MECE live in `references/structure.md`. Read it before filing anything.

## Page model — Compiled Truth + Timeline

Every page has a cheap mutable head and an append-only immutable evidence trail:

```markdown
---
type: constraint
source: canonical          # canonical | from-code | from-doc
covers: [src/billing/**]    # paths this claims about → drift trigger
verified_against: a1b2c3d   # sha at last confirmation
status: active              # active | superseded | archived
---

## Compiled Truth     ← current synthesis; rewritten on change; injected at session start
Billing endpoints must stay <50 req/s — the upstream ledger API rate-limits us.

## Timeline           ← append-only provenance
- 2026-06-13 — captured from chat (session abc); 429s above ~50rps — verified @a1b2c3d
```

The rule that keeps trust intact: **anyone may *propose* a Timeline append (cheap,
safe); rewriting Compiled Truth is gated by `source`** — `from-code` may be
auto-regenerated (re-reading code can't fabricate), `canonical` is flagged for a human
(auto-rewrite would fabricate non-derivable truth). Full page conventions and the
three-way freshness model: `references/pages.md`.

## Capturing knowledge (the core loop)

When a session settles a decision, surfaces a constraint, or defines a term, file it.
Use the resolver to pick the folder, the page template (`assets/templates/page.md`)
for the shape, and **propose the diff — don't silently apply it.** If code is
involved, stamp `covers:` with the relevant paths so the page enters the staleness
system already wired in.

**The extraction prompts are the heart of this** — `references/extraction.md` holds
**two** verbatim prompts: one mines a **chat** transcript for durable non-derivable
knowledge — decisions, constraints, terms, gotchas — **even when the session changed no
code** (a decision reached with zero diff is a first-class keeper); the other reconciles
a **commit** diff (refresh `from-code` caches + flag canonical drift) and needs no chat.
Both **first load `python3 scripts/kb.py outline`**
so they route and dedup against the *actual* wiki (real categories + existing pages),
not the generic defaults. Both are stingy and propose-only. Prompt 1 runs at session-end
and inside `kb catchup`; prompt 2 runs at commit/PR/CI.

Most capture is **mechanical**: the `kb catchup` engine mines past sessions so nothing
is lost even if you forget to file inline. See `references/intake.md`.

**Write-back on a cache miss** is the third capture path (alongside chat triage and
code-synthesis): when an agent needs project knowledge the wiki lacks, it resolves it
(reads the code, asks the user, or web-searches) and then **proposes a page** so the next
agent doesn't re-derive it — only when the knowledge is durable and non-obvious. This is
why the shim and root `INDEX.md` carry a "missing knowledge?" instruction: the wiki is a
write-back cache that grows from use, not just from chats.

## Local web viewer — `kb serve`

Browse the wiki in a browser without any external deps:

```bash
python3 scripts/kb.py serve               # default port 7654, auto-detects wiki
python3 scripts/kb.py serve --port 8080   # custom port
python3 scripts/kb.py serve --wiki path/to/repo-wiki   # explicit wiki dir
```

Opens at `http://127.0.0.1:<port>/`. What you get: a sidebar tree, page render with
frontmatter table + Compiled Truth + Timeline, in-page TOC, ripgrep search,
staleness pills (fresh / stale / unverified), covers chips, and backlinks.

Design stance: **stdlib-only server, vendored offline assets, localhost-only,
read-only.** Editing pages via the browser is a deferred follow-up (see
`references/web.md`). Full technical details (API routes, security posture, asset
provenance): `references/web.md`.

## Comments — human-in-the-loop feedback

The wiki viewer lets users highlight text and post inline comments. These land in
`<wiki>/.comments/comments.jsonl` and are surfaced to agents two ways:

- **Passive hook** (`assets/templates/comments-hook.sh`, wired as a `UserPromptSubmit`
  hook): injects open comments at the top of every agent turn with zero poll overhead.
- **Active watch loop**: the agent calls `kb.py comments list --json --since <cursor>`
  on a short interval, acts on new comments, and advances the cursor.

In either case the **consumption protocol** is: read the anchor (`page`, `line`,
`section`, `selected_text`), act (usually edit the `.md` directly — the comment is the
approval), append a Timeline entry, then `kb.py comments resolve <id> --note "..."`.

Full details — hook install snippet, watch-loop pseudocode, act-then-resolve rules,
edge cases: `references/comments.md`.

## Staleness & catch-up

```bash
python3 scripts/kb.py status      # which pages drifted from the code (soft signal)
python3 scripts/kb.py catchup     # mine chat sessions since the watermark
```

`status` is deterministic: it intersects each page's `covers` globs with what changed
in git since its `verified_against` sha. Stale = a review-queue entry, **never a
commit gate** (hard gates breed `--no-verify` habits). `catchup` wraps the vendored
`recall` scripts (multi-agent: Claude / Codex / pi) to enumerate and read sessions.
Details and the watermark model: `references/intake.md`.

**Keep heavy work off the main thread.** Long transcripts, large diffs, and multi-session
catch-up are slow and token-heavy — **dispatch extraction and `catchup` to subagents or a
background job**, never inline in the user's session. The `SessionStart` hook is already
non-blocking by design: `kb.py session-start` does no git scan (it reports a cached drift
summary and spawns a detached `kb.py reconcile` to refresh it). See
`references/activation.md`.

## Activation — making it actually run

The point of the `SessionStart` hook is that maintenance is an **install problem, not
a willpower problem**. Once `init` writes the (committed) hook config, every session
injects the wiki, reports drift, and reconciles missed chats — regardless of whether
anyone remembers. Add a CI check on PRs as the ungameable backstop. See
`references/activation.md`.

## CLAUDE.md / AGENTS.md → thin shim

The instruction file mixes *directives* (do this) and *knowledge* (this is true).
repo-wiki absorbs the knowledge; the file shrinks to a ~12-line shim: a minimal
always-on pointer to the wiki plus the few universal/safety directives. Migrating an
existing file is the same triage primitive run over a file instead of a chat. See
`references/claude-md-shim.md` and `assets/templates/shim.md`.

## Reference map

| File | Read it when |
|---|---|
| `references/extraction.md` | **the triage prompt** — mining a chat + git diff into proposed pages |
| `references/structure.md` | filing a page; setting up folders; the resolver + disambiguation |
| `references/pages.md` | writing a page; frontmatter; the three-way freshness model |
| `references/intake.md` | git + chat streams, watermarks, `catchup`, the vendored recall scripts |
| `references/activation.md` | hooks, the SessionStart heartbeat, CI backstop, install discipline |
| `references/claude-md-shim.md` | migrating CLAUDE.md/AGENTS.md; what stays vs what moves |
| `references/web.md` | `kb serve` — run instructions, API routes, architecture, security |
| `references/comments.md` | wiki comments — passive hook, active watch loop, act-then-resolve consumption protocol |

## Honest limit

This skill guarantees *detection, reconciliation, and prompting*. It cannot force a
human to author *good* knowledge — that judgment stays human. It surfaces the
opportunity at near-zero cost (a pre-drafted, git-scoped, propose-not-apply diff) and
makes ignoring it visible every session. Don't promise a fully-autonomous *correct*
KB; the human-in-the-loop on `canonical` pages is a feature, not a gap.
