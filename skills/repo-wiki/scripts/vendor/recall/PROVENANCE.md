# Vendored: `recall`

These scripts are copied verbatim from the `recall` skill so that `repo-wiki` has **no
skill dependencies** — it ships its own chat-enumeration + transcript-reading engine.

| | |
|---|---|
| Source skill | `recall` (`~/.claude/skills/recall`) |
| Version | **0.4.1** (per recall `CHANGELOG.md`; the version that made the positional `query` optional → list-mode) |
| Vendored | 2026-06-13 |
| Files | `recall.py`, `read_session.py`, `LICENSE` |
| Dependencies | Python 3 standard library only (`sqlite3` with FTS5, `argparse`, `json`, `pathlib`) — no pip installs |

## What we use

- `recall.py --project <repo> --days N` (no query) — **list-mode**: enumerate every
  session in the window, newest first, across Claude Code / Codex / pi. This is the
  catch-up enumerator.
- `recall.py "<query>" --project <repo>` — BM25 full-text search, used to dedup a
  captured nugget against past sessions before proposing it.
- `read_session.py <transcript-path>` — read a raw transcript, auto-detecting format.

## Re-syncing

Upstream is the user's own `recall` skill, so updating is a copy:

```bash
cp ~/.claude/skills/recall/scripts/recall.py        ./recall.py
cp ~/.claude/skills/recall/scripts/read_session.py  ./read_session.py
cp ~/.claude/skills/recall/LICENSE                   ./LICENSE
# then bump the Version line above
```

The global index lives at `~/.recall.db` (machine-local cache), consistent with
repo-wiki's local-watermark model — only wiki edits are committed.
