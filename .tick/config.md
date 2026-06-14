# Ticks runner config — skills monorepo

## Testing

There is **no test framework** in this repo; skills are verified with smoke checks.
For the repo-wiki web viewer, verify behavior with the running server + `curl`:

```bash
# boot (background) and probe
python3 skills/repo-wiki/scripts/kb.py serve --port 8347 &
SRV=$!; sleep 1
curl -fsS "http://localhost:8347/api/tree"            | head        # JSON, 200
curl -fsS "http://localhost:8347/api/page?path=INDEX.md" | head      # JSON w/ markdown + frontmatter
curl -fsS "http://localhost:8347/api/search?q=billing" | head       # JSON matches
curl -s -o /dev/null -w '%{http_code}' \
  "http://localhost:8347/api/page?path=../../../../etc/passwd"       # MUST be 403/400 (path sandbox)
kill $SRV
```

Each tick's acceptance is the concrete endpoint/behavior it adds, checkable this way.
Run `python3 -m py_compile skills/repo-wiki/scripts/kb.py` after editing the CLI.

## Environment

Pre-flight (orchestrator verifies once):
```bash
which python3                         # required
which rg || which grep                # ripgrep preferred; grep is the fallback
```

## Rules

- **Zero new dependencies.** Server is Python **stdlib only** (`http.server`, `json`,
  `subprocess`, `pathlib`). No pip, no node_modules. Front-end assets are **vendored**
  under `skills/repo-wiki/assets/web/` (e.g. `marked.min.js`, pinned + provenance) —
  no CDN.
- **Bind to localhost only.** This is a local viewer, never exposed.
- **Sandbox to `repo-wiki/`.** Every path param must resolve inside the wiki dir;
  reject traversal (`..`, absolute paths) with 400/403.
- **Read-only in this epic.** No write/edit endpoints yet (separate follow-up epic).
- Reuse existing `kb.py` internals (`compute_status`/status cache, `load_pages`,
  `parse_frontmatter`, `compiled_truth_first_line`) — don't duplicate logic.
- Keep it one small server file + one small client (`app.js`) + one `style.css`;
  serialize ticks that touch these shared files (they will conflict in parallel).
