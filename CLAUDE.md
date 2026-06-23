# Skills Repository

A monorepo of **distributable** Claude Code skills (installed via `npx skills add`) — not
`.claude/` local config. See decision 0001 in the wiki for why that distinction matters.

## Knowledge base

This repo's knowledge lives in `repo-wiki/`. **Read `repo-wiki/INDEX.md` first** — it's the
map + filing rules. Don't read the whole wiki; pull pages by relevance (`covers:`
frontmatter, `grep`, descriptive filenames, each page's Compiled-Truth first line).
When you settle a decision or learn a constraint, file it per `repo-wiki/INDEX.md`
(apply directly — git is the review; report significant writes so they can be reverted).
**If knowledge you need isn't in the wiki:** find it (read the code, ask,
or web-search), use it, then add it so the next agent doesn't re-derive it —
when it's durable and non-obvious. Full method: the `repo-wiki` skill (`skills/repo-wiki/`).

Browse it in a browser: `python3 skills/repo-wiki/scripts/kb.py serve`.
