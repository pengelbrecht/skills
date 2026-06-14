---
type: decision
source: canonical
covers: [skills/repo-wiki/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

The `repo-wiki` skill is built on two principles: **(1) persist only the non-derivable**
(knowledge the code can't regenerate — the why, constraints, decisions, product context;
derivable facts are generated on demand, not stored), and **(2) chat is the primary
intake** (most non-derivable knowledge is tacit and surfaces in conversation, so it's
mined from chats, not just code). Two axes — recoverability and sourcing
(`canonical`/`from-code`/`from-doc`) — drive a per-page freshness model. Pages use a
Compiled-Truth + Timeline shape. Everything is **propose-not-apply**; staleness is a soft
signal, never a commit gate.

**Rejected alternatives:**
- GBrain's full architecture (Postgres + pgvector retrieval, typed entity graph) — too
  heavy for a single repo; `covers` + `ls` + grep suffice. We kept only GBrain's MECE
  resolver idea and the Compiled-Truth/Timeline page shape.
- OKF-style typed entities/relations — over-engineered for one repo.
- Backend/agentwiki sync — files-in-repo stay self-contained.
- Mandatory nested INDEX catalogs — a folder's file list is `ls`'s job and rots; INDEX.md
  carries purpose + convention only.
- LLM-judged freshness — git decides staleness deterministically.

## Timeline

- 2026-06-14 — captured from the design session that built repo-wiki (see docs/ideas/repo-wiki.md) — @fc77a0e
