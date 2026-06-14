# Wiki comments — agent consumption protocol

Comments posted through the wiki viewer are the primary **human-in-the-loop feedback
channel** for an agent editing a living knowledge base. This file documents:

1. How comments are stored (the data model).
2. Two ways an agent can receive them: **passive hook** and **active watch loop**.
3. The **consumption protocol**: act on a comment, then resolve it.

---

## 1. Data model

Each comment is one JSON record in `<wiki>/.comments/comments.jsonl`:

```json
{
  "id": "c_1a2b3c",
  "page": "architecture/api.md",
  "line": 42,
  "end_line": 45,
  "section": "Rate-limiting",
  "selected_text": "Billing endpoints must stay <50 req/s",
  "comment": "This limit changed — now 100 req/s since the ledger upgrade.",
  "ts": "2026-06-14T09:12:00+00:00",
  "status": "open"
}
```

Fields: `page` (wiki-relative path), `line`/`end_line` (1-indexed), `section`
(heading the selection lives under), `selected_text` (exact quote from the page),
`comment` (the user's note), `ts` (ISO-8601 UTC), `status` (`open` | `resolved`).

All fields except `line`, `end_line`, `section`, and `selected_text` are required;
anchor fields are best-effort (a page comment with no text selection omits them).

CLI:

```bash
python3 scripts/kb.py comments list              # human-readable, open only
python3 scripts/kb.py comments list --json       # JSON array, open only
python3 scripts/kb.py comments list --json --since <id>   # only records after <id>
python3 scripts/kb.py comments resolve <id> --note "<what you did>"
python3 scripts/kb.py comments clear             # drop all resolved records
```

---

## 2. Passive monitor — UserPromptSubmit hook

The **zero-effort path**: a shell hook injects open comments at the top of every
agent turn. No polling, no watch mode needed for low-traffic wikis.

**How it works:**
`assets/templates/comments-hook.sh` runs `kb.py comments list` on each
`UserPromptSubmit` event. If there are open comments it prints a clearly-labelled
block (which Claude Code includes in the next turn's context). It prints nothing when
the file is absent or empty — best-effort, exits 0 always.

**Install:**

1. Copy the template:
   ```bash
   mkdir -p .claude/hooks
   cp skills/repo-wiki/assets/templates/comments-hook.sh .claude/hooks/comments-hook.sh
   chmod +x .claude/hooks/comments-hook.sh
   ```

2. Merge into `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/comments-hook.sh\" 2>/dev/null || true"
             }
           ]
         }
       ]
     }
   }
   ```

3. `kb.py init` will install this automatically in a future release (init/docs tick).

**Design note:** `UserPromptSubmit` fires synchronously before each turn, so the hook
is injected into the context *for that turn*. Keep it fast — `kb.py comments list`
is a single file read. No git calls, no network.

---

## 3. Active watch loop

For hands-free, near-real-time monitoring — e.g. "watch the wiki while I'm editing"
— the agent enters a **poll loop**:

```
cursor = None   # or the id of the last comment you've already acted on

loop:
  new = kb.py comments list --json --since <cursor>
  for each comment in new:
    act on it (see §4 below)
    kb.py comments resolve <id> --note "<what you did>"
    cursor = id
  sleep <interval>   # 10–30 s is fine; adjust to taste
  check for stop signal (user message / file sentinel)
```

**Starting the loop:** the user says something like "watch the wiki for comments" or
"monitor wiki feedback". Confirm, then enter the loop.

**Cursor semantics:** `--since <id>` returns all records whose position in the file is
*after* the record with that id. If the id is not found (first run, or the file was
cleared) `kb.py` returns all open records — a safe default. Always advance the cursor
to the last processed id, not the last resolved one, so a re-run doesn't miss records
acted on but not yet resolved (uncommon, but safe).

**Stopping:** the user says "stop watching" / "done" / a file sentinel
(`<wiki>/.comments/stop-watch`) is present. Drain any remaining open comments, then
exit the loop. Clean up the sentinel file if used.

**Interval guidance:** 10 s is snappy for live editing; 30 s is comfortable for
background monitoring. Avoid sub-5 s — `comments.jsonl` is a flat file read, cheap,
but no need to spin.

---

## 4. Consumption protocol — act, then resolve

A comment is **actionable feedback** anchored to a specific location in a wiki page.
The anchor fields (`page`, `line`, `section`, `selected_text`) tell you exactly where
the user is pointing; the `comment` field tells you what they want.

### Step-by-step

1. **Read the page at the anchor.** Open `<wiki>/<page>` and read the section or
   lines indicated. Understand what the selected text claims and what the user is asking.

2. **Classify the ask.** Most comments fall into one of:
   - **Edit:** the user wants the content corrected, clarified, or expanded. This is
     the most common case — the comment *is* the human-in-the-loop approval to act.
   - **Capture:** the user is adding new knowledge that doesn't belong as an inline
     edit (a new decision, a new constraint). File to `inbox/` or the appropriate folder.
   - **Reply:** the user has a question for you, or you need clarification before
     acting. Reply in your turn; do not resolve until the question is answered and any
     resulting action is done.
   - **Defer:** the change is larger than one comment (e.g. a section restructure).
     Create a `decisions/` or `inbox/` ticket, note it in the resolve message.

3. **Act.**
   - **Edit:** make the change directly in the `.md` file. For `canonical` pages this
     is a human-in-the-loop action — the comment serves as the approval, so you may
     rewrite Compiled Truth. Append a **Timeline** entry:
     ```
     - 2026-06-14 — updated per viewer comment c_1a2b3c: <one-line summary>
     ```
     Bump `verified_against` to HEAD sha if the edit fixes a staleness signal.
   - **Capture:** create or append to the target page per the normal page model
     (Compiled Truth + Timeline, `source`, `covers`). Propose-only if `canonical`.
   - **Reply:** write your reply in the turn; resolve after.
   - **Defer:** note what you filed/created in the resolve message.

4. **Resolve.**
   ```bash
   python3 scripts/kb.py comments resolve <id> --note "<concise summary of action>"
   ```
   Always resolve after acting — not before. The `--note` is stored in the record and
   is visible to the user in the viewer, closing the feedback loop.

### What not to do

- Do not silently resolve without acting. The resolve note is the receipt.
- Do not leave comments open after acting — the viewer's unresolved count is the
  user's signal of pending work. A stale open comment misleads.
- Do not ask the user to confirm every edit on a `canonical` page — the comment is
  already approval. If you are genuinely uncertain (e.g. the comment is ambiguous),
  ask *once*, then act and resolve.
- Do not batch-resolve without acting. Each comment gets its own resolution note.

### Example

```
Comment c_1a2b3c on architecture/api.md:42
  § Rate-limiting
  > "Billing endpoints must stay <50 req/s"
  ✎ "This limit changed — now 100 req/s since the ledger upgrade."
```

**Action:**
1. Open `architecture/api.md`, find the Rate-limiting section.
2. Rewrite: "Billing endpoints must stay <100 req/s — upgraded ledger API."
3. Append to Timeline: `- 2026-06-14 — updated per viewer comment c_1a2b3c: rate limit raised to 100 req/s`
4. `kb.py comments resolve c_1a2b3c --note "updated rate limit to 100 req/s in Compiled Truth"`

---

## 5. When to use each mode

| Situation | Mode |
|---|---|
| Normal development session, occasional edits | **Passive hook** — comments surface automatically on next turn |
| Live wiki editing with user in the viewer | **Active watch loop** — near-real-time, no prompt needed |
| CI / scheduled review | **Active watch loop** in a background agent |
| One-off check | `kb.py comments list` directly |

The passive hook is installed once and requires no agent cooperation. The active watch
loop is opt-in per session. Both ultimately use the same consumption protocol (§4).
