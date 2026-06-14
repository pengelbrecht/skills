---
type: constraint
source: canonical
covers: [skills/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

Every skill must have a `skills/<name>/SKILL.md` with YAML frontmatter containing at least
`name` and `description` — required by skills.sh, and the `description` is the skill's
trigger (make it specific/"pushy" so it fires when relevant). A skill directory without a
valid `SKILL.md` won't install or trigger.

## Timeline

- 2026-06-14 — migrated from CLAUDE.md "Adding a new skill" — @fc77a0e
