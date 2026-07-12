# Design: `surface-equivalency` skill

**Date:** 2026-07-12
**Status:** Approved pending user review
**Deliverable:** A distributable skill at `skills/surface-equivalency/` (installed via
`npx skills add`) that helps a project expose the same functionality across CLI, MCP,
and REST — including projects that have neither CLI nor MCP yet.

## Problem

Projects that expose functionality to agents and humans grow surfaces (CLI, MCP
server, REST API) independently. Without structure, the surfaces drift: operations
exist on one surface but not another, parameter models diverge, error contracts fork,
and published docs match only one surface. Metricly is the documented cautionary tale
(flagship `/query` op bypasses its own service layer; four hand-written param models;
two error contracts). Canonify is the documented gold standard (surfaces generated
from one typed registry; conformance gate asserts byte-identical envelopes).

The skill teaches "surface equivalency": one core, N projections, drift caught
mechanically.

## Research inputs

- **Canonify deep-dive** — registry → generated surfaces → one runtime → uniform
  envelope → conformance gate (`tests/conformance/runner.ts`), "no fixture → doesn't
  ship", CI-diffed committed manifests.
- **Metricly deep-dive** — anti-patterns: core bypass, per-surface param models,
  error-shape drift, version telemetry without enforcement, manual doc fan-out.
  Positive: schema→codegen for dashboards (incl. generated LLM prompt docs);
  single-source instructions served over HTTP.
- **Sibling sweep** — AgentPreso (npm + compiled binaries, `update` command with
  install-method detection, shared API keys across CLI/MCP), Ticks (Go self-update,
  brew detection, throttled passive check), OpenAgents (portable-node install),
  Dottie (shared contract package).
- **Community (last30days, 2026-06/07)** — hybrid consensus: CLI for inner loop
  (token-efficient; benchmark 1.4–8.8k tokens/task vs MCP 32–82k), MCP for
  OAuth/multi-tenant; "design quality is protocol-agnostic"; OpenAPI→MCP generator
  ecosystem (Speakeasy, Stainless, FastMCP); CLI-without-skill-file is the named
  failure mode; Anthropic writing-tools-for-agents guidance.

## Skill identity

- **Name:** `surface-equivalency`
- **Location:** `skills/surface-equivalency/` in this repo (distributable, not
  `.claude/` config — per decision 0001).
- **Triggers (description):** "add an MCP server", "build a CLI for this project",
  "expose this to agents", "keep CLI/MCP/REST in sync", "my MCP and CLI behave
  differently", "agent access to my app". Must trigger for projects with zero
  surfaces today (the most common entry).

## Structure

```
skills/surface-equivalency/
  SKILL.md                          # triage + doctrine + ladder (lean)
  references/
    conformance-gate.md             # the drift gate recipe + TS templates
    building-the-surfaces.md        # greenfield path: core → REST → CLI → MCP
    auth.md                         # one auth server, per-surface flows
    cli-distribution.md             # install / upgrade-in-place stack
```

TS-first examples (Bun, Hono-friendly); principles stated stack-agnostically.

## SKILL.md content

### 1. Triage (first step, always)

- **Neither CLI nor MCP** → greenfield path (`building-the-surfaces.md`): confirm or
  extract a callable core (service layer), then build surfaces in order
  REST/core-API → CLI (+ its SKILL.md) → MCP. Add the conformance gate as soon as the
  **second** surface exists.
- **One surface exists** (typically REST-only with logic welded into route handlers)
  → hoist logic into a core, add missing surfaces as thin adapters.
- **Multiple surfaces, drifted** → audit path: inventory ops × surfaces, diff
  param/error shapes, retrofit Tier 1.

### 2. Core doctrine

- **One core, N projections.** Surfaces are clients of one runtime/service layer.
  Business logic in an adapter is the root defect. "Is feature X on MCP?" must be
  answerable from one registry, not three codebases.
- **Decision framework:** REST/core API is the foundation; CLI for inner-loop and
  agent efficiency (always paired with a skill file); MCP when you need per-user
  OAuth, multi-tenancy, or hosted access.

### 3. Maturity ladder

- **Tier 1 — Shared core + gate** (retrofit-friendly minimum): all surfaces call the
  same core functions; adapters are thin with a hard no-logic rule; conformance test
  in CI drives every operation through every surface asserting same accepted params,
  same results, same error shape.
- **Tier 2 — Shared schema + codegen:** op params/errors defined once (zod / JSON
  Schema), generating server models, CLI flags, MCP tool schemas, and docs —
  including LLM-facing prompt docs (Metricly dashboard codegen proves the pattern).
- **Tier 3 — Registry → generated surfaces** (Canonify-grade): typed operation
  registry; surfaces emitted by pure functions (one file per surface); uniform
  envelope; committed wire manifests (`openapi.json`, `cli-reference.json`,
  `mcp-tools.json`) CI-diffed against regeneration; "no test fixture → operation
  doesn't ship".

### 4. Non-negotiables (every tier)

1. Uniform response envelope with machine-readable `error.code`; errors are data,
   not transport exceptions; clients never switch on HTTP status.
2. Conformance gate in CI, including one **negative** drift test proving the gate
   catches an injected divergence.
3. Live introspection: list operations on every surface.
4. Docs generated from the source of truth, never hand-written per surface.
5. Principal (caller identity) resolved at the auth edge, passed explicitly into the
   core — governance/audit never varies by surface.

### 5. Named anti-patterns (all observed in the wild)

1. Flagship op bypasses its own service layer (one surface delegates, another
   reimplements).
2. Hand-written per-surface param models → capability drift, dead flags.
3. Two error-production paths → two contracts; docs match only one surface.
4. Version telemetry collected but never enforced.
5. Manual doc fan-out across channels.
6. CLI shipped without a skill file.
7. Naive OpenAPI endpoint→tool mapping without curation (tool sprawl).

## References content

### `conformance-gate.md`

- Runner shape: build each surface as a black box with its **own fresh state**;
  invoke in-process (REST via `app.request()` / fetch handler, CLI via its program
  object, MCP via in-memory client from the official SDK).
- Normalize **only** non-deterministic fields (ids, timestamps), then byte-compare
  envelopes across surfaces per operation fixture.
- Negative test: inject a deliberate divergence, assert the gate fails.
- Committed-manifest diff gate: `generate && git diff --exit-code`.
- TS templates adapted from the Canonify pattern (genericized: no
  ObjectType/ActionType vocabulary, no Canonify envelope fields).

### `building-the-surfaces.md`

- Greenfield build order and the hoisting refactor for single-surface projects.
- Thin-adapter shape per surface (parse principal → parse args against schema → call
  core → format envelope). Adapter growth is a smell.
- **CLI tech:** Bun end-to-end (runs TS directly in dev; `bun build --compile` for
  per-platform single-file binaries). Parser: commander or citty — deliberately
  low-stakes because the layer is thin. `--json` flag on every command emitting the
  same envelope as REST/MCP; data on stdout, progress on stderr; exit codes; SKILL.md
  shipped alongside.
- **MCP tech:** official TypeScript MCP SDK; tool design per Anthropic
  writing-tools-for-agents (consolidate around workflows not endpoints;
  token-efficient responses with pagination/truncation defaults; namespacing).
- **Escape hatch:** OpenAPI→MCP generators (Speakeasy, Stainless, FastMCP) with the
  curation caveat.

### `auth.md`

- One auth server, three flows resolving to one principal:
  - **MCP:** OAuth per the MCP authorization spec.
  - **CLI:** `login` via OAuth device-code flow (RFC 8628) — Better Auth
    `device-authorization` plugin as reference implementation; prints URL + code,
    opens browser when a display exists (headless/SSH-safe); polls token endpoint.
  - **REST:** bearer tokens.
- Token storage: OS keychain where available, else `0600` file under
  `~/.config/<cli>/`; silent refresh.
- Non-interactive fallback: API keys via env var, **same keys valid on CLI, MCP, and
  REST** (AgentPreso pattern) so an agent credential is surface-independent.

### `cli-distribution.md`

- **Install ladder:** (1) npm/`npx` day one; (2) `curl | sh` + GitHub Releases
  binaries as the canonical path once compiled (Bun); (3) Homebrew tap when mature.
  npm stays as secondary channel (platform binaries as optional deps, pnpm v12
  pattern).
- **Upgrade stack (one feature, four parts):**
  1. `<cli> update` self-update: detect install method — brew → refuse and print
     `brew upgrade …`; npm global → delegate to `npm i -g`; compiled binary → fetch
     latest, download platform binary, **atomic rename over self**.
  2. Passive check: ≤1/24h, cached in `~/.config/<cli>/update-cache.json`,
     non-blocking, nudge at start of next command.
  3. Version header on every server call + server-side min-version enforcement
     (warn, then reject).
  4. Never auto-update silently.

## Out of scope

- Shipping executable scaffolding/scripts (guidance + copy-paste snippets only, per
  user choice of "reference docs").
- An automated audit/grading script (may be a follow-up).
- Non-TS reference implementations.

## Verification

- skill-creator conventions check (frontmatter, description triggering, lean
  SKILL.md with references).
- Self-consistency read of SKILL.md vs references.
- Confirm Better Auth device-authorization plugin API before writing auth.md
  examples (web check during implementation).
