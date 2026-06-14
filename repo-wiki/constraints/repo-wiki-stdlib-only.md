---
type: constraint
source: canonical
covers: [skills/repo-wiki/scripts/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

`repo-wiki` scripts must stay **Python stdlib only** — no third-party imports, no pip, no
node. `subprocess` to `rg`/`grep` is the only permitted external call. Front-end assets are
vendored, never CDN. This is load-bearing for `npx skills add` portability (see decision
0003). If you find yourself reaching for a package, stop — use the `uv run` + PEP 723
escape hatch instead, and only for a script that truly needs it.

## Timeline

- 2026-06-14 — established with decision 0003 — @fc77a0e
