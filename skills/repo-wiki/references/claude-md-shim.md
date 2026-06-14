# CLAUDE.md / AGENTS.md → thin shim

The agent-instruction file is a junk drawer mixing two unrelated jobs:

- **Directives** (imperative — *do this*): "use pnpm," "never commit secrets," "run
  typecheck before commit."
- **Knowledge** (declarative — *this is true*): the why, mental models, constraints,
  glossary, product context.

Its defining mechanic is that it is **always-on, fully disclosed, every session** — a
feature for a handful of universal directives, a tax for everything else. The wiki is
the opposite: **gradual disclosure**, specifics paged in only when relevant. So
repo-wiki **absorbs the knowledge** and the file shrinks to a thin **shim**.

## What the shim is

Two ingredients, ~12 lines total:

1. A **minimal always-on pointer** — "knowledge lives in `repo-wiki/`; read `INDEX.md`
   first; pull pages by relevance; full method = the `repo-wiki` skill." This is the
   "how to use the wiki" instruction, kept tiny because it pays full token freight every
   session. The *manual itself* lives in `repo-wiki/INDEX.md` and this skill — the shim
   only points.
2. The few **universal / safety-critical directives** that must stay resident (can't
   risk non-load behind gradual disclosure).

See `assets/templates/shim.md` for the exact text.

## The routing rule

| Content | Lands in |
|---|---|
| Universal, always-relevant, safety-critical **directive** | the shim |
| Code-scoped knowledge (constraint, gotcha) | wiki `constraints/` + `covers:` |
| General knowledge (why, mental model, term) | wiki `decisions/` `architecture/` `glossary/` |
| Functional requirement | wiki `product/` |
| Non-functional requirement (perf/security/compliance) | wiki `constraints/` |

The test: **relevant *always* → shim; relevant only when touching specific code → wiki
(scoped by `covers`).**

## Three-tier disclosure

```
shim (CLAUDE.md/AGENTS.md)   ← always-on pointer + safety directives  (tier 1, tiny)
   │ points to
repo-wiki/INDEX.md           ← the manual: organization, resolver, page shape  (tier 2)
   │
page bodies                  ← paged in on demand, covers-scoped  (tier 3)
```

The shim emphasizes **reading** (grounding), with two lightweight write nudges — because
the heavy capture is *mechanical* (the `catchup` triage mines sessions regardless):

1. "File new decisions/constraints per `INDEX.md` (propose-only)."
2. **Write-back on a cache miss.** If the agent needs knowledge the wiki lacks, it should
   resolve it (read the code / ask the user / web-search) and then *propose* a page so the
   next agent doesn't re-derive it. This makes the wiki a write-back cache that grows from
   everyday use, not just from chats. The same recoverability filter applies — only
   durable, non-obvious knowledge is captured; trivia that's cheap to re-derive stays out.
   Source priority matters: read the code for *how* (→ `from-code`), **ask the user** for
   *why/intent/constraints* rather than guessing (→ `canonical`), web-search for external
   facts (→ `from-doc`). Full protocol in the root `INDEX.md`.

## Migrating an existing file

Same triage primitive as chat-capture, run over a file instead of a conversation:

1. Walk `CLAUDE.md`/`AGENTS.md` section by section.
2. Classify each: directive (stays) vs knowledge (moves).
3. Route knowledge into the MECE folders via the resolver; stamp `covers` where
   code-scoped.
4. Replace the migrated bulk with the shim (`assets/templates/shim.md`).
5. **Propose the whole thing as a diff** — the human approves; nothing auto-applies.

`kb.py init` offers to do this when it detects an existing instruction file.

## Multi-tool consequence

The wiki is the single canonical, tool-agnostic source. `CLAUDE.md`, `AGENTS.md`,
`GEMINI.md` all collapse into near-identical thin shims pointing at it — killing the
per-tool instruction-file duplication. Adding or switching an agent tool costs one
shim, not a re-authoring. **Shim-lint** at session start flags re-accreted knowledge so
the file can't quietly become a drawer again.
