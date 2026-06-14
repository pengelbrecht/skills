---
type: glossary
source: canonical
covers: []
verified_against: fc77a0e
status: active
---

## Compiled Truth

- **Skill** — a *distributable* package under `skills/<name>/` (installed via `npx skills
  add`). NOT a `.claude/`/`~/.claude/` local config file. The word always means the
  distributable sense in this repo.
- **Shim** — the thin `CLAUDE.md`/`AGENTS.md` left behind after its *knowledge* moves to
  the wiki: an always-on pointer to `repo-wiki/` + a few universal directives.
- **Compiled Truth / Timeline** — the two parts of every wiki page: a mutable current-best
  summary (Compiled Truth) over an append-only evidence log (Timeline).
- **`covers`** — frontmatter globs naming the code a page makes claims about; `kb status`
  flags the page stale when those paths change after its `verified_against` sha.
- **Resolver** — the MECE decision tree in a wiki's root `INDEX.md` that routes each fact
  to exactly one folder.

## Timeline

- 2026-06-14 — seeded during repo-wiki conversion — @fc77a0e
