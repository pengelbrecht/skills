---
type: decision
source: canonical
covers: [skills/telegram-cli/**]
verified_against: 74a5cd7
status: active
---

## Compiled Truth

`tg` tracks "how far have local agents processed a chat/topic" with a **client-side cursor
file** (`~/.config/tg/cursor.json`, keyed `chat_id` or `chat_id/topic_id`), not Telegram's
server-side read state. `tg read --since-cursor` fetches only messages above the cursor
**oldest-first** (so `--limit` never skips unseen traffic); `--advance-cursor` stores the
highest id printed. Writes are atomic (temp file + `os.replace`) and implicit advances are
**monotonic** — the file is re-read at write time and never moved backwards — so concurrent
agents sharing a config dir (cron loop + interactive session) can't regress each other.
Explicit rewind is `tg cursor <chat> --set N`. Primary consumer: the A2A polling loop
(`references/a2a.md`).

**Why client-side:** Telegram's unread/read state is account-wide UX state shared with the
user's phone apps — the user opening Telegram would clear it, and the CLI never marks
messages read by design. Agents need a *processed* cursor, not a *seen* flag, and it must be
shared across local agents but private to the machine.

**Rejected:** per-agent cursors (agents on one machine would double-answer A2A traffic);
file locking (monotonic max-merge on write is enough — the only concurrent hazard is a
lower advance overwriting a higher one); marking messages read server-side (side effects on
the user's own apps).

**Gotcha:** `--since-cursor` with no stored cursor starts from the *beginning* of the
chat/topic — initialize with `tg cursor --set <latest-id>` when only new traffic is wanted.

## Timeline

- 2026-07-16 — added on user request ("track queue progress locally but global among local
  agents"); verified live against the Pax Agent2Agent topic — @74a5cd7
