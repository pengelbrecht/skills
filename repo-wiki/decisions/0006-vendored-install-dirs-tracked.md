---
type: decision
source: canonical
covers: [.agents/**, .claude/**]
status: active
---

## Compiled Truth

The `.agents/` and `.claude/` skill **install dirs are committed (tracked) in this
repo**, not gitignored. As of this decision they hold a vendored copy of the installed
`last30days` skill (`.agents/skills/last30days/`, `.claude/skills/last30days/`).

**Why:** owner chose to vendor the installed skill (plus `skills-lock.json`) into the repo
so a local fix to it travels with the repo. `last30days` is *not* one of this repo's
authored source skills (those are `agent-screencast`, `gws-slides`, `missions`, etc. under
the root) — it is an installed third-party skill.

**Tension with [[0001-skills-are-distributable-packages]]:** 0001 says "`.claude/` in this
repo is local-only." That still holds for *authored* skills (developed under `skills/<name>/`,
never copied into `.claude/`). 0006 is the narrow exception: install dirs may be tracked when
deliberately vendoring an *installed* skill.

**Consequence / gotcha:** a fix applied inside a vendored install dir can be **overwritten by
a future `npx skills add` / reinstall**. To persist such a fix, send it upstream to the
skill author too — tracking it here only preserves the current snapshot.

## Timeline

- 2026-06-27 — owner elected to commit `.agents/`+`.claude/`+`skills-lock.json` (81 files)
  rather than gitignore them, carrying a `last30days` SKILL.md script-path fix (hard-coded
  `~/.claude/skills/...` → resolve across `~/.claude` and `~/.agents` install roots).
