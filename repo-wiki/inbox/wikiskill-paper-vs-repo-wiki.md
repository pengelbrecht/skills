---
type: note
source: from-doc
from: https://arxiv.org/abs/2608.27454
covers: [skills/repo-wiki/**]
verified_against: faaf70a
status: active
---

## Compiled Truth

The WikiSkill paper (arXiv 2608.27454, "Compiling Agent Experience into Persistent
Knowledge for Skill Evolution") independently validates repo-wiki's core premise —
its ablations show a *persistent* knowledge base is essential for agents to improve
across iterations, and that compiled knowledge transfers across models. Its
architecture parallels repo-wiki closely: `wiki/patterns/` as individual markdown
pages + `index.md` catalog (≈ our pages + INDEX.md), immutable `raw/` traces
(≈ our Timeline provenance), incremental patch-based edits (≈ apply-and-report).

Two ideas repo-wiki lacks and could adopt:

1. **`skill-impact.md` rejection audit trail** — records every proposed change, its
   diff, validation score, and accept/reject outcome, so agents don't re-propose a
   modification that was already rejected. repo-wiki's git-revert safety net has
   this gap: a reverted page can be re-added by the next agent, which sees no record
   of the revert.
2. **Validation-gated skill edits** — a skill modification is accepted only if it
   improves a measured validation score (rollback otherwise). Maps onto
   skill-creator's evals for this monorepo's skills generally.

Conversely, the paper names "no automated wiki pruning" as its limitation — the
staleness problem repo-wiki explicitly solves via `covers` ∩ git diff.

## Timeline

- 2026-08-29 — captured from chat (user asked which parts of arXiv 2608.27454 are
  relevant); paper fetched and compared against skills/repo-wiki/SKILL.md — verified @faaf70a
