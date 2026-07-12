---
name: surface-equivalency
description: >
  Make a project expose the same functionality across CLI, MCP, and REST — one
  core, N projections, drift caught mechanically. Use this skill whenever a
  project needs agent access: "add an MCP server", "build a CLI for this",
  "expose this to agents", "should this be CLI or MCP?", or when surfaces
  already exist and misbehave: "keep CLI/MCP/REST in sync", "my MCP and CLI
  behave differently", "the API has features the CLI doesn't". Also use it for
  the operational half of shipping a CLI: distribution ("how do users install
  this?"), in-place upgrades ("self-update", "version check"), and auth for
  agent surfaces (OAuth for MCP, device-code login for CLI, API keys). Trigger
  even when the project has neither a CLI nor an MCP server yet — designing the
  first surface correctly is the cheapest moment to apply this skill.
---

# Surface Equivalency

A project that exposes functionality to humans and agents grows surfaces: a
REST API, a CLI, an MCP server. Built independently, they drift — operations
exist on one surface but not another, parameter models diverge, error
contracts fork, and the docs match only one of them. Drift is not a hygiene
problem; it makes agents fail in ways users can't debug ("works in the CLI but
not over MCP").

The fix is structural, not disciplinary: **one core, N projections**. Every
surface is a thin client of the same core; equivalence is enforced by a test
gate, not by review vigilance.

## Step 1: Triage — where is this project today?

Always start here. The path differs by starting point:

1. **Neither CLI nor MCP exists** (most common). Build greenfield: confirm or
   extract a callable core (service layer), then add surfaces in order —
   REST/core API → CLI (paired with a skill file) → MCP. Add the conformance
   gate the moment the *second* surface exists; that is when drift becomes
   possible. Read `references/building-the-surfaces.md`.
2. **One surface exists** — typically REST-only, with business logic welded
   into route handlers. Hoist logic into a core first, then add the missing
   surfaces as thin adapters. The hoisting refactor is covered in
   `references/building-the-surfaces.md`.
3. **Multiple surfaces exist and have drifted.** Audit: inventory operations ×
   surfaces, diff parameter and error shapes, then retrofit Tier 1 of the
   ladder below. The gate recipe is in `references/conformance-gate.md`.

## The doctrine

**Surfaces are clients, never implementations.** All business logic — the
operation itself, plus cross-cutting behavior like auth checks, audit, and
idempotency — lives in one core. An adapter's whole job is: resolve the
caller's identity → parse arguments against the operation's schema → call the
core → format the response. Business logic in an adapter is the root defect
this skill exists to prevent, because logic that lives in one adapter is, by
construction, absent from the others.

The test of a healthy architecture: "is feature X available over MCP?" must be
answerable by looking at one registry or one core module — never by reading
three codebases.

**Which surfaces, and when:**

- **REST / core API** is the foundation. Even if never published, an internal
  HTTP or in-process API is what the other surfaces ride on.
- **CLI** serves the inner loop — local dev and agent efficiency. Agents drive
  CLIs natively and cheaply (community benchmarks put CLI at a fraction of
  MCP's token cost per task). A CLI must ship with a skill file (SKILL.md
  describing usage patterns for agents); a bare CLI with `--help` alone is the
  documented failure mode.
- **MCP** earns its place when you need per-user OAuth, multi-tenancy, or
  hosted access — the things a local CLI structurally cannot provide.
- Products that agents consume want **both CLI and MCP — generated or derived
  from one source, never hand-maintained in parallel**.

## The maturity ladder

Adopt the highest tier the project can afford; never ship below Tier 1 once
two surfaces exist.

**Tier 1 — Shared core + conformance gate** (the retrofit-friendly minimum).
All surfaces call the same core functions. Adapters are thin, with a hard
no-logic rule. A conformance test in CI drives every operation through every
surface and asserts: same parameters accepted, same results returned, same
error shape on the same bad input. This tier requires no codegen and fits any
existing project.

**Tier 2 — Shared schema + codegen.** Define each operation's parameters and
errors once (zod or JSON Schema) and generate the per-surface forms: server
request models, CLI flags, MCP tool input schemas — and the docs, including
LLM-facing prompt docs. A parameter now cannot exist on REST but not on the
CLI, because both are projections of one definition.

**Tier 3 — Registry → generated surfaces.** A typed operation registry is the
single source of truth; each surface is emitted by one pure function over the
registry (`generateRestApp(registry)`, `generateCli(registry)`,
`generateMcpServer(registry)`). No hand-written per-operation route, command,
or tool files exist at all. Wire manifests (`openapi.json`,
`cli-reference.json`, `mcp-tools.json`) are committed and CI-diffed against a
fresh regeneration, so a stale manifest fails the build. Operations without a
test fixture are rejected before surfaces are generated: no fixture → doesn't
ship.

## Non-negotiables (every tier)

1. **Uniform response envelope.** Every call, on every surface, success or
   failure, returns the same envelope shape. Errors are *data* with a stable,
   machine-readable `error.code` — not transport exceptions. REST may set an
   HTTP status, but clients switch on `error.code`, never on the status,
   because the CLI and MCP have no status to switch on.
2. **Conformance gate in CI** — including one *negative* test that injects a
   deliberate divergence and asserts the gate catches it. A gate that has
   never failed is an untested gate. Recipe: `references/conformance-gate.md`.
3. **Live introspection.** Every surface can list the available operations
   (`GET /operations`, `<cli> ops list`, an MCP list tool), so disagreement is
   detectable at runtime, not only at build time.
4. **Docs are generated** from the source of truth, never hand-written per
   surface. Hand-written surface docs are drift with a publishing pipeline.
5. **Principal resolved at the edge, passed into the core.** Each surface
   resolves the caller's identity in its own way (OAuth, device-code session,
   API key) but hands the core an explicit principal argument, so
   authorization and audit behavior never varies by surface. Flows:
   `references/auth.md`.

## Named anti-patterns

All of these have been observed in production codebases. Reject them in
review; they are how equivalency dies.

| # | Anti-pattern | Why it kills equivalency |
|---|---|---|
| 1 | Flagship operation bypasses its own service layer — one surface delegates to the core, another reimplements the pipeline inline | Two implementations of the same operation diverge silently; only the delegating surface gets fixes |
| 2 | Hand-written per-surface parameter models | Capabilities drift (a filter exists on REST only); dead flags accumulate (a CLI flag parsed but never sent) |
| 3 | Two error-production paths | Two contracts — different field names, codes, singular vs plural — and published docs match only one surface |
| 4 | Version telemetry collected but never enforced | The server watches clients skew out of date and does nothing; see `references/cli-distribution.md` |
| 5 | Manual doc fan-out across channels | Every manually-synced mirror lags; automate the fan-out or the channels lie |
| 6 | CLI shipped without a skill file | Agents get raw `--help` archaeology; a CLI plus a good skill file outperforms a bloated MCP, but a bare CLI underperforms both |
| 7 | Naive OpenAPI endpoint→tool mapping | One MCP tool per endpoint produces tool sprawl and token bloat; curate tools around workflows, not endpoints |

## Reference files

Read the one that matches the task at hand; skim the others' headings so you
know what exists.

- `references/building-the-surfaces.md` — greenfield build order, the hoisting
  refactor, thin-adapter shapes per surface, CLI/MCP tech choices (Bun,
  commander/citty, official MCP SDK), MCP tool-design guidance, and the
  OpenAPI-generator escape hatch.
- `references/conformance-gate.md` — the drift gate: test runner shape,
  normalization rules, the negative test, and the committed-manifest diff
  gate. TypeScript templates included.
- `references/auth.md` — one auth server, three flows: OAuth for MCP,
  device-code login for the CLI (Better Auth reference implementation),
  API keys shared across all surfaces.
- `references/cli-distribution.md` — install ladder (npm → `curl | sh` +
  compiled binaries → Homebrew), the four-part upgrade stack (self-update
  command with install-method detection, atomic replace, passive nudge,
  server-side min-version).
