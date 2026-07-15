---
name: telegram-cli
description: Use when any task involves the user's personal Telegram — reading messages, checking unreads, listing chats, searching history, or sending/replying to messages. Covers requests like "check my telegram", "what's new in <chat>", "search telegram for X", "reply to <person>", "send a telegram message". Also use when setting up Telegram access on a new machine.
---

# telegram-cli — Telegram as the user's own account

`tg` is a single-file CLI (Python + Telethon via `uv`, MTProto) logged in as the **user's personal Telegram account**. It is NOT a bot — every read and send happens as the user, and it sees everything their official apps see.

**Not installed yet?** (`which tg` fails, or it reports missing config/login) → follow `references/setup.md`. The script itself is `scripts/tg` in this skill.

## Quick reference

```
tg dialogs [--limit N] [--json]        # chats, newest first, with unread counts
tg read <chat> [--limit N] [--json]    # recent messages, oldest-first; --before-id <ID> pages back
tg search <query> [--chat C] [--json]  # global or per-chat message search
tg send <chat> <text...>               # send as the user — see rule below
tg whoami / tg login / tg logout
```

`<chat>` = @username, t.me link, numeric id, or unique title substring (ambiguity is reported with candidates). Prefer `--json` when post-processing. `[id]` prefixes are real message ids. Config: `~/.config/tg/`; `TG_CONFIG_DIR` overrides for multi-account.

## RULE: Outgoing messages require verbatim approval

Before ANY `tg send`, you MUST:

1. Show the user the **recipient** and the **exact, final message text, verbatim** — the literal string that will be sent, not a summary or paraphrase.
2. Wait for their explicit approval of that text.
3. Send only the approved text, unchanged. Any edit — theirs or yours, even one word — restarts at step 1.

**No exceptions:**
- "They asked me to reply" is not approval of the text — they approved the *task*, not the *words*.
- Earlier approval doesn't carry over to a new or edited message.
- Not for urgency, short messages ("it's just 'ok'"), or drafts they "basically already dictated" — if they dictated it, showing the verbatim text costs one line.
- Never batch: N messages = N verbatim approvals.

## Gotchas

- Session expired? Re-login without a TTY: `tg login --phone +<countrycode><number>` (sends code), then `tg login --code <CODE> [--password <2FA>]` after the user reports the code.
- First run after an update may be slow while uv resolves dependencies.
- The session file grants full account access — never copy it off the machine or into a repo.
