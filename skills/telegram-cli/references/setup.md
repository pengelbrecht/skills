# Setting up `tg` on a fresh machine

One-time setup. Prerequisites: macOS/Linux, [`uv`](https://docs.astral.sh/uv/) installed (`brew install uv` or the curl installer), and `~/.local/bin` on PATH.

## 1. Install the script

Copy `scripts/tg` from this skill onto the PATH and make it executable:

```bash
cp "$(dirname <path-to-this-skill>)/scripts/tg" ~/.local/bin/tg   # or curl it from the repo
chmod +x ~/.local/bin/tg
tg --help   # first run resolves Telethon via uv, then it's cached
```

No venv or pip needed — the script carries PEP 723 inline metadata and `uv run` handles dependencies.

## 2. Get Telegram API credentials

The user must do this themselves (it's tied to their account):

1. Go to https://my.telegram.org and log in with their phone number.
2. Open **API development tools**, create an app (any name/platform).
3. Copy the `api_id` (number) and `api_hash` (hex string).

Then write the config:

```bash
mkdir -p ~/.config/tg
echo '{"api_id": 123456, "api_hash": "abcdef0123..."}' > ~/.config/tg/config.json
chmod 600 ~/.config/tg/config.json
```

## 3. Log in (one time)

In a real terminal, plain `tg login` prompts interactively. From an agent session without interactive stdin, use the two-step flow:

```bash
tg login --phone +4512345678        # Telegram sends a login code to the user's app/SMS
tg login --code 12345               # user reports the code back; add --password <2FA> if enabled
```

Verify with `tg whoami` and `tg dialogs --limit 5`.

Notes:
- The login code must come from the user; never guess or retry codes repeatedly (Telegram rate-limits and may flood-wait).
- The session persists in `~/.config/tg/tg.session` — no further logins unless the user revokes it (Telegram → Settings → Devices) or changes their password.

## Security

- `config.json` and especially `tg.session` grant **full access to the account**. Keep them `chmod 600`, never commit them, never copy them off the machine.
- Brand-new Telegram accounts occasionally get flagged when first using the API; established accounts doing normal reads are fine.

## Multi-account

Point `TG_CONFIG_DIR` at a second config dir:

```bash
TG_CONFIG_DIR=~/.config/tg-work tg login --phone +45...
TG_CONFIG_DIR=~/.config/tg-work tg dialogs
```
