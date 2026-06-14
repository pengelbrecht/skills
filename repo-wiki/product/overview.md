---
type: product
source: canonical
covers: []
verified_against: fc77a0e
status: active
---

## Compiled Truth

A monorepo of **distributable Claude Code skills** authored by Peter Engelbrecht. The
audience is *other Claude Code instances/users* who install individual skills via
[skills.sh](https://skills.sh) (`npx skills add pengelbrecht/skills [--skill <name>]`).
Each skill is a self-contained package under `skills/<name>/`. The repo's job is to
author and distribute these skills — not to be an app.

The "why": skills here are **shareable packages**, deliberately *not* `.claude/` /
`~/.claude/` local configuration. That distinction is the organizing principle of the
whole repo (see decision 0001).

## Timeline

- 2026-06-14 — captured from CLAUDE.md + the repo-wiki conversion session — @fc77a0e
