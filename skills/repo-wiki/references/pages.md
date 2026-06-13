# Page model: Compiled Truth + Timeline

Every page has two parts: a cheap, mutable **Compiled Truth** (the current best
understanding) and an append-only, immutable **Timeline** (the evidence trail). One
shape subsumes head/body disclosure, immutable decisions, and provenance.

```markdown
---
type: constraint          # product | architecture | constraint | decision | runbook | incident | glossary
source: canonical         # canonical | from-code | from-doc
covers: [src/billing/**]   # paths this page makes claims about → the drift trigger
verified_against: a1b2c3d  # sha (or hash) at last confirmation; == the latest Timeline entry
status: active            # active | superseded | archived
---

## Compiled Truth
Billing endpoints must stay <50 req/s — the upstream ledger API rate-limits us.

## Timeline
- 2026-06-13 — captured from chat (session abc); ledger 429s above ~50rps — verified @a1b2c3d
- 2026-05-20 — first noted during incident 0002
```

- **Compiled Truth** is what gets injected at session start (the cheap head). Keep it
  terse and claim-first so it's cheap to read and inject.
- **Timeline** is append-only. "Supersede, don't edit" = append an entry, rewrite
  Compiled Truth, and flip `status`. The newest Timeline sha *is* `verified_against`.

## Frontmatter fields

| Field | Meaning |
|---|---|
| `type` | the page kind (drives nothing mechanical; aids the reader) |
| `source` | **the keystone** — decides the drift response (below) |
| `covers` | globs of code this page claims about; `kb status` intersects these with git diffs |
| `from` | (synthesized only) the upstream source — code paths or an external doc path/URL |
| `verified_against` | the sha/hash the page was last confirmed against |
| `status` | `active` (live), `superseded` (newer page wins), `archived` (retired) |

`covers` is for **canonical/from-code** pages ("this claim is about these paths").
`from` is for **synthesized** pages ("I am derived from this upstream"). A page can
carry both when a cached traversal is *about* the same paths it's *derived from*.

## The two axes, as page attributes

- **Recoverability** — is this regenerable from code? If yes and cheap → don't persist;
  generate on demand. If yes but *expensive-and-hot* (e.g. tracing a flow across 15
  files) → cache it as a `from-code` page. If no → it's the durable core.
- **Sourcing** (`source`) — `canonical` (born here, the wiki is the source of truth) vs
  `synthesized` (`from-code`/`from-doc`, a projection of an upstream that stays
  authoritative).

## Three-way freshness (keyed on `source`)

Staleness is always a **soft signal** — a review-queue entry, never a commit gate.
What differs is the suggested action when covered paths / upstream change:

| `source` | on drift | auto-apply? |
|---|---|---|
| **from-code** (traversal cache) | re-run the traversal, propose the updated page | **yes** — re-reading code can't fabricate |
| **from-doc** (ADR/spec mirror) | re-summarize from the upstream doc | mostly — propose the diff |
| **canonical** (born here) | flag for human review ("is this still true?") | **no** — auto-rewrite would fabricate non-derivable truth |

The load-bearing rule: **anyone (including an agent) may propose a Timeline append —
cheap and safe. Rewriting Compiled Truth is gated by `source`.** This is what keeps a
plausible-but-wrong auto-edit from re-poisoning the trust the wiki exists to protect.

## Synthesize sparingly

Every `synthesized` page is a mirror that *will* drift and demands re-syncs — a
standing freshness debt. Only persist one when (a) the upstream is authoritative and
(b) the page is read often enough to amortize the re-sync. Otherwise prefer
generate-on-demand over a persisted mirror.

## Decisions are a special case

`decisions/NNNN-slug.md` are `canonical`. The rejected alternatives and rationale live
in the **Timeline** (immutable history). Compiled Truth states the current standing of
the decision ("we use Postgres"); when superseded, append a Timeline entry, rewrite
Compiled Truth, set `status: superseded`, and add a new decision that references it.
Decisions don't rot — they get superseded.
