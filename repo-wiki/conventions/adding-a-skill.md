---
type: convention
source: canonical
covers: [skills/**, README.md]
verified_against: fc77a0e
status: active
---

## Compiled Truth

To add a skill:
1. Create `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`).
2. Add supporting files in the same dir (`references/`, `scripts/`, `assets/`, `samples/`,
   optional `pyproject.toml`/`Makefile`). Keep it self-contained — no cross-skill imports.
3. Add a row to the skills table in `README.md`.

Optionally run `/skill-creator` to scaffold and iterate (test prompts + description
optimization for triggering).

## Timeline

- 2026-06-14 — migrated from CLAUDE.md "Adding a new skill" — @fc77a0e
