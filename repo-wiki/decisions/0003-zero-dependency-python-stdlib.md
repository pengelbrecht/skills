---
type: decision
source: canonical
covers: [skills/repo-wiki/scripts/**]
verified_against: fc77a0e
status: active
---

## Compiled Truth

`repo-wiki` is **zero-dependency Python stdlib** — `kb.py`, the web viewer server, and the
vendored recall scripts import only the standard library (incl. `sqlite3` FTS5,
`http.server`, `subprocess`). It runs with bare `python3`; front-end assets are vendored
(no CDN). This is what lets the skill install via `npx skills add` and "just work" with
only a Python 3 interpreter.

The stance *drove* the web-viewer architecture: stdlib `http.server` (not Flask/FastAPI),
client-side render with vendored `marked.js` (not a server-side markdown dependency),
ripgrep via `subprocess` (not a Python search lib). **Reflex was rejected as overkill** —
it pulls in a Node/Next build toolchain and breaks the zero-dep property.

**Escape hatch:** if a skill ever genuinely needs a third-party package, follow the repo
convention — `uv run` + PEP 723 inline script metadata (as `agent-screencast` does) — not
pip/venv. Zero-dep scripts stay on bare `python3`.

## Timeline

- 2026-06-14 — captured from the dependency-management discussion in the repo-wiki session — @fc77a0e
