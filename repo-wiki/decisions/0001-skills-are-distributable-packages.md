---
type: decision
source: canonical
covers: [skills/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

Skills are authored as **distributable packages** under `skills/<name>/`, designed for
`npx skills add` — deliberately *not* as `.claude/`/`~/.claude/` local configuration.

**Why:** the goal is to share skills with other Claude Code instances/users. Local
`.claude/` config can't be distributed via skills.sh and is machine-scoped. Keeping each
skill self-contained under `skills/` is what makes it installable elsewhere.

**Consequence:** no cross-skill imports; each skill must work standalone when copied;
`.claude/` in this repo is local-only (e.g. the repo-wiki SessionStart hook references the
in-repo skill path, so the repo is self-hosting without copying anything into `.claude/`).

## Timeline

- 2026-06-14 — migrated from the CLAUDE.md "Note" (the distributable-vs-local distinction) — @fc77a0e
