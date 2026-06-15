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
  precompact     PreCompact hook: print directive to mine context before compaction.
  session-end    SessionEnd hook: nudge to run catchup before session is gone.
  serve          Boot a local HTTP server (127.0.0.1) with /api/tree and the web UI.
"""
import argparse
import json
import os
import re
import shutil
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
            i = j  # j already points past the list items; do NOT add 1 again below
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
            i += 1
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
                          "action": action, "changed": hit[:3],
                          "verified_against": va})
        else:
            fresh += 1
    return {"pages": len(pages), "fresh": fresh, "stale": stale, "unverified": unverified}


def cmd_status(args):
    root = repo_root()
    wiki = root / "repo-wiki"
    if not wiki.exists():
        sys.exit("no repo-wiki/ here — run `kb.py init` first")
    st = compute_status(root, wiki, load_pages(wiki))

    new_only = getattr(args, "new", False)
    if new_only:
        # Delta mode: print only newly-stale pages and mark them surfaced.
        surfaced = load_surfaced(root)
        delta = newly_stale(st["stale"], surfaced)
        if delta:
            print(f"NEWLY STALE ({len(delta)} page(s) — soft signal, review not a gate):")
            for s in delta:
                print(f"  • {s['page']}  [{s['source']}] → {s['action']}")
                for h in s["changed"]:
                    print(f"        ↳ changed: {h}")
            mark_surfaced(surfaced, delta)
            save_surfaced(root, surfaced)
        # No output when nothing is newly stale.
        return 1 if delta else 0

    # Full standing report (does NOT touch the surfaced cursor).
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


def cmd_precompact(args):
    """PreCompact hook: print a directive to mine the current window before it's lost."""
    wm_hint = ""
    try:
        root = repo_root()
        wm = load_watermark(root)
        sid = wm.get("chat_session_id") or "(none)"
        wm_hint = f" Last extraction watermark: chat_session_id={sid}."
    except Exception:
        pass
    print(
        "[repo-wiki] Context is about to compact. Before it does:\n"
        "  1. Run the chat-extraction prompt (repo-wiki/references/extraction.md, Prompt 1)\n"
        "     over the recent conversation — only the window SINCE the last extraction\n"
        f"     (avoid re-mining already-ingested turns).{wm_hint}\n"
        "  2. Propose durable knowledge into repo-wiki/ (propose-only, no auto-apply).\n"
        "  3. Advance the watermark once done:\n"
        "       kb.py watermark --set-session <newest-session-id>\n"
        "  This prevents double-extraction on repeated compactions."
    )
    return 0


def cmd_session_end(args):
    """SessionEnd hook: nudge to run catchup before the session is gone."""
    print(
        "[repo-wiki] Session ending — run `kb catchup` (or `python3 kb.py catchup`) so\n"
        "this session's durable knowledge is mined before it's gone.\n"
        "Propose-only: file insights into repo-wiki/, then advance the watermark."
    )
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
    session start). Does NO git scan: it counts pages (cheap fs walk), reports only the
    NEWLY-stale delta (first time a page drifts), and spawns a detached `reconcile` to
    refresh the cache for next time. Never raises."""
    try:
        root = repo_root()
        wiki = root / "repo-wiki"
        if not wiki.exists():
            return 0

        # ── self-heal: ensure non-inheritable artifacts exist ──────────────────
        # .git/hooks/post-commit is not cloned; re-install if missing or not wired.
        try:
            install_post_commit_hook(root)  # idempotent — no-op if already present
        except Exception:
            pass
        # .ingest/ must exist for cache/watermark writes.
        try:
            (wiki / ".ingest").mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        n = sum(1 for _ in iter_pages(wiki))  # cheap: filesystem only, no git
        print("\n[repo-wiki] Knowledge base present. Read repo-wiki/INDEX.md first; "
              f"pull pages by relevance (covers/grep). {n} pages.")
        cache = load_status_cache(root)
        if cache:
            stale_list = cache.get("stale", [])
            if stale_list:
                surfaced = load_surfaced(root)
                delta = newly_stale(stale_list, surfaced)
                if delta:
                    print(f"[repo-wiki] {len(delta)} newly stale page(s) since last verified"
                          " — run `kb.py status` to review:")
                    for s in delta:
                        print(f"  • {s['page']}")
                    mark_surfaced(surfaced, delta)
                    save_surfaced(root, surfaced)
                # If nothing is newly stale, stay quiet about staleness.
            # Surface un-ingested chat sessions count (cached by background reconcile).
            uningested = cache.get("uningested_chat_sessions", 0)
            try:
                uningested = int(uningested)
            except Exception:
                uningested = 0
            if uningested > 0:
                print(f"[repo-wiki] {uningested} un-ingested chat session(s) — run `kb catchup`.")
        else:
            print("[repo-wiki] (freshness scan running in background; check `kb.py status`).")
        # Refresh the cache without blocking this session.
        spawn_background(["reconcile"], cwd=root)
    except Exception:
        pass
    return 0


def cmd_post_commit(args):
    """Post-commit git hook: nudge about drift this commit caused — soft, non-blocking.

    Always exits 0.  If anything goes wrong (not in a repo, no wiki, no covers hit,
    exception) → silent no-op.
    """
    try:
        root = repo_root()
        wiki = root / "repo-wiki"
        if not wiki.exists():
            return 0

        # Get files changed by the last commit.
        # git diff --name-only HEAD~1 HEAD fails for the root commit; treat that as no-op.
        out, code = git("diff", "--name-only", "HEAD~1", "HEAD", cwd=root)
        if code != 0 or not out:
            return 0
        commit_files = [p for p in out.splitlines() if p.strip()]
        if not commit_files:
            return 0

        pages = load_pages(wiki)
        st = compute_status(root, wiki, pages)
        surfaced = load_surfaced(root)
        delta = newly_stale(st["stale"], surfaced)

        # Filter to pages whose covers intersect THIS commit's changed files.
        triggered = []
        for entry in delta:
            # Re-read the covers for this page from the stale entry's changed list.
            # compute_status already limited 'changed' to paths that match covers;
            # we need to check whether any of those overlap with commit_files.
            page_changed = entry.get("changed", [])
            if any(cf in commit_files for cf in page_changed):
                triggered.append(entry)

        if not triggered:
            return 0

        print(f"[repo-wiki] {len(triggered)} page(s) may have drifted from this commit (soft signal — not a gate):")
        for entry in triggered:
            action = entry.get("action", "review")
            source = entry.get("source", "canonical")
            print(f"  • {entry['page']}  [{source}] → {action}")
            for h in entry.get("changed", [])[:3]:
                if h in commit_files:
                    print(f"        ↳ changed: {h}")

        mark_surfaced(surfaced, triggered)
        save_surfaced(root, surfaced)
    except Exception:
        pass
    return 0


def count_uningested_chat_sessions(root, days=30):
    """Use vendored recall to count sessions newer than the chat watermark.

    Returns an int (0 if recall unavailable, watermark absent, or any error).
    Best-effort: never raises.
    """
    try:
        if not RECALL.exists():
            return 0
        wm = load_watermark(root)
        watermark_sid = wm.get("chat_session_id") or ""
        proc = subprocess.run(
            [sys.executable, str(RECALL), "--project", str(root),
             "--days", str(days), "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return 0
        sessions = json.loads(proc.stdout)
        if not isinstance(sessions, list):
            return 0
        if not watermark_sid:
            return len(sessions)
        # Count sessions whose id (or path) comes after the watermark.
        # Recall returns sessions newest-first; we want those not yet ingested.
        # Strategy: count sessions that appear before (newer than) the watermark id.
        count = 0
        for s in sessions:
            sid = s.get("id") or s.get("session_id") or ""
            if sid == watermark_sid:
                break
            count += 1
        return count
    except Exception:
        return 0


def cmd_reconcile(args):
    """Heavy scan — meant to run detached / in the background. Computes git staleness over
    every page and writes the cache the fast `session-start` reads. Safe to run anytime."""
    root = repo_root()
    wiki = root / "repo-wiki"
    if not wiki.exists():
        return 0
    st = compute_status(root, wiki, load_pages(wiki))
    # Also count un-ingested chat sessions so session-start can surface it cheaply.
    st["uningested_chat_sessions"] = count_uningested_chat_sessions(root)
    st["ts"] = datetime.now(timezone.utc).isoformat()
    save_status_cache(root, st)
    if args.verbose:
        print(f"reconciled: {len(st['stale'])} stale, {st['fresh']} fresh, "
              f"{st['uningested_chat_sessions']} un-ingested chat session(s)")
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


# ── surfaced cursor ───────────────────────────────────────────────────────────
def surfaced_path(root):
    return root / "repo-wiki" / ".ingest" / "surfaced.json"


def load_surfaced(root):
    """Load the surfaced cursor: {<page>|<verified_against>: true, ...}.

    Returns an empty dict if the file is missing or malformed.
    """
    p = surfaced_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def save_surfaced(root, data):
    """Persist the surfaced cursor atomically."""
    p = surfaced_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _surfaced_key(page, verified_against):
    """Stable key for a (page, verified_against) pair."""
    return f"{page}|{verified_against}"


def newly_stale(stale_list, surfaced):
    """Return the subset of stale_list entries not yet in the surfaced cursor.

    Each entry must have 'page' and 'verified_against' (as compute_status now supplies).
    """
    out = []
    for entry in stale_list:
        key = _surfaced_key(entry["page"], entry.get("verified_against", ""))
        if key not in surfaced:
            out.append(entry)
    return out


def mark_surfaced(surfaced, pages):
    """Record (page, verified_against) pairs as surfaced in-place.

    'pages' is a list of stale-entry dicts (must have 'page' and 'verified_against').
    """
    for entry in pages:
        key = _surfaced_key(entry["page"], entry.get("verified_against", ""))
        surfaced[key] = True


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
    ensure_gitignore(root, ["repo-wiki/.ingest/", "repo-wiki/.comments/"])

    # SessionStart hook
    installed = install_hook(root)

    # UserPromptSubmit hook (comments)
    comments_installed = install_comments_hook(root)

    # PreCompact hook
    precompact_installed = install_precompact_hook(root)

    # SessionEnd hook
    session_end_installed = install_session_end_hook(root)

    # post-commit git hook
    post_commit_installed = install_post_commit_hook(root)

    # detect instruction files
    shims = [f for f in ("CLAUDE.md", "AGENTS.md", "GEMINI.md") if (root / f).exists()]

    print("repo-wiki initialized.\n")
    if created:
        print("created:")
        for c in created:
            print(f"  + {c}")
    print(f"\nSessionStart hook:      {'installed in .claude/settings.json' if installed else 'already present / skipped'}")
    print(f"Comments hook:          {'installed (UserPromptSubmit)' if comments_installed else 'already present / skipped'}")
    print(f"PreCompact hook:        {'installed (PreCompact)' if precompact_installed else 'already present / skipped'}")
    print(f"SessionEnd hook:        {'installed (SessionEnd)' if session_end_installed else 'already present / skipped'}")
    print(f"post-commit git hook:   {'installed in .git/hooks/post-commit' if post_commit_installed else 'already present / skipped'}")
    print("  Note: .git/hooks/ is local-only — not shared by clone. Collaborators")
    print("  get the hook re-installed automatically via the SessionStart self-heal.")
    print("ingest watermark:       repo-wiki/.ingest/ (gitignored)")
    print("comments store:         repo-wiki/.comments/ (gitignored)")
    print("\nComments: highlight text in the web viewer (kb serve) to post inline")
    print("feedback. Open comments are injected into every agent turn via the hook.")
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


def install_post_commit_hook(root):
    """Install (or append to) .git/hooks/post-commit to call kb.py post-commit.

    Rules:
    - Resolve the hooks dir via `git rev-parse --git-path hooks` (worktree-aware).
    - If the hook file doesn't exist: create it with #!/bin/sh, chmod +x.
    - If it exists but doesn't already call our kb.py: APPEND our line (preserve user content).
    - If it already calls kb.py post-commit: do nothing (idempotent).
    - The hook line uses `|| true` so a hook error never blocks a commit.

    Returns True if a new hook or new line was added, False if already present.
    """
    # Resolve hooks dir (respects git worktrees)
    out, code = git("rev-parse", "--git-path", "hooks", cwd=root)
    if code == 0 and out:
        hooks_dir = Path(out) if Path(out).is_absolute() else root / out
    else:
        hooks_dir = root / ".git" / "hooks"

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "post-commit"

    # Absolute path to kb.py for the hook line
    kb_abs = Path(__file__).resolve()
    hook_line = f'python3 "{kb_abs}" post-commit 2>/dev/null || true'

    if hook_file.exists():
        content = hook_file.read_text(encoding="utf-8")
        # Idempotency: check if kb.py post-commit is already wired
        if "kb.py" in content and "post-commit" in content:
            return False
        # Append our line (preserve the user's existing hook)
        with hook_file.open("a", encoding="utf-8") as f:
            if not content.endswith("\n"):
                f.write("\n")
            f.write(hook_line + "\n")
    else:
        # Create from scratch
        hook_file.write_text(f"#!/bin/sh\n{hook_line}\n", encoding="utf-8")

    # Ensure executable
    hook_file.chmod(hook_file.stat().st_mode | 0o111)
    return True


def install_precompact_hook(root):
    """Install the PreCompact hook that calls kb.py precompact.

    Idempotent: checks for an existing kb.py precompact entry before adding.
    Does not touch other hooks.
    """
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
        except Exception:
            data = {}
    hooks = data.setdefault("hooks", {})
    pc = hooks.setdefault("PreCompact", [])
    blob = json.dumps(pc)
    if "repo-wiki/scripts/kb.py" in blob and "precompact" in blob:
        return False
    cmd = 'python3 "$CLAUDE_PROJECT_DIR/skills/repo-wiki/scripts/kb.py" precompact 2>/dev/null || true'
    pc.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd}],
    })
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def install_session_end_hook(root):
    """Install the SessionEnd hook that calls kb.py session-end.

    Idempotent: checks for an existing kb.py session-end entry before adding.
    Does not touch other hooks.
    """
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
        except Exception:
            data = {}
    hooks = data.setdefault("hooks", {})
    se = hooks.setdefault("SessionEnd", [])
    blob = json.dumps(se)
    if "repo-wiki/scripts/kb.py" in blob and "session-end" in blob:
        return False
    cmd = 'python3 "$CLAUDE_PROJECT_DIR/skills/repo-wiki/scripts/kb.py" session-end 2>/dev/null || true'
    se.append({
        "matcher": "",
        "hooks": [{"type": "command", "command": cmd}],
    })
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def install_comments_hook(root):
    """Install the UserPromptSubmit hook that injects open wiki comments.

    Idempotent: checks whether a kb.py comments call is already present in any
    UserPromptSubmit entry before adding.  Does not touch SessionStart.
    """
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(exist_ok=True)
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
        except Exception:
            data = {}
    hooks = data.setdefault("hooks", {})
    ups = hooks.setdefault("UserPromptSubmit", [])
    blob = json.dumps(ups)
    # Idempotency: bail if a kb.py comments list invocation is already wired
    if "repo-wiki/scripts/kb.py" in blob and "comments list" in blob:
        return False
    cmd = (
        'KB="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}'
        '/skills/repo-wiki/scripts/kb.py"; '
        'PENDING="$(python3 "$KB" comments list 2>/dev/null)" || true; '
        '[ -z "$PENDING" ] || [ "$PENDING" = "No open comments." ] && exit 0; '
        "printf '=== PENDING WIKI COMMENTS (feedback from the viewer -- please act on these) ===\\n'; "
        'printf \'%s\\n\' "$PENDING"; '
        "printf '=== end wiki comments -- resolve each with: kb.py comments resolve <id> --note \"<what you did>\" ===\\n'"
    )
    ups.append({
        "matcher": "",
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


_SEARCH_MAX_QUERY = 200
_SEARCH_MAX_RESULTS = 100


def _search_wiki(wiki, query):
    """Search wiki for query using ripgrep (or grep fallback).

    Security contract:
    - command is built as an argv list; shell=False (never shell=True).
    - query is passed as a positional argument (after -e) so shell metacharacters
      in the query cannot be interpreted by a shell.
    - wiki dir is resolved and passed as a Path argument.
    """
    wiki_str = str(wiki)
    if shutil.which("rg"):
        cmd = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color", "never",
            "--max-count", "1",   # one match per file (keep results concise)
            "-g", "*.md",
            "-e", query,
            wiki_str,
        ]
    else:
        cmd = [
            "grep",
            "-rn",
            "--include=*.md",
            "-e", query,
            wiki_str,
        ]

    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []

    results = []
    for raw_line in proc.stdout.splitlines():
        # ripgrep / grep output format: /abs/path/file.md:lineno:matched text
        # Split on first two colons only
        parts = raw_line.split(":", 2)
        if len(parts) < 3:
            continue
        abs_path, lineno_str, snippet = parts[0], parts[1], parts[2]
        try:
            lineno = int(lineno_str)
        except ValueError:
            continue
        try:
            rel = str(Path(abs_path).relative_to(wiki))
        except ValueError:
            continue
        results.append({
            "path": rel,
            "line": lineno,
            "snippet": snippet.strip()[:300],
        })
        if len(results) >= _SEARCH_MAX_RESULTS:
            break

    return results


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
            self.send_header("Cache-Control", "no-cache")  # always revalidate after a skill update
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            from urllib.parse import urlparse, parse_qs
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

            # /api/page?path=<rel>
            if path == "/api/page":
                qs = parse_qs(parsed.query)
                rel_parts = qs.get("path", [])
                if not rel_parts:
                    self.send_json({"error": "missing ?path="}, status=400)
                    return
                rel = rel_parts[0]
                # Reject empty, absolute paths, or paths containing ".."
                if not rel or rel.startswith("/") or ".." in rel.split("/"):
                    self.send_json({"error": "invalid path"}, status=400)
                    return
                target = (wiki / rel).resolve()
                # Sandbox: target must be inside wiki
                try:
                    target.relative_to(wiki)
                except ValueError:
                    self.send_json({"error": "path outside wiki"}, status=403)
                    return
                if not target.exists() or not target.is_file() or target.suffix != ".md":
                    self.send_json({"error": "not found"}, status=400)
                    return
                try:
                    text = target.read_text(encoding="utf-8", errors="replace")
                    fm = parse_frontmatter(text)
                    # Strip the leading ---...--- block from markdown body.
                    # Count how many lines the frontmatter block occupies (including
                    # both --- delimiters and any trailing blank line) so the client
                    # can offset line anchors to match real on-disk line numbers.
                    body = text
                    frontmatter_lines = 0
                    if text.startswith("---"):
                        end = text.find("\n---", 3)
                        if end != -1:
                            # stripped_prefix is text[:end+4] which ends in "\n---"
                            # (the closing delimiter has no trailing \n in the prefix).
                            # newline count + 1 gives the number of lines occupied by the
                            # frontmatter block itself (opening --- through closing ---).
                            stripped_prefix = text[:end + 4]
                            frontmatter_lines = stripped_prefix.count("\n") + 1
                            body = text[end + 4:]
                            # body now starts with "\n" (line-terminator of the closing ---
                            # line, already counted above) followed by any blank separator
                            # lines. Skip the first "\n" (terminator), then count the
                            # remaining leading blank lines — each is one more file line
                            # consumed before body content begins.
                            if body.startswith("\n"):
                                body = body[1:]  # consume the --- line terminator
                            leading_blank = len(body) - len(body.lstrip("\n"))
                            frontmatter_lines += leading_blank
                            body = body.lstrip("\n")
                    rel_str = str(target.relative_to(wiki))
                    stat = target.stat()
                    self.send_json({
                        "path": rel_str,
                        "frontmatter": fm,
                        "markdown": body,
                        "frontmatter_lines": frontmatter_lines,
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    })
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # /api/changed?path=<rel> — return mtime (and size) for a single wiki file
            # Used by the client poll to detect in-place edits without re-fetching content.
            if path == "/api/changed":
                qs = parse_qs(parsed.query)
                rel_parts = qs.get("path", [])
                if not rel_parts:
                    self.send_json({"error": "missing ?path="}, status=400)
                    return
                rel = rel_parts[0]
                if not rel or rel.startswith("/") or ".." in rel.split("/"):
                    self.send_json({"error": "invalid path"}, status=400)
                    return
                target = (wiki / rel).resolve()
                try:
                    target.relative_to(wiki)
                except ValueError:
                    self.send_json({"error": "path outside wiki"}, status=400)
                    return
                if not target.exists() or not target.is_file() or target.suffix != ".md":
                    self.send_json({"error": "not found"}, status=400)
                    return
                try:
                    stat = target.stat()
                    self.send_json({"mtime": stat.st_mtime, "size": stat.st_size})
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # /api/revision — return max mtime across all wiki .md files
            # Used by the client poll to detect any wiki change (new page, edit).
            # Skip .comments/ and .ingest/ — they are internal state dirs, not wiki content.
            if path == "/api/revision":
                try:
                    max_mtime = 0.0
                    for p in wiki.rglob("*.md"):
                        if "/.comments/" in str(p) or "/.ingest/" in str(p):
                            continue
                        try:
                            mt = p.stat().st_mtime
                            if mt > max_mtime:
                                max_mtime = mt
                        except OSError:
                            pass
                    self.send_json({"revision": max_mtime})
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # /api/search?q=<query>
            if path == "/api/search":
                qs = parse_qs(parsed.query)
                q_parts = qs.get("q", [])
                q = q_parts[0] if q_parts else ""
                if not q or not q.strip():
                    self.send_json({"results": []})
                    return
                if len(q) > _SEARCH_MAX_QUERY:
                    self.send_json({"error": "query too long"}, status=400)
                    return
                try:
                    results = _search_wiki(wiki, q)
                    self.send_json({"results": results})
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # /api/status — freshness for the served wiki
            if path == "/api/status":
                try:
                    # Locate the git root containing the wiki (best-effort)
                    out, code = git("rev-parse", "--show-toplevel", cwd=str(wiki))
                    if code != 0 or not out:
                        # Not in a git repo — return all unverified gracefully
                        pages = load_pages(wiki)
                        unverified = [str(p.relative_to(wiki)) for p, _ in pages]
                        self.send_json({"stale": {}, "unverified": unverified})
                        return
                    root = Path(out)
                    pages = load_pages(wiki)
                    raw = compute_status(root, wiki, pages)
                    # Reshape to API shape:
                    # stale: {rel_path: {action, source, changed}}
                    # unverified: [rel_path, ...]
                    stale_map = {}
                    for s in raw.get("stale", []):
                        stale_map[s["page"]] = {
                            "action": s["action"],
                            "source": s["source"],
                            "changed": s.get("changed", []),
                        }
                    self.send_json({
                        "stale": stale_map,
                        "unverified": raw.get("unverified", []),
                    })
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # /api/backlinks?path=<rel> — pages that reference this page
            if path == "/api/backlinks":
                qs = parse_qs(parsed.query)
                rel_parts = qs.get("path", [])
                if not rel_parts:
                    self.send_json({"error": "missing ?path="}, status=400)
                    return
                rel = rel_parts[0]
                # Sandbox: reject empty, absolute, or path-traversal attempts
                if not rel or rel.startswith("/") or ".." in rel.split("/"):
                    self.send_json({"error": "invalid path"}, status=400)
                    return
                target = (wiki / rel).resolve()
                try:
                    target.relative_to(wiki)
                except ValueError:
                    self.send_json({"error": "path outside wiki"}, status=403)
                    return
                # Search for the page by its filename (stem is usually unique enough)
                # Use both the relative path and filename as search terms
                try:
                    filename = Path(rel).name  # e.g. "c.md"
                    results = _search_wiki(wiki, re.escape(filename))
                    # Exclude the page itself from backlinks
                    backlinks = [r for r in results if r["path"] != rel]
                    self.send_json({"backlinks": backlinks})
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=500)
                return

            # static assets
            if path in _STATIC:
                self.send_static(WEB_ASSETS / _STATIC[path])
                return

            self.send_error(404, "Not found")

        def do_POST(self):  # noqa: N802
            from urllib.parse import urlparse
            parsed = urlparse(self.path)
            path = parsed.path

            # /api/comment — append a human comment record
            if path == "/api/comment":
                # Read body
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    # Bound the request body (16 KB is well above the field caps)
                    if length > 16384:
                        self.send_json({"error": "request body too large"}, status=413)
                        return
                    body_bytes = self.rfile.read(length)
                    data = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    self.send_json({"error": "invalid JSON body"}, status=400)
                    return

                # Extract fields
                page = data.get("page", "")
                line = data.get("line")
                end_line = data.get("end_line")
                section = data.get("section", "") or ""
                selected_text = data.get("selected_text", "") or ""
                comment = data.get("comment", "") or ""

                # Validate required non-empty fields
                if not comment or not comment.strip():
                    self.send_json({"error": "comment is required and must be non-empty"}, status=400)
                    return
                if not selected_text or not selected_text.strip():
                    self.send_json({"error": "selected_text is required and must be non-empty"}, status=400)
                    return

                # Size caps
                if len(comment) > 4000:
                    self.send_json({"error": "comment exceeds 4000 character limit"}, status=400)
                    return
                if len(selected_text) > 2000:
                    self.send_json({"error": "selected_text exceeds 2000 character limit"}, status=400)
                    return
                if len(section) > 200:
                    self.send_json({"error": "section exceeds 200 character limit"}, status=400)
                    return

                # Validate line/end_line are ints or null
                if line is not None:
                    if not isinstance(line, int):
                        self.send_json({"error": "line must be an integer or null"}, status=400)
                        return
                if end_line is not None:
                    if not isinstance(end_line, int):
                        self.send_json({"error": "end_line must be an integer or null"}, status=400)
                        return

                # Sandbox page to wiki dir (same pattern as /api/page).
                # Belt-and-suspenders: also reject percent-encoded traversal sequences
                # (%2e = '.', %2f = '/').  The resolve()+relative_to() sandwich is the
                # real gate; this guard catches them at the string level first.
                if (not page or page.startswith("/") or ".." in page.split("/")
                        or "%2e" in page.lower() or "%2f" in page.lower()):
                    self.send_json({"error": "invalid page path"}, status=400)
                    return
                target = (wiki / page).resolve()
                try:
                    target.relative_to(wiki)
                except ValueError:
                    self.send_json({"error": "page path outside wiki"}, status=400)
                    return
                if not target.exists() or not target.is_file() or target.suffix != ".md":
                    self.send_json({"error": "page not found or not a .md file"}, status=400)
                    return

                # Build record
                import secrets
                import time as _time
                ts_ms = int(_time.time() * 1000)
                rand_hex = secrets.token_hex(4)
                comment_id = f"{ts_ms:x}-{rand_hex}"
                ts_iso = datetime.now(timezone.utc).isoformat()
                record = {
                    "id": comment_id,
                    "page": str(target.relative_to(wiki)),
                    "line": line,
                    "end_line": end_line,
                    "section": section,
                    "selected_text": selected_text,
                    "comment": comment,
                    "ts": ts_iso,
                    "status": "open",
                }

                # Append to <wiki>/.comments/comments.jsonl
                comments_dir = wiki / ".comments"
                comments_dir.mkdir(exist_ok=True)
                comments_file = comments_dir / "comments.jsonl"
                try:
                    with comments_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                except Exception as exc:
                    self.send_json({"error": f"failed to write comment: {exc}"}, status=500)
                    return

                self.send_json({"ok": True, "id": comment_id}, status=201)
                return

            self.send_error(404, "Not found")

    return WikiHandler


def _background_reconcile(wiki):
    """Run a freshness reconcile in a daemon thread so serve startup isn't blocked."""
    import threading

    def _run():
        try:
            out, code = git("rev-parse", "--show-toplevel", cwd=str(wiki))
            if code != 0 or not out:
                return  # Not in a git repo — skip
            root = Path(out)
            pages = load_pages(wiki)
            st = compute_status(root, wiki, pages)
            st["ts"] = datetime.now(timezone.utc).isoformat()
            save_status_cache(root, st)
        except Exception:
            pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()


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
        wiki = (root / "repo-wiki").resolve()

    if not wiki.exists():
        sys.exit(f"wiki directory does not exist: {wiki}\n"
                 "Run `kb.py init` first, or pass --wiki <path>.")

    # Kick a background freshness refresh so the cache is warm — best-effort, never blocks.
    _background_reconcile(wiki)

    handler_cls = _make_handler(wiki)
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler_cls)
    except OSError as exc:
        sys.exit(f"cannot bind 127.0.0.1:{args.port} — {exc}.\n"
                 "Is the port already in use? Try --port <other>.")

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


# ── comments helpers ──────────────────────────────────────────────────────────

def _resolve_wiki_for_comments(args):
    """Resolve the wiki directory for comments commands."""
    if args.wiki:
        wiki = Path(args.wiki).resolve()
    else:
        try:
            root = repo_root()
        except SystemExit:
            sys.exit("not inside a git repo and --wiki not specified")
        wiki = (root / "repo-wiki").resolve()
    if not wiki.exists():
        sys.exit(f"wiki directory does not exist: {wiki}")
    return wiki


def _load_comments(comments_file):
    """Load all comment records from comments.jsonl; skip malformed lines."""
    records = []
    if not comments_file.exists():
        return records
    with comments_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _save_comments(comments_file, records):
    """Rewrite comments.jsonl atomically (write to temp then rename) with the given records.

    Using a temp file in the same directory then Path.replace() ensures an atomic swap on
    POSIX so a crash mid-write never truncates the live file.
    """
    import tempfile
    comments_dir = comments_file.parent
    comments_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(comments_dir), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        Path(tmp_path).replace(comments_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def cmd_comments(args):
    wiki = _resolve_wiki_for_comments(args)
    comments_dir = wiki / ".comments"
    comments_file = comments_dir / "comments.jsonl"

    subcmd = getattr(args, "comments_cmd", None) or "list"

    if subcmd == "list":
        records = _load_comments(comments_file)
        since = getattr(args, "since", None)
        as_json = getattr(args, "json", False)

        # Apply --since filter (by id or ts) for machine-readable output
        if since and as_json:
            # Find the position of the cursor record and return everything after it
            idx = None
            for i, r in enumerate(records):
                if r.get("id") == since or r.get("ts", "") == since:
                    idx = i
                    break
            if idx is not None:
                records = records[idx + 1:]
            else:
                # cursor not found — return all (safe default for a watch-loop)
                pass

        open_records = [r for r in records if r.get("status") == "open"]

        if as_json:
            print(json.dumps(open_records, ensure_ascii=False, indent=2))
        else:
            if not open_records:
                print("No open comments.")
                return 0
            for r in open_records:
                loc = r.get("page", "")
                line = r.get("line")
                if line is not None:
                    loc += f":{line}"
                section = r.get("section", "")
                snippet = r.get("selected_text", "")
                if len(snippet) > 60:
                    snippet = snippet[:60] + "…"
                comment_text = r.get("comment", "")
                if len(comment_text) > 80:
                    comment_text = comment_text[:80] + "…"
                print(f"[{r.get('id')}] {loc}")
                if section:
                    print(f"  § {section}")
                print(f"  > {snippet!r}")
                print(f"  ✎ {comment_text}")
                print()
        return 0

    if subcmd == "resolve":
        comment_id = getattr(args, "id", None)
        note = getattr(args, "note", None)
        if not comment_id:
            sys.exit("resolve requires an <id> argument")
        records = _load_comments(comments_file)
        found = False
        for r in records:
            if r.get("id") == comment_id:
                r["status"] = "resolved"
                r["resolved_ts"] = datetime.now(timezone.utc).isoformat()
                if note:
                    r["resolved_note"] = note
                found = True
                break
        if not found:
            sys.exit(f"comment id not found: {comment_id}")
        _save_comments(comments_file, records)
        print(f"resolved: {comment_id}")
        return 0

    if subcmd == "clear":
        records = _load_comments(comments_file)
        remaining = [r for r in records if r.get("status") == "open"]
        removed = len(records) - len(remaining)
        _save_comments(comments_file, remaining)
        print(f"cleared {removed} resolved comment(s); {len(remaining)} open remain.")
        return 0

    sys.exit(f"unknown comments subcommand: {subcmd}")


def main():
    ap = argparse.ArgumentParser(prog="kb.py", description="repo-wiki command line")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="scaffold the wiki + install the hook")

    sp = sub.add_parser("status", help="report stale pages (soft signal)")
    sp.add_argument("-v", "--verbose", action="store_true", help="also list unverified pages")
    sp.add_argument("--new", action="store_true",
                    help="print only newly-stale pages (delta since last surfaced) and mark them surfaced")

    sub.add_parser("outline", help="emit wiki structure for context (load before extracting)")

    cp = sub.add_parser("catchup", help="enumerate chat sessions since the watermark")
    cp.add_argument("--days", type=int, default=30, help="look-back window (default 30)")

    wp = sub.add_parser("watermark", help="show / advance the ingest watermark")
    wp.add_argument("--set-session", help="advance the chat session cursor")
    wp.add_argument("--set-sha", help="advance the git sha cursor (default: HEAD)")

    sub.add_parser("session-start", help="fast, non-blocking heartbeat for the SessionStart hook")

    sub.add_parser("precompact", help="PreCompact hook: print extract-before-compaction directive")

    sub.add_parser("session-end", help="SessionEnd hook: nudge to run catchup before session is gone")

    sub.add_parser("post-commit", help="git post-commit hook: nudge about drift this commit caused (soft, non-blocking)")

    rp = sub.add_parser("reconcile", help="heavy freshness scan → cache (run in background)")
    rp.add_argument("-v", "--verbose", action="store_true")

    svp = sub.add_parser("serve", help="boot local web server with /api/tree + web UI")
    svp.add_argument("--port", type=int, default=8347, help="port to listen on (default: 8347)")
    svp.add_argument("--wiki", default=None, help="path to wiki dir (default: <repo>/repo-wiki)")

    # comments subcommand with its own sub-subcommands
    cosp = sub.add_parser("comments", help="manage human→agent comment channel")
    cosp.add_argument("--wiki", default=None, help="path to wiki dir (default: <repo>/repo-wiki)")
    cosub = cosp.add_subparsers(dest="comments_cmd")

    co_list = cosub.add_parser("list", help="list open comments (default action)")
    co_list.add_argument("--json", action="store_true", help="machine-readable JSON output")
    co_list.add_argument("--since", default=None, metavar="ID_OR_TS",
                         help="return only comments after this id or timestamp (with --json)")
    co_list.add_argument("--wiki", default=None, help="path to wiki dir (overrides parent --wiki)")

    co_res = cosub.add_parser("resolve", help="mark a comment resolved")
    co_res.add_argument("id", help="comment id to resolve")
    co_res.add_argument("--note", default=None, help="optional resolution note")
    co_res.add_argument("--wiki", default=None, help="path to wiki dir (overrides parent --wiki)")

    co_clear = cosub.add_parser("clear", help="remove all resolved comments from the file")
    co_clear.add_argument("--wiki", default=None, help="path to wiki dir (overrides parent --wiki)")

    args = ap.parse_args()
    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "outline": cmd_outline,
        "catchup": cmd_catchup,
        "watermark": cmd_watermark,
        "session-start": cmd_session_start,
        "precompact": cmd_precompact,
        "session-end": cmd_session_end,
        "post-commit": cmd_post_commit,
        "reconcile": cmd_reconcile,
        "serve": cmd_serve,
        "comments": cmd_comments,
    }
    sys.exit(dispatch[args.cmd](args) or 0)


if __name__ == "__main__":
    main()
