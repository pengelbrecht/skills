# repo-wiki — a self-verifying, agent-first knowledge base for a git repo

> Inspiration: [agentwiki](../../../agentwiki), Karpathy's LLM-wiki concept, Google's
> Open Knowledge Format, and Garry Tan's [GBrain](https://github.com/garrytan/gbrain)
> (MECE directories + resolver; Compiled-Truth/Timeline page shape).

## Problem Statement

How might we give a repo a living, **agent-first** knowledge base whose docs carry proof
of what they were verified against — so **staleness is detected by git, not discovered by
a burned agent** — and which captures the tacit knowledge that today dies at the end of
every human–agent chat?

Repos accumulate docs; most rot silently. A pile of well-formatted-but-untrusted docs is
worse than none. Everything below is downstream of two ideas: **store only what the code
can't regenerate**, and **capture the reasoning that evaporates from chats**.

## Thesis

The bottleneck in software stopped being *generating artifacts* (agents do that) and
became *preserving the reasoning behind them*. As more code is written by agents in
ephemeral sessions, the *why* is destroyed faster than ever. A codebase produced by 100
agent-sessions whose reasoning was discarded is an archaeological disaster — nobody, human
or agent, can safely change it because the invisible constraints are gone. **Capturing
chat-knowledge is the mechanism that keeps agent-built systems safe to evolve.**

---

## Core principles

### Two axes

1. **Recoverability — can it be regenerated from the code?**
   - *Derivable* (file tree, API surface, schema, "what the code does") → **don't persist;
     generate on demand**. It's the fastest-rotting, lowest-value knowledge.
   - *Non-derivable* (the why, gotchas, mental models, constraints, product context) →
     **persist in the wiki**. It's the bulk of what matters and it's mostly *tacit*.
   - Exception: an *expensive-and-hot* derivation (tracing auth across 15 files) may be
     **cached** as a `synthesized`-from-code page with an auto-refresh trigger.

2. **Sourcing — does the truth live here or elsewhere?** (a per-page attribute)
   - `canonical` — born in the wiki; the wiki is the source of truth.
   - `synthesized` — a projection of an external source (code, or an external doc/ADR)
     that remains authoritative; carries a refresh mechanism.

`source` is the keystone: it determines the drift response (below).

> **Persist only the non-derivable.** A folder's file listing is derivable (`ls`) → never
> hand-maintain a catalog. A routing rule is non-derivable → persist it (once, at root).

### Chat is the primary intake

Four of the value-categories are tacit knowledge that surfaces in conversation and is then
thrown away. Code→docs is the cheap cache; **chat→knowledge is the precious, capture-or-
lose-forever stream.**

---

## Structure

**MECE at level 1, free below it. Everything is a folder. Recommended, not prescribed.**

```
repo-wiki/
  INDEX.md           # root: short purpose + MECE resolver rules + the manual
  product/           # PROBLEM   — ICP, personas, jobs, requirements (functional), non-goals, metrics
  glossary/          # LANGUAGE  — ubiquitous language (glossary/glossary.md; split a-f.md… when long)
  architecture/      # SOLUTION  — how it's built/works; synthesized-from-code traversal caches
  constraints/       # RULES     — invariants, NFRs, gotchas (what must stay true)
  decisions/         # RATIONALE — choices + rejected paths (NNNN-slug.md)

  # ── optional: add a slot only when needed ──
  operations/        # OPERATION — deploy/run/monitor/runbooks/incidents (services, not libs)
  roadmap/           # DIRECTION — where it's heading + in-flight work (now.md)
  conventions/       # PROCESS   — how we develop (only what's NOT in linters/the shim)

  inbox/             # raw captures awaiting triage
  archive/           # superseded pages (status: archived) — retired, not deleted
```

### Governance tiers

| Tier | What | Status |
|---|---|---|
| **Discipline** | level-1 MECE (one home), everything-a-folder, self-documenting | **prescribed** |
| **Categories** | the eight subjects above | **recommended** — rename/swap/add; the resolver records reality |
| **Sub-structure** | how a category is organized internally | **free** — agent/user decides |

### `INDEX.md` in every folder — short

Carries **purpose + the local convention as a rule**. Never an instance list.
- ✓ "One page per significant invariant; minor ones grouped." (stable)
- ✗ "auth.md, billing.md, payments.md…" (that's `ls`'s job; it drifts)

Contents discovery = `ls` + descriptive filenames + `covers:` frontmatter + Compiled-Truth
first lines. Root `INDEX.md` additionally holds the resolver table + manual.

### The resolver — "what is the primary subject?"

1. user / why-it-exists / what-to-build → `product/`
2. meaning of a term → `glossary/`
3. how the system *is built / works* → `architecture/`
4. a rule/limit that must hold → `constraints/`
5. why a *past choice* was made → `decisions/`
6. how to run / deploy / recover → `operations/`
7. where it's heading / in flight → `roadmap/`
8. how *we* develop → `conventions/`

| Confusion | Rule |
|---|---|
| architecture vs constraints | *descriptive* "how it works" → architecture; *prescriptive* "what must hold" → constraints |
| constraints vs decisions | *forward-looking rule* → constraints; *backward choice + why* → decisions (a decision can spawn a constraint) |
| architecture vs decisions | "how it **is**" → architecture; "why it **became** that" → decisions |
| product vs roadmap | enduring *problem/users* → product; *sequenced future work* → roadmap |
| operations vs architecture | how to *run/fix* → operations; how it's *structured* → architecture |
| conventions vs constraints | how we *prefer to work* → conventions; a *hard rule the system requires* → constraints |
| functional vs non-functional req | functional → `product/`; non-functional (perf/security/compliance) → `constraints/` |

---

## Page model — Compiled Truth + Timeline

Every page has a cheap mutable head and an append-only immutable evidence trail.

```markdown
---
type: constraint          # product | architecture | constraint | decision | runbook | …
source: canonical         # canonical | from-code | from-doc
covers: [src/billing/**]   # paths this claims about → drift trigger
verified_against: a1b2c3d  # sha/hash at last confirmation (= latest Timeline entry)
status: active            # active | superseded | archived
---

## Compiled Truth      ← cheap head; current synthesis; rewritten on change; injected at session start
Billing endpoints must stay <50 req/s — the upstream ledger API rate-limits us.

## Timeline            ← append-only, immutable provenance
- 2026-06-13 — captured from chat (session abc); 429s above ~50rps — verified @a1b2c3d
- 2026-05-20 — first noted during incident 0002
```

This one shape subsumes: head/body (disclosure), immutable decisions (the Timeline is
append-only; supersede = append + rewrite truth + flip `status`), and provenance
(`verified_against` = latest Timeline sha).

### Freshness — three-way, keyed on `source` (soft signal, never a gate)

| `source` | on drift (covered paths / upstream changed) | auto-apply? |
|---|---|---|
| **from-code** (traversal cache) | re-run traversal, propose update | **yes** — re-reading code can't fabricate |
| from-doc (ADR/spec mirror) | re-summarize from the doc | mostly |
| **canonical** (born here) | flag for human review | **no** — auto-rewrite would fabricate |

Rule: **anyone may *propose* a Timeline append (cheap/safe); rewriting Compiled Truth is
gated by `source`.** Stale = a review-queue entry, not a commit block.

---

## Intake — two streams, watermark-based

| Stream | Source of truth for | Produces | Watermark | Catch-up |
|---|---|---|---|---|
| **git** | the derivable side (what code *is*) | staleness signal + code-cache refresh | last commit `sha` | diff `sha..HEAD` |
| **chats** | the non-derivable side (the *why*) | proposed entries via the resolver | last `session-id` | sessions since cursor |

- **Correctness depends on the watermark + catch-up at session-start, never on a live event
  firing.** Live hooks (post-commit, session-end) are the warm fast-path.
- **Git-aware chat triage:** feed the session's diff into capture — scopes what's mined and
  **auto-stamps `covers`** so a captured constraint is born wired into staleness.
- **Watermarks are local (gitignored)** — chat streams are per-dev/per-machine; only the
  resulting wiki edits are committed.

### Chat engine — vendored, no skill dependency

Vendor the two pure-stdlib `recall` scripts into `skills/repo-wiki/scripts/vendor/recall/`
(+ LICENSE + `PROVENANCE.md` with version pin):
- `recall.py` **list-mode** (`--project <repo> --days N`) = the catch-up enumerator;
  multi-source (**Claude / Codex / pi**) → agent-agnostic. FTS search is a bonus for
  "has this been discussed?" dedup during triage.
- `read_session.py` = the multi-format transcript adapter.

A thin `catchup` wrapper orchestrates: enumerate since watermark → read → git-aware triage
→ propose pages.

---

## CLAUDE.md / AGENTS.md — hollowed into a thin shim

The instruction file is a junk drawer mixing **directives** (do this) and **knowledge**
(this is true). repo-wiki absorbs the knowledge; the file shrinks to a ~12-line **shim**:
1. a minimal always-on **pointer**: "knowledge lives in `repo-wiki/`; read `INDEX.md`
   first; pull pages by relevance; full method = the `repo-wiki` skill", and
2. the few **universal/safety-critical directives** that must stay resident.

Routing: relevant *always* → shim; relevant only when touching specific code → wiki +
`covers`. Three-tier disclosure: **shim (always-on pointer)** → **`repo-wiki/INDEX.md`
(the manual)** → **page bodies (paged in on demand, `covers`-scoped)**. All per-tool files
(CLAUDE/AGENTS/GEMINI) collapse to near-identical shims → one canonical wiki, killing
per-tool duplication. Migrating an existing CLAUDE.md is the *same triage primitive* run
over a file instead of a chat. **Shim-lint** (at session-start) flags re-accreted knowledge.

---

## Activation — ensure the mechanics actually run

It's an **install problem, not a per-use-discipline problem.**

| Trigger | Reliability | Fires | Drives |
|---|---|---|---|
| **SessionStart hook** (`.claude/settings.json`, committed) | high | every session | **heartbeat**: inject wiki + `covers`-scoped pages, report drift, run/prompt catch-up |
| Git hooks (committed via pre-commit/husky) | medium (bypassable) | commit/push | advance git-watermark, fast staleness flag |
| **CI check on PR** | high (server-side) | every PR | **ungameable backstop**: comment/soft-fail on stale pages |
| SessionEnd/Stop | low (best-effort) | session end | warm-path capture |
| SKILL.md / `kb` CLI | discretionary / manual | — | inline capture, on-demand control |

How usage is ensured:
1. **Bootstrap installs the triggers** (writes committed hook config) — one-time, not willpower.
2. **Prefer committed/shared config** so the whole team inherits hooks on clone.
3. **SessionStart is load-bearing + mechanical**; watermarks make it gap-filling.
4. **Visible drift is the flywheel** — consumed every session, so rot is felt and fixed.
5. **CI backstops** the bypassed-hook / no-agent paths.

**Honest limit:** we guarantee *detection, reconciliation, and prompting*. We cannot force
a human to author *good* knowledge — that judgment stays human. The system surfaces the
opportunity at near-zero cost (pre-drafted, git-scoped, propose-not-apply diff) and makes
ignoring it visible every session. Anyone promising a fully-autonomous *correct* KB is
hand-waving the propose-not-apply safety.

---

## MVP scope

**In:** the recommended structure + root resolver `INDEX.md`; per-folder short `INDEX.md`;
Compiled-Truth/Timeline page shape + frontmatter (`type/source/covers/verified_against/
status`); deterministic `kb status` (git staleness via `covers`); vendored recall +
`catchup`; SessionStart hook (inject + drift report + reconcile); `init` bootstrap
(scaffold wiki, install hooks, migrate CLAUDE.md → shim); propose-not-apply review queue.

**Out / not doing:**
- Auto-applying edits to `canonical` pages — propose-only (re-poisons trust otherwise).
- Postgres/pgvector/embeddings retrieval (GBrain's heavy layer) — `covers` + `ls` + grep first.
- OKF-style typed entities/relations — markdown + frontmatter + folders is enough for one repo.
- Backend/agentwiki sync — files-in-repo is self-contained; revisit for cross-repo search.
- Hard staleness gates — soft signal; hard gates breed `--no-verify` habits.
- LLM-judged freshness — git decides stale, deterministically.

## Later / fun

- **Local wiki web viewer** — SHIPPED as `kb serve`. Sidebar tree, page render
  (frontmatter + Compiled Truth + Timeline via vendored marked), in-page TOC, ripgrep
  search, staleness pills, covers chips, backlinks. Stdlib-only, localhost-only,
  read-only. See `skills/repo-wiki/references/web.md`.

## Open questions

- Root file name: `INDEX.md` (convention consistency) vs `README.md` (GitHub front-door)?
- Monorepo: one root `repo-wiki/` vs per-package — start root, split when a package's
  knowledge is self-contained; root INDEX points to children.
- `kb status` as a soft PR comment vs an optional CI soft-fail — default to comment.
- Distribution: ship `recall` vendored, or as an optional auto-detected dependency?
```
