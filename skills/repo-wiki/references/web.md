# web.md — `kb serve` local web viewer

Reference for the built-in read-only browser UI shipped with `kb serve`.

---

## Running

```bash
# From the repo root (auto-detects repo-wiki/ in cwd or parent)
python3 scripts/kb.py serve

# With options
python3 scripts/kb.py serve --port 8080 --wiki path/to/repo-wiki
```

Binds to `127.0.0.1:<port>` (default 7654). Open `http://127.0.0.1:7654/` in any
browser. No network access, no install, no build step.

---

## What the viewer shows

| Feature | Detail |
|---|---|
| Sidebar tree | Folders + pages; stale/fresh/unverified pill per page |
| Page render | Frontmatter table, Compiled Truth + Timeline rendered via vendored marked |
| In-page TOC | Right-rail sticky; hides at narrow widths (< 900px) |
| Search | ripgrep-backed; falls back to Python grep if rg absent |
| Staleness pills | fresh (green) / stale (amber) / unverified (grey) |
| Covers chips | `covers:` globs from frontmatter, shown below page title |
| Backlinks | Pages that link to the current page |

---

## API routes

All routes are GET-only. The client (app.js) calls these; they are also curl-friendly.

### `GET /api/tree`

Returns the full sidebar tree.

```json
{
  "folders": [
    {
      "name": "architecture",
      "pages": [
        { "path": "architecture/index.md", "title": "Architecture" }
      ]
    }
  ],
  "loose": [
    { "path": "INDEX.md", "title": "INDEX" }
  ]
}
```

### `GET /api/page?path=<rel>`

Returns the content and frontmatter of a single page. `path` is relative to the
wiki root (e.g. `architecture/index.md`). Rejects `..` and absolute paths.

```json
{
  "path": "architecture/index.md",
  "frontmatter": {
    "type": "architecture",
    "source": "canonical",
    "covers": ["src/**"],
    "verified_against": "a1b2c3d",
    "status": "active"
  },
  "markdown": "## Compiled Truth\n..."
}
```

Error responses use `{"error": "<message>"}` with appropriate HTTP status codes
(400 bad request, 403 path-outside-wiki, 404 not found, 500 server error).

### `GET /api/search?q=<query>`

Full-text search across the wiki. Uses ripgrep (`rg`) if available, otherwise falls
back to a Python `re.search` walk. Query is capped at 200 characters.

```json
{
  "results": [
    {
      "path": "constraints/auth.md",
      "line": 12,
      "snippet": "...matched text..."
    }
  ]
}
```

Empty query returns `{"results": []}`. Query-too-long returns 400.

### `GET /api/status`

Returns the staleness state for all wiki pages that carry `covers:` frontmatter,
computed from git. If the wiki is not inside a git repo, all pages are returned as
unverified.

```json
{
  "stale": {
    "architecture/auth.md": {
      "action": "review",
      "source": "canonical",
      "changed": ["src/auth/middleware.py"]
    }
  },
  "unverified": ["inbox/note.md"]
}
```

### `GET /api/backlinks?path=<rel>`

Returns pages that reference `path`. Uses the same search backend as `/api/search`
(ripgrep or Python grep). The page itself is excluded from results.

```json
{
  "backlinks": [
    {
      "path": "decisions/0001-auth-strategy.md",
      "line": 7,
      "snippet": "...see constraints/auth.md..."
    }
  ]
}
```

---

## Architecture

```
kb.py cmd_serve()
  └─ http.server.HTTPServer  (stdlib, no external deps)
       └─ WikiHandler (do_GET)
            ├─ /api/*        → Python handlers (tree, page, search, status, backlinks)
            └─ /             → serves assets/web/index.html
               /app.js       → assets/web/app.js
               /style.css    → assets/web/style.css
               /marked.min.js → assets/web/marked.min.js  (vendored)

assets/web/
  index.html      — shell (sidebar + content pane)
  app.js          — fetch /api/* → render; marked for markdown; no framework
  style.css       — clean-docs tokens; dark mode via prefers-color-scheme
  marked.min.js   — vendored (see PROVENANCE.md); markdown → HTML, client-side
  PROVENANCE.md   — asset provenance record
```

The server is single-threaded (stdlib default). All markdown rendering is
client-side via vendored marked — the server sends raw markdown; the browser renders
it. This keeps the server trivial and avoids a Python markdown dependency.

A background daemon thread runs a staleness reconcile on startup so the first
`/api/status` call can return a cached result without blocking.

---

## Security posture

| Concern | Mitigation |
|---|---|
| Network exposure | Binds to `127.0.0.1` only — never `0.0.0.0` |
| Path traversal | `/api/page` and `/api/backlinks` reject `..` segments and absolute paths; `Path.resolve().relative_to(wiki)` sandbox enforced |
| Shell injection | Search uses `subprocess` with a list (not a string); `shell=False` is the default |
| Read-only | No POST/PUT/DELETE routes; no write path exists |
| Query length | Search query capped at 200 characters |

The viewer is intentionally localhost-only and read-only. Do not expose it via a
reverse proxy without authentication.

---

## Deferred: edit support

In-browser editing (create page, edit Compiled Truth, append Timeline entry) is
tracked as a follow-up epic. The current viewer is **read-only by design** — the
propose-not-apply discipline that keeps `canonical` pages trustworthy applies here
too. Any edit path must gate `canonical` rewrites on human confirmation.
