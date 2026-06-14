---
type: decision
source: canonical
covers: [skills/repo-wiki/scripts/vendor/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

The chat-enumeration engine (`recall.py` list-mode + `read_session.py`) is **vendored** into
`skills/repo-wiki/scripts/vendor/recall/` rather than referenced as a separate skill, so
`repo-wiki` has **no skill dependencies**. The vendored scripts are pure stdlib and
multi-agent (Claude Code / Codex / pi), making the wiki's chat intake agent-agnostic.

**Why:** a distributable skill must be self-contained — depending on the `recall` skill
being installed would break clean `npx skills add`. Upstream is the user's own `recall`
skill, so re-syncing is a `cp` (version pinned in `vendor/recall/PROVENANCE.md`).

**Rejected:** declaring `recall` as a runtime dependency / soft auto-detect — adds an
install-order coupling for no benefit at vendoring's low cost (two small files).

## Timeline

- 2026-06-14 — captured from the "absorb the scripts, no skill deps" decision — @fc77a0e
