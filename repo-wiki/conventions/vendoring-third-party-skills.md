---
type: convention
source: canonical
covers: [skills/*/PROVENANCE.md]
status: active
---

## Compiled Truth

A third-party skill can be vendored into the distributable library as
`skills/<name>/`: copy the upstream files unmodified, copy the upstream `LICENSE`
alongside them (required for MIT and similar), and add `PROVENANCE.md` with the
upstream URL, author, license, pinned commit, vend date, and a "Local changes"
section. Add a README row that says it is vendored and links upstream. Only vendor
skills whose license permits redistribution. Distinct from [[0006-vendored-install-dirs-tracked]],
which covers *installed* copies under `.agents/`/`.claude/`.

## Timeline

- 2026-10-26 — established when vendoring `be-ambitious` from DannyMac180/skills @7dc63b7
