---
type: architecture
source: canonical
covers: [skills/**, README.md]
verified_against: fc77a0e
status: active
---

## Compiled Truth

Each skill lives in `skills/<name>/` with a `SKILL.md` at its root (YAML frontmatter:
`name`, `description` — the description is the skill's trigger). Supporting files sit
alongside: `references/` (docs loaded on demand), `scripts/` (executable code),
`assets/` (templates/output), `samples/`, optional `pyproject.toml`/`Makefile`. The
layout is what makes `npx skills add pengelbrecht/skills` work.

**Mental model:** each `skills/<name>/` is an *independently installable package*, not
part of a shared app — no cross-skill imports; a skill must stand alone when copied
elsewhere. `README.md` holds the canonical skills table.

The current list of skills is **derivable** — read `skills/*/SKILL.md` or the README
table; it is deliberately not duplicated here (a hand-maintained list rots).

## Timeline

- 2026-06-14 — captured from CLAUDE.md structure section — @fc77a0e
