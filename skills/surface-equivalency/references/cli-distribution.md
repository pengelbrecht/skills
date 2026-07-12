# CLI distribution and in-place upgrade

How users get the CLI, and how it stays current. Upgrade is not an
afterthought: a CLI that drifts out of date in the field re-creates the
surface-drift problem between *client versions* — the server and MCP evolve,
the installed CLI doesn't, and "works over MCP but not in my CLI" is back.

## Contents

- [Install ladder](#install-ladder)
- [The install script](#the-install-script)
- [The upgrade stack](#the-upgrade-stack)
- [Version pinning and channels](#version-pinning-and-channels)

## Install ladder

Climb as the audience grows; don't build step 3 on day one.

1. **npm only** — `npm i -g acme-cli`, `npx acme-cli`. Zero infra, right for
   a Node-guaranteed audience. Upgrades are the user's problem (`npm i -g`
   again), which is acceptable exactly as long as the audience is developers
   who know that.
2. **Compiled binaries + `curl | sh`** — the canonical path once the CLI
   matters. `bun build --compile` per platform
   (darwin-arm64/x64, linux-arm64/x64, windows), binaries attached to GitHub
   Releases, installed by a script:
   `curl -fsSL https://acme.dev/install.sh | sh`. Users need neither Node nor
   Bun, and the binary can own its own upgrade (below). Keep npm as a
   secondary channel — publish platform binaries as optional dependencies
   (the pnpm v12 pattern) so `npx` still works.
3. **Homebrew tap** — when you have enough macOS users to expect it.
   `brew install acme/tap/acme`. Note this *constrains* self-update (below).

## The install script

Keep it boring and inspectable — users do read these:

- Detect OS + arch; download the matching binary from the latest GitHub
  Release; verify a checksum; install to `~/.local/bin` (no sudo) with a
  clear message if that's not on PATH.
- Idempotent: re-running installs the latest version over the old one.
- Record the install method (see below) so `acme update` knows what it's
  dealing with, e.g. write `~/.config/acme/install.json` with
  `{ "method": "script" }`.

## The upgrade stack

Four parts. They ship together — each one alone is insufficient, and one of
them (telemetry without enforcement) is a named anti-pattern on its own.

### 1. `acme update` — self-update with install-method detection

Detect how the CLI was installed **before** touching anything:

- **Homebrew** → do not self-update. A brew-managed binary that replaces
  itself corrupts brew's bookkeeping. Print the right command instead:
  `Installed via Homebrew — run: brew upgrade acme/tap/acme`.
- **npm global / npx** → delegate: run (or print) `npm i -g acme-cli@latest`.
  Detect by checking whether `process.execPath`/argv[0] resolves under a
  node_modules or npm prefix.
- **Compiled binary (script install)** → true self-update: query the latest
  version (GitHub Releases API or your own version endpoint), download the
  platform binary to a temp file alongside the current one, verify checksum,
  then **atomic rename over self** (rename works on a running executable on
  macOS/Linux; on Windows, rename the old binary aside first, then move the
  new one in).

```ts
// surfaces/cli/commands/update.ts (shape, not a library)
const method = detectInstallMethod(); // "brew" | "npm" | "binary"
if (method === "brew") return print("Run: brew upgrade acme/tap/acme");
if (method === "npm")  return print("Run: npm i -g acme-cli@latest");
const latest = await fetchLatestVersion();          // version endpoint / Releases API
if (latest === VERSION) return print(`Already up to date (${VERSION})`);
const tmp = await downloadBinary(latest, platform); // to same filesystem as target
await verifyChecksum(tmp, latest);
await atomicReplace(tmp, process.execPath);
print(`Updated ${VERSION} → ${latest}`);
```

### 2. Passive update check (the nudge)

- At most once per 24h: check the version endpoint in a **non-blocking**
  background fetch, cache the result in
  `~/.config/acme/update-cache.json`.
- On the *next* command start, if the cache says a newer version exists,
  print one line to **stderr**: `A new version is available: 1.4.2 → 1.5.0.
  Run: acme update`.
- Re-validate the cache against the currently running version (so the nudge
  disappears immediately after an upgrade) and never let a failed check block
  or slow a command — the check is best-effort, the nudge is the product.
- Respect CI: skip the check when `CI` is set or stdout isn't a TTY.

### 3. Server-side minimum version — telemetry with teeth

The CLI sends its version on every server call (a header:
`x-acme-cli-version`). The server enforces a floor:

- Below `warnBelow` → include a warning in the response envelope; CLI prints
  it.
- Below `rejectBelow` → refuse with a stable error code
  (`CLI_VERSION_UNSUPPORTED`) and the upgrade command in the message.

Collecting the version and doing nothing with it is the anti-pattern:
the server watches clients skew for months and the operator learns about it
from a support ticket. Enforcement is what closes the loop — it's also what
lets you actually delete server-side compatibility shims.

### 4. Never auto-update silently

Nudge + explicit `acme update`, always. Silent background replacement of a
developer tool breaks reproducibility (CI images, scripted environments) and
trust. The one acceptable automation: an explicit opt-in config
(`autoUpdate: true`) for users who want it.

## Version pinning and channels

- Support `acme update --version 1.4.2` (and the install script's
  `VERSION=1.4.2` env) for pinning and rollback — the atomic-replace
  machinery already supports installing *any* version, so expose it.
- If you need prerelease channels, one `channel` field in
  `~/.config/acme/install.json` and a `--channel beta` flag on `update` is
  enough; resist anything fancier until real demand exists.
- Print the version prominently in `acme --version` **and** in `acme whoami`
  / diagnostics output — version confusion is the first question in every
  support thread.
