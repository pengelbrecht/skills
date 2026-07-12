# Auth across surfaces

One auth server, one principal type, three login flows. Auth is where
"equivalent surfaces" most often silently diverges: each surface grows its own
credential handling, and suddenly authorization behavior depends on how you
connected.

## Contents

- [The invariant: edge-resolved principal](#the-invariant-edge-resolved-principal)
- [MCP: OAuth](#mcp-oauth)
- [CLI: device-code login](#cli-device-code-login)
- [API keys: the shared non-interactive path](#api-keys)
- [Token storage on the client](#token-storage-on-the-client)

## The invariant: edge-resolved principal

Each surface resolves the caller's identity its own way, but all of them
produce the same `Principal` value and pass it explicitly into the core:

```ts
export type Principal =
  | { kind: "user"; userId: string; orgId: string }
  | { kind: "agent"; keyId: string; orgId: string; scopes: string[] };
```

Authorization decisions, audit records, and rate limits key off the
principal — never off the transport. If the core ever asks "did this come in
over MCP?", authorization has forked and the surfaces are no longer
equivalent. The conformance gate should run fixtures under a fixed test
principal so authorization behavior is part of what's compared.

## MCP: OAuth

Follow the MCP specification's authorization flow: the MCP server acts as an
OAuth resource server; clients (Claude, Cursor, etc.) discover the
authorization server via protected-resource metadata, run the OAuth flow in
the user's browser, and attach bearer tokens to requests. The official
TypeScript SDK handles token validation plumbing; your job is:

1. Point the SDK at your auth server's issuer/JWKS.
2. Map a validated token to a `Principal` (one function, at the edge).
3. Keep scopes coarse and workflow-shaped, matching your tool curation.

Do not invent header-based custom auth for MCP — clients won't support it,
and it forks your credential model. For local/stdio MCP servers (running on
the user's machine), the server inherits the user's environment; resolve the
principal from the same stored credentials the CLI uses (below), so a local
MCP server and the CLI are the same identity.

## CLI: device-code login

Interactive login for a CLI must survive headless environments (SSH, remote
boxes, containers). The OAuth Device Authorization Grant (RFC 8628) is the
standard answer, and it's what users already know from `gh auth login`:

1. `acme login` requests a device code from the auth server.
2. CLI prints: `Visit https://acme.dev/device and enter code ABCD-1234` —
   and opens the browser only if a display exists.
3. User approves on any device; CLI polls the token endpoint until approved.
4. CLI stores the token + refresh token locally.

**Reference implementation: Better Auth** ships a `deviceAuthorization`
plugin (RFC 8628) — server side:

```ts
// auth server
import { betterAuth } from "better-auth";
import { deviceAuthorization } from "better-auth/plugins";

export const auth = betterAuth({
  plugins: [deviceAuthorization({ verificationUri: "/device" })],
});
```

and a `deviceAuthorizationClient` plugin for the CLI side (request code →
display → poll). `npx @better-auth/cli login` demonstrates the full flow
against their demo server if you want to feel the UX before building it. Any
OAuth provider supporting RFC 8628 (Auth0, Zitadel, etc.) works identically;
the flow is the contract, not the vendor.

## API keys

The non-interactive path for CI and agents — and the place to enforce
cross-surface sameness hard: **one API key is valid on CLI, MCP, and REST
alike.** An agent's credential must be surface-independent; "this key only
works on the API" recreates the drift problem inside auth.

- Use a recognizable prefix (`acme_…`) so keys are greppable in leaks and
  identifiable in logs.
- Accept via `Authorization: Bearer` on REST/MCP and via env var
  (`ACME_API_KEY`) on the CLI, which also makes the CLI trivially scriptable.
- Keys resolve to a `Principal` of kind `agent` with explicit scopes — same
  resolution function, same authorization path as user tokens.

Precedence on the CLI: explicit `--api-key` flag → env var → stored login
session. Print which identity is active in `acme whoami`.

## Token storage on the client

- Prefer the OS keychain where available; otherwise a `0600` file under
  `~/.config/<cli>/` (respect `XDG_CONFIG_HOME`).
- Store the refresh token and refresh silently; never make the user re-run
  `login` on expiry of a short-lived access token.
- `acme logout` deletes local credentials and revokes the refresh token
  server-side.
- Never write tokens into shell history, argv (visible in `ps`), or logs;
  env var and stored-file are the only two channels.
