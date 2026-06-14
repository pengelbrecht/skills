# repo-wiki

The knowledge base for this repository. **Agent-first, propose-not-apply.**
Read this file first, then pull pages by relevance — don't read the whole tree.

## How to use this wiki

- **Find knowledge:** `ls` a folder, read descriptive filenames, match `covers:`
  frontmatter against the files you're touching, skim each page's **Compiled Truth**
  (the first lines). Session start injects the pages relevant to your working set.
- **Add knowledge:** pick the folder with the resolver below, use the page shape
  (Compiled Truth + Timeline), stamp `covers:` if code is involved, and **propose the
  diff** — never silently apply. Decisions are append-only; supersede, don't edit.
- **Freshness:** `kb status` flags pages whose `covers` paths changed since their
  `verified_against` sha. Stale is a *signal*, not a gate.

## When knowledge is missing (cache miss → fill it)

If you need project knowledge the wiki doesn't have, don't just work around it — fill the
gap so the next agent doesn't pay the same cost:

1. **Resolve it from the most authoritative source:**
   - *how something works* → **read the code** (then it's `from-code`),
   - *why / intent / a constraint / product context* → **ask the user** — do **not**
     guess non-derivable truth (then it's `canonical`),
   - *external library / standard / API* → **web search** (then it's `from-doc` with a
     `from:` URL).
2. **Use it** for your task.
3. If it's **durable and non-obvious** — it would help the next agent and isn't cheap to
   re-derive — **propose** a wiki page for it: route via the resolver, stamp `covers`, set
   `source` per above, dedup against existing pages first. **Skip trivia** you could
   re-derive in seconds (that stays out of the wiki by design).

This makes the wiki a write-back cache: every genuine gap becomes a one-time fill.

## What goes where — the resolver

1. user / why-it-exists / what-to-build → `product/`
2. meaning of a term → `glossary/`
3. how the system *is built / works* → `architecture/`
4. a rule / limit that must hold → `constraints/`
5. why a *past choice* was made → `decisions/`
6. how to run / deploy / recover → `operations/`
7. where it's heading / in flight → `roadmap/`
8. how *we* develop → `conventions/`
9. unsure → `inbox/`  ·  dead → `archive/`

Disambiguation: descriptive "how it works" → architecture, prescriptive "what must
hold" → constraints; forward-looking rule → constraints, past choice+why → decisions;
non-functional req → constraints, functional req → product.

## Page shape

```markdown
---
type: constraint
source: canonical          # canonical | from-code | from-doc
covers: [src/area/**]
verified_against: <sha>
status: active
---
## Compiled Truth
<current best understanding — terse, claim-first>
## Timeline
- <date> — <evidence / source> — verified @<sha>
```

## Wiki comments — feedback channel

The wiki viewer lets users highlight text and leave comments. These are a
**human-in-the-loop feedback channel** for agents: if the `UserPromptSubmit` hook
injects a `PENDING WIKI COMMENTS` block, act on each comment (edit the page, file to
`inbox/`, or reply) and resolve it with `kb.py comments resolve <id> --note "..."`.
Full protocol: `repo-wiki/references/comments.md`.

## Conventions in this wiki

<!-- Record any repo-specific deviations from the recommended structure here, so the
     wiki stays self-documenting. e.g. "decisions live in docs/adrs/, synthesized here." -->
