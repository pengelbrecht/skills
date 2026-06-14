#!/usr/bin/env python3
"""
kb.py — repo-wiki command line.

Deterministic, dependency-free (Python 3 stdlib + git + the vendored recall scripts).
Git decides staleness; the model only ever writes/proposes content. Nothing here
auto-applies edits to your knowledge base — these commands report and scaffold.

Subcommands:
  init           Scaffold repo-wiki/, install the SessionStart hook, gitignore the
                 watermark, and detect CLAUDE.md/AGENTS.md for migration.
  status         Report pages whose `covers` paths changed since `verified_against`
                 (soft signal — never a gate).
  catchup        Enumerate chat sessions since the watermark (via vendored recall) so
                 they can be triaged into the wiki.
  watermark      Show / advance the local ingest watermark.
  session-start  Compact heartbeat block for the SessionStart hook (best-effort).
  serve          Boot a local HTTP server (127.0.0.1) with /api/tree and the web UI.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "assets" / "templates"
RECALL = HERE / "vendor" / "recall" / "recall.py"

CATEGORIES = [
    ("product", "PROBLEM — who it's for, why it exists, requirements, non-goals, metrics"),
    ("glossary", "LANGUAGE — the ubiquitous language; what our domain terms mean"),
    ("architecture", "SOLUTION — how the system is built/works; from-code traversal caches"),
    ("constraints", "RULES — invariants, NFRs, gotchas. What must stay true. (NFRs here; functional reqs → product/.)"),
    ("decisions", "RATIONALE — choices + rejected alternatives. NNNN-slug.md, append-only."),
]
SCAFFOLD_ONLY = ["inbox", "archive"]


# ── git helpers ──────────────────────────────────────────────────────────────
def git(*args, cwd=None):
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
        )
        return out.stdout.strip(), out.returncode
    except FileNotFoundError:
        return "", 1


def repo_root():
    out, code = git("rev-parse", "--show-toplevel")
    if code != 0 or not out:
        sys.exit("not inside a git repository (repo-wiki needs git as the source of truth)")
    return Path(out)


def head_sha(root):
    out, _ = git("rev-parse", "--short", "HEAD", cwd=root)
    return out


def changed_paths_since(sha, root):
    if not sha:
        return None  # unknown baseline
    out, code = git("diff", "--name-only", f"{sha}", "HEAD", cwd=root)
    if code != 0:
        return None
    return [p for p in out.splitlines() if p.strip()]


# ── frontmatter + glob ───────────────────────────────────────────────────────
def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end].strip("\n").splitlines()
    fm, i = {}, 0
    while i < len(block):
        line = block[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":  # maybe a block list follows
            items, j = [], i + 1
            while j < len(block) and re.match(r"^\s*-\s+", block[j]):
                items.append(re.sub(r"^\s*-\s+", "", block[j]).strip())
                j += 1
            fm[key] = items if items else ""
            i = j
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
        else:
            fm[key] = val.strip("'\"")
        i += 1
    return fm


def compiled_truth_first_line(text):
    m = re.search(r"^##\s+Compiled Truth\s*$", text, re.M)
    body = text[m.end():] if m else text
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("---"):
            return s
    return ""


def glob_to_regex(pat):
    esc = re.escape(pat)
    esc = esc.replace(r"\*\*", ".*").replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
    return "^" + esc + "$"


def matches_any(path, patterns):
    return any(re.match(glob_to_regex(p), path) for p in patterns if p)


# ── pages ────────────────────────────────────────────────────────────────────
def iter_pages(wiki):
    for p in sorted(wiki.rglob("*.md")):
        name = p.name
        if name == "INDEX.md" or "/.ingest/" in str(p):
            continue
        yield p


def load_pages(wiki):
    pages = []
    for p in iter_pages(wiki):
        try:
            fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            fm = {}
        pages.append((p, fm))
    return pages


# ── commands ─────────────────────────────────────────────────────────────────
def compute_status(root, wiki, pages):
    stale, unverified, fresh = [], [], 0
    for p, fm in pages:
        if fm.get("status") == "archived":
            continue
        covers = fm.get("covers") or []
        if isinstance(covers, str):
            covers = [covers] if covers else []
        va = fm.get("verified_against") or ""
        rel = str(p.relative_to(wiki))
        if not covers or not va:
            unverified.append(rel)
            continue
        changed = changed_paths_since(va, root)
        if changed is None:
            unverified.append(rel)
            continue
        hit = [c for c in changed if matches_any(c, covers)]
        if hit:
            action = "re-synthesize" if fm.get("source") == "from-code" else "review"
            stale.append({"page": rel, "source": fm.get("source", "canonical"),
                          "action": action, "changed": hit[:3]})
        else:
            fresh += 1
    return {"pages": len(pages), "fresh": fresh, "stale": stale, "unverified": unverified}


def cmd_status(args):
    root = repo_root()
    wiki = root / "repo-wiki"
    if not wiki.exists():
        sys.exit("no repo-wiki/ here — run `kb.py init` first")
    st = compute_status(root, wiki, load_pages(wiki))
    print(f"repo-wiki status — {st['pages']} pages, {st['fresh']} fresh, "
          f"{len(st['stale'])} stale, {len(st['unverified'])} unverified\n")
    if st["stale"]:
        print("STALE (soft signal — review, do not gate commits):")
        for s in st["stale"]:
            print(f"  • {s['page']}  [{s['source']}] → {s['action']}")
            for h in s["changed"]:
                print(f"        ↳ changed: {h}")
    if st["unverified"] and args.verbose:
        print("\nUNVERIFIED (no covers/verified_against, or unknown baseline):")
        for rel in st["unverified"]:
            print(f"  • {rel}")
    return 1 if st["stale"] else 0


def cmd_outline(args):
    """Emit the current wiki structure for context: resolver + manual, folder purposes,
    and existing pages with their Compiled-Truth first line. Load this BEFORE extracting
    so routing and dedup use the actual wiki (incl. repo-specific deviations), not the
    generic defaults."""
    root = repo_root()
    wiki = root / "repo-wiki"
    if not wiki.exists():
        sys.exit("no repo-wiki/ here — run `kb.py init` first")
    ri = wiki / "INDEX.md"
    print("=== repo-wiki/INDEX.md (resolver + manual; honor any repo-specific deviations) ===")
    if ri.exists():
        print(ri.read_text(encoding="utf-8").rstrip())
    print("\n=== folders (purpose) ===")
    for d in sorted(p for p in wiki.iterdir() if p.is_dir() and not p.name.startswith(".")):
        purpose = ""
        idx = d / "INDEX.md"
        if idx.exists():
            for line in idx.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    purpose = s
                    break
        print(f"  {d.name}/ — {purpose}")
    print("\n=== existing pages (path — Compiled-Truth first line) — dedup against these ===")
    pages = load_pages(wiki)
    if not pages:
        print("  (none yet)")
    for p, fm in pages:
        rel = p.relative_to(wiki)
        try:
            ct = compiled_truth_first_line(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            ct = ""
        cov = fm.get("covers") or []
        cov = (" [covers: " + ",".join(cov) + "]") if isinstance(cov, list) and cov else ""
        print(f"  {rel} — {ct}{cov}")
    return 0


def cmd_catchup(args):
    root = repo_root()
    wm = load_watermark(root)
    print(f"ingest watermark: chat_session_id={wm.get('chat_session_id') or '(none)'} "
          f"git_sha={wm.get('git_sha') or '(none)'}\n")
    if not RECALL.exists():
        sys.exit(f"vendored recall not found at {RECALL}")
    print(f"enumerating sessions for this project (last {args.days} days)…\n")
    proc = subprocess.run(
        [sys.executable, str(RECALL), "--project", str(root), "--days", str(args.days)],
        capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
    print(
        "\nNext: triage sessions newer than the watermark. Read one with:\n"
        f"  python3 {RECALL.parent / 'read_session.py'} <File-path-from-above>\n"
        "Then file durable knowledge into repo-wiki/ (propose-only), and advance:\n"
        "  python3 kb.py watermark --set-session <newest-session-id> --set-sha <HEAD-sha>"
    )
    return 0


def cmd_watermark(args):
    root = repo_root()
    wm = load_watermark(root)
    if args.set_session or args.set_sha:
        if args.set_session:
            wm["chat_session_id"] = args.set_session
        wm["git_sha"] = args.set_sha or head_sha(root)
        wm["ts"] = datetime.now(timezone.utc).isoformat()
        save_watermark(root, wm)
        print("watermark advanced:")
    print(json.dumps(wm, indent=2))
    return 0


def cmd_session_start(args):
    """Blocking heartbeat — MUST stay fast (output is injected into context, so it gates
    session start). Does NO git scan: it counts pages (cheap fs walk), reports the LAST
    cached status, and spawns a detached `reconcile` to refresh the cache for next time.
    Never raises."""
    try:
        root = repo_root()
        wiki = root / "repo-wiki"
        if not wiki.exists():
            return 0
        n = sum(1 for _ in iter_pages(wiki))  # cheap: filesystem only, no git
        print("\n[repo-wiki] Knowledge base present. Read repo-wiki/INDEX.md first; "
              f"pull pages by relevance (covers/grep). {n} pages.")
        cache = load_status_cache(root)
        if cache:
            ns = len(cache.get("stale", []))
            print(f"[repo-wiki] As of {cache.get('ts', '?')[:19]}: {ns} stale"
                  f"{' — run `kb.py status` to review' if ns else ''}.")
        else:
            print("[repo-wiki] (freshness scan running in background; check `kb.py status`).")
        # Refresh the cache without blocking this session.
        spawn_background(["reconcile"], cwd=root)
    except Exception:
        pass
    return 0


def cmd_reconcile(args):
    """Heavy scan — meant to run detached / in the background. Computes git staleness over
    every page and writes the cache the fast `session-start` reads. Safe to run anytime."""
    root = repo_root()
    wiki = root / "repo-wiki"
    if not wiki.exists():
        return 0
    st = compute_status(root, wiki, load_pages(wiki))
    st["ts"] = datetime.now(timezone.utc).isoformat()
    save_status_cache(root, st)
    if args.verbose:
        print(f"reconciled: {len(st['stale'])} stale, {st['fresh']} fresh")
    return 0


def status_cache_path(root):
    return root / "repo-wiki" / ".ingest" / "status.json"


def load_status_cache(root):
    p = status_cache_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def save_status_cache(root, st):
    p = status_cache_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")


def spawn_background(argv, cwd):
    """Fire-and-forget a detached `kb.py <argv>`. Never blocks; swallows failures."""
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), *argv],
            cwd=str(cwd), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def cmd_init(args):
    root = repo_root()
    wiki = root / "repo-wiki"
    created = []
    wiki.mkdir(exist_ok=True)

    root_index = wiki / "INDEX.md"
    if not root_index.exists():
        root_index.write_text(read_template("INDEX.root.md"), encoding="utf-8")
        created.append("repo-wiki/INDEX.md")

    folder_tmpl = read_template("INDEX.folder.md")
    for name, purpose in CATEGORIES:
        d = wiki / name
        d.mkdir(exist_ok=True)
        idx = d / "INDEX.md"
        if not idx.exists():
            body = folder_tmpl.replace("<folder>", name)
            body = f"# {name}/\n\n{purpose}\n\nOrganized: <set the local convention as a rule>.\n"
            idx.write_text(body, encoding="utf-8")
            created.append(f"repo-wiki/{name}/INDEX.md")
    for name in SCAFFOLD_ONLY:
        (wiki / name).mkdir(exist_ok=True)
        keep = wiki / name / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    # local ingest watermark (gitignored)
    ingest = wiki / ".ingest"
    ingest.mkdir(exist_ok=True)
    ensure_gitignore(root, ["repo-wiki/.ingest/"])

    # SessionStart hook
    installed = install_hook(root)

    # detect instruction files
    shims = [f for f in ("CLAUDE.md", "AGENTS.md", "GEMINI.md") if (root / f).exists()]

    print("repo-wiki initialized.\n")
    if created:
        print("created:")
        for c in created:
            print(f"  + {c}")
    print(f"\nSessionStart hook: {'installed in .claude/settings.json' if installed else 'already present / skipped'}")
    print("ingest watermark: repo-wiki/.ingest/ (gitignored)")
    if shims:
        print(f"\nFound {', '.join(shims)} — consider migrating its *knowledge* into the wiki")
        print("and leaving a thin shim (see references/claude-md-shim.md +")
        print("assets/templates/shim.md). This is propose-only; review the diff.")
    print("\nNext: read references/structure.md, then seed product/, a couple of")
    print("constraints/, and any decisions you already know. Keep it small and real.")
    return 0


# ── state + scaffolding helpers ──────────────────────────────────────────────
def watermark_path(root):
    return root / "repo-wiki" / ".ingest" / "state.json"


def load_watermark(root):
    p = watermark_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def save_watermark(root, wm):
    p = watermark_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(wm, indent=2) + "\n", encoding="utf-8")


def read_template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def ensure_gitignore(root, entries):
    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    add = [e for e in entries if e not in existing]
    if add:
        with gi.open("a", encoding="utf-8") as f:
            if existing and existing[-1].strip():
                f.write("\n")
            f.write("# repo-wiki local ingest state\n")
            for e in add:
                f.write(e + "\n")


def install_hook(root):
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
        except Exception:
            data = {}
    hooks = data.setdefault("hooks", {})
    ss = hooks.setdefault("SessionStart", [])
    cmd = 'python3 "$CLAUDE_PROJECT_DIR/skills/repo-wiki/scripts/kb.py" session-start 2>/dev/null || true'
    blob = json.dumps(ss)
    if "repo-wiki/scripts/kb.py" in blob:
        return False
    ss.append({
        "matcher": "startup",
        "hooks": [{"type": "command", "command": cmd}],
    })
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


# ── web server ───────────────────────────────────────────────────────────────

WEB_ASSETS = HERE.parent / "assets" / "web"

_MIME = {
    ".html": "text/html; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md":   "text/plain; charset=utf-8",
}

# Static routes: URL path → filename under assets/web/
_STATIC = {
    "/":            "index.html",
    "/app.js":      "app.js",
    "/style.css":   "style.css",
    "/marked.min.js": "marked.min.js",
}


def _folder_purpose(folder_dir):
    """Return first non-heading, non-blank line from the folder's INDEX.md."""
    idx = folder_dir / "INDEX.md"
    if not idx.exists():
        return ""
    for line in idx.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return ""


def _build_tree(wiki):
    """Build the /api/tree payload from the wiki directory."""
    folders = []
    for d in sorted(p for p in wiki.iterdir() if p.is_dir() and not p.name.startswith(".")):
        folders.append({
            "name": d.name,
            "purpose": _folder_purpose(d),
        })

    pages = []
    for p in iter_pages(wiki):
        rel = str(p.relative_to(wiki))
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            summary = compiled_truth_first_line(text)
        except Exception:
            summary = ""
        pages.append({
            "path": rel,
            "summary": summary,
        })

    return {"folders": folders, "pages": pages}


def _make_handler(wiki):
    """Return a BaseHTTPRequestHandler class closed over wiki path."""
    import http.server

    class WikiHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # noqa: N802
            sys.stderr.write(f"[serve] {self.address_string()} {fmt % args}\n")

        def send_json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_static(self, asset_path):
            suffix = asset_path.suffix
            mime = _MIME.get(suffix, "application/octet-stream")
            try:
                data = asset_path.read_bytes()
            except OSError:
                self.send_error(404, "Not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            from urllib.parse import urlparse
            parsed = urlparse(self.path)
            path = parsed.path

            # /api/tree
            if path == "/api/tree":
                try:
                    data = _build_tree(wiki)
                    self.send_json(data)
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # static assets
            if path in _STATIC:
                self.send_static(WEB_ASSETS / _STATIC[path])
                return

            self.send_error(404, "Not found")

    return WikiHandler


def cmd_serve(args):
    import http.server

    # Resolve wiki directory
    if args.wiki:
        wiki = Path(args.wiki).resolve()
    else:
        try:
            root = repo_root()
        except SystemExit:
            sys.exit("not inside a git repo and --wiki not specified")
        wiki = root / "repo-wiki"

    if not wiki.exists():
        sys.exit(f"wiki directory does not exist: {wiki}\n"
                 "Run `kb.py init` first, or pass --wiki <path>.")

    handler_cls = _make_handler(wiki)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler_cls)

    print(f"repo-wiki serving on http://127.0.0.1:{args.port}")
    print(f"  wiki : {wiki}")
    print(f"  Press Ctrl-C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        server.server_close()
    return 0


def main():
    ap = argparse.ArgumentParser(prog="kb.py", description="repo-wiki command line")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="scaffold the wiki + install the hook")

    sp = sub.add_parser("status", help="report stale pages (soft signal)")
    sp.add_argument("-v", "--verbose", action="store_true", help="also list unverified pages")

    sub.add_parser("outline", help="emit wiki structure for context (load before extracting)")

    cp = sub.add_parser("catchup", help="enumerate chat sessions since the watermark")
    cp.add_argument("--days", type=int, default=30, help="look-back window (default 30)")

    wp = sub.add_parser("watermark", help="show / advance the ingest watermark")
    wp.add_argument("--set-session", help="advance the chat session cursor")
    wp.add_argument("--set-sha", help="advance the git sha cursor (default: HEAD)")

    sub.add_parser("session-start", help="fast, non-blocking heartbeat for the SessionStart hook")

    rp = sub.add_parser("reconcile", help="heavy freshness scan → cache (run in background)")
    rp.add_argument("-v", "--verbose", action="store_true")

    svp = sub.add_parser("serve", help="boot local web server with /api/tree + web UI")
    svp.add_argument("--port", type=int, default=8347, help="port to listen on (default: 8347)")
    svp.add_argument("--wiki", default=None, help="path to wiki dir (default: <repo>/repo-wiki)")

    args = ap.parse_args()
    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "outline": cmd_outline,
        "catchup": cmd_catchup,
        "watermark": cmd_watermark,
        "session-start": cmd_session_start,
        "reconcile": cmd_reconcile,
        "serve": cmd_serve,
    }
    sys.exit(dispatch[args.cmd](args) or 0)


if __name__ == "__main__":
    main()
