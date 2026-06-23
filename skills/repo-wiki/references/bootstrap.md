# Bootstrap — interactive wiki creation protocol

Bootstrap = the universal guided procedure for **creating a wiki structure and seeding
content**. It applies to **every repo — new or existing** — because the wiki structure
must always be agreed with the user before anything is scaffolded. Bootstrap drives two
human gates before any mining runs, proposes but never applies changes, and fans mining
work out to parallel subagents so a cold-start on an existing repo is fast.

> **`kb init` does NOT scaffold wiki structure.** It installs plumbing only (hooks +
> gitignore + `.ingest/`). The wiki structure is NEVER created automatically — it must
> be agreed with the user first via this flow (scan → propose → agree → scaffold).
> `kb init` and `kb plumbing` are both plumbing-only; `kb scaffold` (after Gate 1) is
> what creates the structure.

Three invariants that apply end-to-end:

- **Apply-and-report.** The *structure* still needs agreement before scaffolding (Gate 1
  below) — a folder tree is a one-time structural commitment. But once it's agreed, the
  page **content** is written directly and the import batch is **reported** so the user
  can review or `git`-revert; no per-page approval gate. See
  [[0005-apply-and-report-not-propose]].
- **Stingy.** A few real, durable, non-derivable pages beats a folder of thin stubs.
  If nothing durable was found in a source, write nothing.
- **Always-MECE.** The agreed structure must have exactly one home per fact. No overlaps,
  no gaps. Every page is routed through the agreed resolver before being written.

---

## Step 0 — Gather signals (read-only)

Run the bootstrap enumeration before presenting anything to the user:

```bash
python3 scripts/kb.py bootstrap          # human-readable report
python3 scripts/kb.py bootstrap --json   # machine-readable; parse for structured use
```

This is **read-only** — safe to run repeatedly; it never creates or modifies any file.

The report provides two blocks of information needed for the two gates:

**STRUCTURE SIGNALS** — what the repo already has:
- whether an ADR directory exists (`adr_dir`) and its path
- whether `docs/` is present and how many `.md` files it contains
- ops indicators (Dockerfile, docker-compose, Procfile, k8s/, .github/workflows/, Makefile) and the derived `suggest_operations` flag
- whether `repo-wiki/` already exists
- which instruction files are present (CLAUDE.md, AGENTS.md, GEMINI.md)

**SOURCE COUNTS** — how much material each source holds:
- chats: session count + date range (oldest → newest)
- commits: total count + date range
- existing docs: enumerated file list (READMEs, docs/, ADR dir, instruction files)
- code dirs: top-level source directories with rough file counts (candidate subsystems)

Load this output into context before presenting Gate 1.

---

## Step 0.5 — Install plumbing (order-independent)

Run `kb plumbing` (or equivalently `kb init`) any time — before or after Gate 1,
before or after `kb scaffold`. It installs all hooks (`SessionStart`,
`UserPromptSubmit`, `PreCompact`, `SessionEnd`, `post-commit`) and gitignores the
local ingest dirs. No dirs or INDEX files are created.

```bash
python3 scripts/kb.py plumbing   # or: python3 scripts/kb.py init  (same effect)
```

This is idempotent and safe to run immediately. The hooks work even before any wiki
structure exists — plumbing is fully independent of structure. Do not expect
`kb init` to create `repo-wiki/` folders or INDEX files; it never does.

---

## GATE 1 — Agree the structure (always MECE)

Present the proposed category set to the user and get explicit agreement **before
scaffolding or mining anything.** Gate 1 is a conversation — ask the user, wait for
their answer, and record what was agreed.

### Propose a MECE category set adapted to this repo

Start from the default eight categories in `references/structure.md` and adapt using the
bootstrap signals:

| Signal | Adaptation |
|---|---|
| `suggest_operations == true` | include `operations/` (service repo; deploy/run/monitor) |
| `adr_dir` found | include `decisions/`; note it will **reference/synthesize** the existing ADRs rather than duplicate them — the ADR files stay where they are |
| no ops indicators AND not a service | omit `operations/` |
| no evidence of user/market context | `product/` can be sparse or omitted if the user agrees |
| any custom need the user names | add a slot; ensure no overlap with existing slots |

Present the proposed set as a short table (folder name + one-line purpose). Example
format:

```
Proposed wiki structure for this repo:

  product/        — users, requirements, non-goals
  glossary/       — ubiquitous language
  architecture/   — how it's built; code-derived caches
  constraints/    — invariants, NFRs, gotchas
  decisions/      — choices + rejected paths (synthesizes adr/ — existing files stay)
  operations/     — deploy, run, monitor, runbooks  [suggested: Dockerfile detected]
  inbox/          — raw captures awaiting triage
  archive/        — retired pages

Omitted (no signal): roadmap/, conventions/
```

Then ask:

> "Does this structure work? You can rename, add, or remove categories. One constraint:
> the final set must stay MECE — exactly one home per fact. I'll record any deviations
> from the default in the root `INDEX.md` resolver."

### Invariant: MECE throughout

If the user renames, adds, or removes categories, apply the disambiguation rules from
`references/structure.md` to keep the resolver consistent. No two categories may have
overlapping scope; every expected topic must have exactly one home. If a proposed change
would create overlap, surface the conflict and resolve it before proceeding.

### Record the agreed structure

Once the user approves, **record the agreed structure in the root `INDEX.md` resolver**,
including any deviations from the default set (e.g., a renamed category, an added
custom slot, an omitted standard slot with the reason). This is the resolver all mining
subagents will use in Step 3.

### Then scaffold the agreed structure

Only after Gate 1 agreement is recorded: run `kb scaffold` with the agreed category
set. An explicit flag is required — `kb scaffold` with no flags creates nothing (it
prints the recommended proposal + agree-first reminder instead).

```bash
# User accepted the recommended set as-is:
python3 scripts/kb.py scaffold --recommended

# User accepted recommended set + wants operations (e.g. ops indicators found):
python3 scripts/kb.py scaffold --recommended --add operations

# User agreed a custom subset + extra:
python3 scripts/kb.py scaffold --only product,decisions,architecture --add operations
```

`kb scaffold` creates `repo-wiki/` + the agreed folders + INDEX files. **It installs no
hooks** — plumbing is separate and order-independent (see Step 0.5 below).

Do **not** scaffold or mine before the structure is agreed. The resolver must exist
before any page is proposed, so that every proposal has exactly one valid home.

---

## GATE 2 — Agree the ingestion scope (per source, informed by the counts)

Present each source with its count from Step 0 and offer scope options. Capture the
user's explicit choice per source. Do not mine outside the agreed scope.

Present Gate 2 as a structured checklist. Example:

```
What should we mine? (counts from kb bootstrap)

  chats — 47 sessions (2024-03-15 → 2026-06-15)
    □ all project history
    □ last N days — how many?
    □ none

  commits — 312 commits (2024-01-08 → 2026-06-14)
    □ all history
    □ since <date or tag>
    □ none

  existing docs — README.md, docs/architecture.md, docs/adr/*, CLAUDE.md (6 files)
    □ include all
    □ include specific files: ___
    □ skip docs
    □ skip instruction files (CLAUDE.md / AGENTS.md)

  code subsystems — src/ (142 files), scripts/ (23 files), lib/ (67 files)
    □ map all top-level dirs
    □ map specific dirs: ___
    □ skip code mapping
```

Wait for the user to fill in choices before proceeding. The scope answers become the
bounds for Step 3 — no subagent mines outside what was agreed here.

---

## Step 3 — Mine (cold-start mining — fanned out to parallel subagents)

**Farm maximal work to parallel subagents.** Bootstrap is slow if run sequentially —
transcripts are long, diffs are large, and code traversal is expensive. Per
`references/activation.md` ("Heavy work runs off the main thread") and
`references/extraction.md` ("dispatch each extraction to a subagent"), dispatch **one
subagent per source** and parallelize within a source where feasible. The two gates stay
in the interactive main thread; only mining fans out.

The main agent dispatches all subagents simultaneously, then waits for their proposals
before proceeding to Step 4.

### Subagent roster

#### docs subagent(s)

Migrate each in-scope existing doc (README, docs/, ADR directory, instruction files)
into proposed wiki pages. Use the migration triage from `references/claude-md-shim.md`
generalized to any file:

1. Walk the file section by section (or the whole file if short).
2. Classify each piece: **directive** (stays in the instruction file) vs **knowledge**
   (moves to the wiki).
3. Route knowledge through the agreed resolver — exactly one home per fact.
4. Stamp `covers` where the knowledge is code-scoped; leave `covers: []` for
   process/product/cross-cutting knowledge.
5. For ADR files: synthesize the decision + rationale into a `decisions/` page; record
   the original file path in the Timeline entry; do not duplicate the ADR content.

Spawn one subagent per large document (or one per ADR batch) if the volume warrants it.
Each returns proposed page diffs only.

#### chat subagent(s)

Run `references/extraction.md` **Prompt 1** (chat extraction) over the in-scope
sessions. Batch sessions to keep subagent context sizes manageable — for example, group
by month or by a fixed session count, and dispatch **one subagent per batch**. Each
subagent receives:

- The wiki outline (`python3 scripts/kb.py outline`) so it routes against the actual
  agreed structure.
- The batch of transcripts (read via `scripts/vendor/recall/read_session.py <file>`).
- The scope agreed at Gate 2 (date bounds or session list).

Per Prompt 1: keep only knowledge that is non-derivable, durable, and relevant to the
repo. Be stingy — most sessions yield 0–3 items. If nothing durable was settled in a
batch, propose nothing.

#### commit subagent

Mine decision-shaped commit messages within the agreed scope. Dispatch one subagent
with:

- The agreed commits scope (all / since <date|tag>).
- The git log: `git log --format="%H %ad %s%n%b" --date=short` (within scope).
- The wiki outline.

The subagent scans for commits whose messages describe a *choice* — a why, a tradeoff,
a rejected path, a constraint. These route to `decisions/`. Routine chore/fix commits
yield nothing. Return proposed `decisions/` page diffs only.

#### code subagent(s)

One subagent per chosen subsystem:

- Run an architecture orientation (`kb map <subsystem>` or equivalent code traversal)
  to produce a proposed `architecture/<subsystem>-overview.md` page.
- Where a cross-file flow is expensive to re-trace and will be read often, propose a
  `from-code` cache page in `architecture/`.
- Mark every proposed architecture page with `source: from-code` and
  `verified_against: <current HEAD sha>`.

### Verbatim per-subagent mining instruction

Give every mining subagent the following instruction verbatim (customize the
source-specific parts in brackets):

---

> You are a mining subagent doing cold-start bootstrap extraction for a repo-wiki.
>
> **Your inputs:**
> - WIKI OUTLINE (from `python3 scripts/kb.py outline`) — the agreed structure, resolver,
>   and existing pages. This is your ground truth for routing and dedup.
> - [SOURCE-SPECIFIC INPUT: transcript batch / git log range / file(s) / code subsystem]
> - AGREED SCOPE from Gate 2: [scope agreed by user]
>
> **Your job:** Extract durable, non-derivable knowledge from the source and return
> PROPOSED PAGES ONLY — never write any file.
>
> **Keep only knowledge that is ALL THREE of:**
> 1. **Non-derivable** — cannot be regenerated by reading the code: a decision + rejected
>    alternatives + rationale, a constraint, a gotcha, load-bearing weirdness, a mental
>    model, product/user context, the meaning of a domain term.
> 2. **Durable** — still matters next month. Not transient, not status.
> 3. **Relevant to the repo** — shapes how this project is understood or evolves.
>
> **Discard:** restatements of what the code plainly says; anything rederivable by
> reading the repo; chit-chat; tool output; status updates; anything already in the wiki
> outline.
>
> **Be stingy.** A cold-start should produce a few real pages, not an exhaustive tree of
> thin stubs. If a source yields nothing durable, propose nothing.
>
> **For each kept item:**
> 1. Route through the **WIKI OUTLINE resolver** (the agreed categories, including any
>    deviations recorded in `INDEX.md`). Exactly one home per fact.
> 2. Check the outline for existing pages that already cover this — if one exists,
>    propose an *update* (append Timeline, rewrite Compiled Truth), not a new page.
> 3. Set `source:` appropriately: `canonical` for knowledge born in discussion or docs;
>    `from-code` for code-derived synthesis.
> 4. Set `covers:` to the code paths the knowledge is *about* (not what changed). Leave
>    `covers: []` for cross-cutting or process knowledge.
> 5. Set `verified_against:` to the current HEAD sha.
> 6. Write terse, claim-first **Compiled Truth** + one **Timeline** entry:
>    `- <date> — [mined from bootstrap: <source description>] — @<HEAD-sha>`.
>
> **Mark gaps explicitly.** If you cannot determine something and it matters (e.g. the
> intended deployment model, a key constraint, the primary user persona), write a
> `inbox/bootstrap-gaps.md` entry: `- couldn't determine <X> — confirm with the team`.
> Do **not** fabricate or guess. A gap honestly marked is more useful than a wrong page.
>
> **Output format:** one proposed page diff per item, each with a one-line summary and
> the full proposed page content. No files written; these are proposals for human
> approval.

---

### What the main agent does while subagents run

The main agent waits. It does not run extraction inline. When all subagents return their
proposals, the main agent collects them and proceeds to Step 4.

---

## Step 4 — Review + commit

### Consolidate proposals

The main agent receives all proposed pages from the subagents. Before presenting them:

1. **Dedup.** Apply the resolver: if two subagents proposed pages covering the same fact,
   merge them into a single page with the richer content. Exactly one home per fact.
2. **Check MECE.** Verify every proposed page lands in a category agreed at Gate 1. Flag
   any that fell into an unagreed slot.
3. **Check gaps.** Collect all gap entries from subagents into a single
   `inbox/bootstrap-gaps.md` proposal (dedup duplicate gaps).

### Present to user

Show the full proposed starter wiki as a diff — list of proposed new pages with their
first Compiled Truth sentence, and any update proposals for existing pages. Include the
gaps file. Let the user read, edit, or reject individual pages.

Example summary format:

```
Proposed starter wiki (14 pages):

  architecture/
    auth-flow.md       "Auth requests pass through middleware X then reach service Y…"
    data-model.md      "Core entities: Workspace (billing boundary), User, Session…"
  constraints/
    billing-rate-limit.md  "Never call the ledger API above 50 rps…"
  decisions/
    0001-postgres-over-mongo.md  "Chose Postgres for transactional writes; Mongo evaluated…"
  glossary/
    workspace.md       "A Workspace is a billing boundary, not a team boundary…"
  product/
    personas.md        "Primary user: seed-stage founder; secondary: their first hire…"
  inbox/
    bootstrap-gaps.md  "3 gaps: intended deployment model, SLA targets, primary user persona"

Approve all / approve individually / reject: ___
```

### Commit on approval

On user approval (full or partial), write the approved pages to disk, **stamp the ingest
watermark**, then commit:

```bash
# Seeding mined the chat history, so mark it ingested — otherwise the heartbeat will
# nag the entire pre-seed history as "un-ingested". This writes the local cursor AND a
# committed, portable baseline (repo-wiki/.ingest/seed.json) so clones don't re-nag.
python3 skills/repo-wiki/scripts/kb.py watermark --seed

git add repo-wiki/                       # includes the tracked seed.json baseline
git commit -m "feat(repo-wiki): cold-start bootstrap — initial wiki seeded"
```

`kb watermark --seed` is mandatory after any seed that mined chat history: a freshly
seeded wiki should report ~0 un-ingested, and `kb catchup` should list nothing — both
surfaces read the same watermark, so they must agree. Skipping it leaves a false backlog.

Pages not approved remain as proposals in the conversation (not written). The user can
approve them in a follow-up.

---

## Cross-references

| Referenced from | Used for |
|---|---|
| `references/structure.md` | The resolver, MECE discipline, default categories, disambiguation rules — Gate 1 adapts from this |
| `references/extraction.md` | Prompt 1 (chat extraction) — chat subagents run this prompt; also the fan-out / off-main-thread principle |
| `references/claude-md-shim.md` | Migration triage for CLAUDE.md / AGENTS.md and other existing docs — docs subagent generalizes this |
| `references/activation.md` | Heavy-work-off-main-thread principle; parallel subagent and background job patterns the subagent roster follows |
