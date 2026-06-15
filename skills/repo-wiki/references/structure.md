# Structure & the resolver

The structure is **recommended, not prescribed**. The *discipline* is fixed; the
*categories* are a sensible default; the *sub-structure* is free.

| Tier | What | Status |
|---|---|---|
| **Discipline** | level-1 is MECE (one home), everything is a folder, self-documenting via `INDEX.md` | **prescribed** |
| **Categories** | the eight subjects below | **recommended** — rename/swap/add; the resolver records reality |
| **Sub-structure** | how a category is organized internally | **free** — agent/user decides |

A default earns its value through *conventionality*: an agent dropped into any
repo-wiki should find `decisions/` where its priors expect. Deviating is allowed but
not free. The rule that keeps deviation safe: **whatever structure the repo picks, the
resolvers describe it.** Keep it MECE and self-documenting and it stays discoverable.

## Everything is a folder

Even singletons. A short glossary is `glossary/glossary.md`; when it grows, split into
`glossary/glossary_a-f.md`, `glossary/glossary_g-m.md`, … This kills the per-category
"dir or doc?" decision, makes "split on growth" seamless, and gives every category a
stable path prefix.

## `INDEX.md` in every folder — short

Carries **purpose + the local convention as a rule.** Never an instance list — that's
`ls`'s job, and a hand-maintained catalog drifts the moment someone adds a file.

```
constraints/INDEX.md
─────────────────────
# constraints/
Invariants, NFRs, and gotchas — rules that must stay true.
(NFRs route here; functional requirements → product/.)
Organized: one page per significant invariant; minor ones grouped.
```

- ✓ "One page per significant invariant." (a *rule* — stable)
- ✗ "auth.md, billing.md, payments.md…" (an *instance list* — drifts)

Contents discovery = `ls` + descriptive filenames + `covers:` frontmatter +
Compiled-Truth first lines. The **root `INDEX.md`** additionally holds the resolver
table below + the manual (page model, intake, propose-not-apply). Nested `INDEX.md`
beyond the per-folder blurb are opt-in — add a curated reading order only for a large
folder where it beats `ls`, and know you must keep it current.

## The recommended categories

```
repo-wiki/
  product/         # PROBLEM   — ICP, personas, jobs, requirements (functional), non-goals, metrics
  glossary/        # LANGUAGE  — ubiquitous language
  architecture/    # SOLUTION  — how it's built/works; from-code traversal caches
  constraints/     # RULES     — invariants, NFRs, gotchas (what must stay true)
  decisions/       # RATIONALE — choices + rejected paths (NNNN-slug.md)

  # ── optional: add a slot only when needed ──
  operations/      # OPERATION — deploy/run/monitor/runbooks/incidents (services, not libs)
  roadmap/         # DIRECTION — where it's heading + in-flight work (now.md)
  conventions/     # PROCESS   — how we develop (only what's NOT in linters / the shim)

  inbox/           # raw captures awaiting triage
  archive/         # superseded pages (status: archived) — retired, not deleted
```

Top five are near-universal; the bottom three are common-but-not-universal (a library
has no `operations/`). The structure is a **destination map, not a day-one checklist** —
a new wiki is `INDEX.md` + a few real pages, never a tree of empty folders.

## The resolver — "what is the primary subject?"

1. A user / market / *why it exists* / what to build → `product/`
2. The meaning of a term → `glossary/`
3. How the system *is built or works* → `architecture/`
4. A rule or limit that must hold → `constraints/`
5. Why a *past choice* was made → `decisions/`
6. How to run / deploy / recover it → `operations/`
7. Where it's heading or what's in flight → `roadmap/`
8. How *we* develop (standards, workflow) → `conventions/`
9. Unsorted / unsure → `inbox/`  ·  Dead / superseded → `archive/`

## Disambiguation rules (what makes it MECE, not just tidy)

| Confusion | Rule |
|---|---|
| architecture vs constraints | *descriptive* "how it works" → architecture; *prescriptive* "what must hold" → constraints |
| constraints vs decisions | *forward-looking rule* → constraints; *backward choice + why* → decisions (a decision can spawn a constraint) |
| architecture vs decisions | "how it **is**" → architecture; "why it **became** that" → decisions |
| product vs roadmap | enduring *problem/users* → product; *sequenced future work* → roadmap |
| operations vs architecture | how to *run/fix* it → operations; how it's *structured* → architecture |
| conventions vs constraints | how we *prefer to work* → conventions; a *hard rule the system requires* → constraints |
| functional vs non-functional req | functional → `product/`; non-functional (perf/security/compliance) → `constraints/` |

## Worked examples

- "Pre-revenue, targeting seed-stage founders" → `product/`
- "A *workspace* is a billing boundary, not a team" → `glossary/`
- "Auth flows through middleware X then service Y" → `architecture/`
- "Never call the ledger API above 50 rps" → `constraints/`
- "Chose Postgres over Mongo for transactional writes" → `decisions/`
- "To roll back: flip flag X, redeploy" → `operations/`
- "Mid-migration REST→gRPC; new endpoints gRPC-only" → `roadmap/now.md`
- "Trunk-based dev, squash-merge" → `conventions/`

## Bootstrap Gate 1 — recording the agreed structure

When cold-starting a wiki via `kb bootstrap`, Gate 1 produces an agreed category set
(see `references/bootstrap.md`). That agreement is **recorded in the root `INDEX.md`
resolver** — the category table and disambiguation rules are updated to reflect the
actual chosen structure before any mining begins. Whatever structure is agreed **must
remain MECE**: exactly one home per fact, no overlaps, no gaps. This is enforced at
Gate 1, not after-the-fact — agreeing a MECE structure upfront is what makes every
subsequent page-routing decision unambiguous.
