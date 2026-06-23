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
| Search | ranked FTS5/BM25 (per-wiki index cache); falls back to ripgrep/grep if FTS5 absent |
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

Ranked full-text search across the wiki. Uses **SQLite FTS5 / BM25** (porter
stemmer, title-boosted) via a **per-wiki** index cache at `.ingest/search.db`
(scoped to this repo's pages; gitignored, rebuilt locally by file mtime on each
request, never committed). On interpreters whose
`sqlite3` lacks FTS5 it falls back to a ripgrep (`rg`) / Python-grep content walk.
Query is capped at 200 characters.

```json
{
  "results": [
    {
      "path": "constraints/auth.md",
      "line": 12,
      "snippet": "...matched [text]...",
      "title": "Auth invariants",
      "summary": "Tokens are validated at the edge, never trusted from the client.",
      "score": 2.41
    }
  ]
}
```

`title`, `summary` (the page's Compiled-Truth line), and `score` (higher = better)
are present only on the FTS path; the grep fallback returns just `path`, `line`,
and `snippet`. Empty query returns `{"results": []}`. Query-too-long returns 400.

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

Returns pages that reference `path`. Backlinks match a page's *filename* as a
literal, so this endpoint stays on the ripgrep/Python-grep path (`_search_wiki`)
rather than the FTS index — link-resolution wants exact substring matching, not
stemmed relevance ranking. The page itself is excluded from results.

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

### `POST /api/comment`

Appends an inline comment record to `<wiki>/.comments/comments.jsonl`. Called by the
web viewer when a user submits a selection comment. Request body is JSON:

```json
{
  "page":          "architecture/auth.md",
  "line":          42,
  "end_line":      47,
  "section":       "## Compiled Truth",
  "selected_text": "…the text the user highlighted…",
  "comment":       "This is stale — the token endpoint moved."
}
```

`page` is required and must resolve to a `.md` file inside the wiki (path traversal
rejected). `comment` and `selected_text` are required and non-empty. `line`,
`end_line`, and `section` are optional anchors. Size caps: `comment` ≤ 4000 chars,
`selected_text` ≤ 2000, `section` ≤ 200.

Success response (200):

```json
{
  "id": "193a4f2b-c1d2e3f4",
  "status": "ok"
}
```

The written record also carries `timestamp` (ISO-8601 UTC), `status: "open"`.

Error responses: `{"error": "<message>"}` with 400 (bad input) or 500 (write failure).

Agents consume comments via `kb.py comments list` and resolve them with
`kb.py comments resolve <id> --note "..."`. See `references/comments.md`.

### `GET /api/changed?path=<rel>`

Returns the `mtime` and `size` of a single wiki file without re-fetching content.
Used by the viewer's per-page poll to detect in-place edits (e.g. an agent updating
the `.md` file in response to a comment).

```json
{ "mtime": 1718300123.456, "size": 4096 }
```

`path` is relative to the wiki root. Rejects `..` and absolute paths. Returns 400 if
the file does not exist or is not a `.md` file.

### `GET /api/revision`

Returns the maximum `mtime` across **all** `.md` files in the wiki (recursive). Used
by the viewer's global poll to detect any wiki change — a new page, an edit to any
file — and trigger a sidebar/content refresh.

```json
{ "revision": 1718300200.123 }
```

No parameters. Never errors (returns 0.0 on an empty wiki).

---

## Live auto-refresh

The viewer polls two endpoints to keep the page current without a manual reload:

| Poll | Endpoint | Interval | Action on change |
|---|---|---|---|
| Per-page | `GET /api/changed?path=<rel>` | ~5 s | Re-fetch and re-render the current page |
| Global | `GET /api/revision` | ~10 s | Reload sidebar tree; re-render page if it changed |

This creates the **agent-edits → viewer-updates** loop: when an agent acts on a
comment and rewrites the `.md` file, the viewer picks up the change within ~5 seconds
— the human sees the update without refreshing.

Polling is paused when the browser tab is hidden (via Page Visibility API) and
resumes immediately when the tab becomes active again.

---

## Architecture

```
kb.py cmd_serve()
  └─ http.server.HTTPServer  (stdlib, no external deps)
       ├─ WikiHandler (do_GET)
       │    ├─ /api/tree        → sidebar tree
       │    ├─ /api/page        → page content + frontmatter
       │    ├─ /api/search      → full-text search
       │    ├─ /api/status      → staleness state
       │    ├─ /api/backlinks   → backlink lookup
       │    ├─ /api/changed     → per-file mtime poll
       │    ├─ /api/revision    → global wiki mtime poll
       │    └─ /               → serves assets/web/ (index.html, app.js, style.css, marked.min.js)
       └─ WikiHandler (do_POST)
            └─ /api/comment     → append comment to <wiki>/.comments/comments.jsonl

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
| Write surface | Only `POST /api/comment` writes (appends to `.comments/comments.jsonl`); all other routes are read-only; no delete/update path |
| Query length | Search query capped at 200 characters |

The viewer is intentionally localhost-only and read-only. Do not expose it via a
reverse proxy without authentication.

---

## Deferred: edit support

In-browser editing (create page, edit Compiled Truth, append Timeline entry) is
tracked as a follow-up epic. The current viewer is **mostly read-only** — `POST
/api/comment` is the only write surface (human feedback, not content edits). Content
edits remain the agent's job in-repo under apply-and-report
([[0005-apply-and-report-not-propose]]): write directly, report significant changes,
revert via git — including `canonical` pages.

Comments + live auto-refresh are now shipped. See `references/comments.md` for the
full consumption protocol (hook install, watch-loop, act-then-resolve).
