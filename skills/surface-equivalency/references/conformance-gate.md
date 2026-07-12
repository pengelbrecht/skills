# The conformance gate

The mechanical answer to "how do we know the surfaces agree?" — a CI test
that drives every operation through every surface and asserts the responses
are identical. Discipline and review catch some drift; the gate catches all
of it, including the drift introduced by the well-meaning fix someone ships
at 23:40.

## Contents

- [What the gate asserts](#what-the-gate-asserts)
- [Runner shape](#runner-shape)
- [Normalization: mask only what is genuinely non-deterministic](#normalization)
- [The negative test](#the-negative-test)
- [Error-shape conformance](#error-shape-conformance)
- [The committed-manifest diff gate (Tier 3)](#the-committed-manifest-diff-gate)
- [Debugging a conformance failure](#debugging-a-conformance-failure)

## What the gate asserts

For every operation, with the same fixture input and the same starting state,
every surface returns the **same normalized envelope** — byte-for-byte after
JSON canonicalization. Not "roughly the same data": identical. Anything less
("both succeeded", "same keys exist") lets field-level drift through, and
field-level drift is exactly what breaks agents.

Each operation needs at least one **fixture**: input + seed state. At Tier 3,
make fixtures mandatory at the registry level — an operation without a
fixture is rejected before surfaces are even generated, because an untestable
operation is an unprovable one.

## Runner shape

Three rules make the runner trustworthy:

1. **Invoke each surface as a black box, in-process.** REST via the app's
   fetch handler (`app.request()` in Hono), CLI via its program object with
   captured stdout, MCP via the SDK's in-memory client/server transport pair.
   No network, no subprocesses — fast enough to run on every commit.
2. **Each surface gets its own fresh state** (own DB/seed) per fixture.
   Sharing state means surface A's writes contaminate surface B's reads and
   the comparison stops meaning anything.
3. **Compare envelopes, not transport artifacts.** Strip transport wrapping
   (HTTP status, MCP content framing) down to the envelope JSON before
   comparing.

```ts
// tests/conformance/runner.ts
import { describe, expect, test } from "bun:test";
import { fixtures } from "./fixtures";
import { makeRestSurface, makeCliSurface, makeMcpSurface } from "./surfaces";

// Each factory returns: (opName, input, principal) => Promise<Envelope<unknown>>
// backed by its OWN freshly-seeded state.

for (const fx of fixtures) {
  describe(`conformance: ${fx.op}`, () => {
    test("all surfaces return identical normalized envelopes", async () => {
      const [rest, cli, mcp] = await Promise.all([
        makeRestSurface(fx.seed), makeCliSurface(fx.seed), makeMcpSurface(fx.seed),
      ]);
      const envs = await Promise.all([
        rest(fx.op, fx.input, fx.principal),
        cli(fx.op, fx.input, fx.principal),
        mcp(fx.op, fx.input, fx.principal),
      ]);
      const [a, b, c] = envs.map((e) => canonicalize(normalize(e)));
      expect(b).toBe(a); // CLI === REST
      expect(c).toBe(a); // MCP === REST
    });
  });
}
```

`canonicalize` is a stable JSON stringify (sorted keys). The surface
factories are where per-surface translation lives — e.g. the CLI factory maps
`(op, input)` to argv and parses the `--json` stdout back into an envelope.
Writing those factories is most of the work, and it is one-time work.

## Normalization

Mask **only** genuinely non-deterministic fields — ids and timestamps — and
compare everything else literally:

```ts
const NONDETERMINISTIC_KEYS = new Set(["id", "createdAt", "updatedAt", "requestId"]);

function normalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) =>
      [k, NONDETERMINISTIC_KEYS.has(k) ? "<masked>" : normalize(v)]));
  }
  return value;
}
```

Prefer masking by key name or id-prefix convention (`inv_…`, `cust_…`) over
masking by value shape. Resist the temptation to widen the mask when a
conformance test fails — a failure on a "noisy" field is usually real drift
(one surface formats a date differently, one rounds a number). Every key you
mask is a field the gate no longer protects.

## The negative test

A gate that has never failed is untested. Prove the gate can catch drift by
injecting some, permanently, as a test:

```ts
test("gate detects an injected divergence", async () => {
  const rest = await makeRestSurface(seed);
  const drifted = wrapSurface(rest, (env) => ({ ...env, data: { ...env.data, DRIFT: true } }));
  const [a, b] = [canonicalize(normalize(await rest(op, input, p))),
                  canonicalize(normalize(await drifted(op, input, p)))];
  expect(a).not.toBe(b);
});
```

This looks trivial; it exists to catch the failure mode where normalization
grows so aggressive (masking whole subtrees, comparing key sets instead of
values) that the gate silently stops discriminating.

## Error-shape conformance

Drift lives disproportionately in error paths, because happy paths get tested
and error paths get improvised per surface. For each operation include at
least one **failing fixture** (bad input, missing resource) and assert the
error envelopes match across surfaces exactly like success envelopes: same
`error.code`, same message, same structure. Two error contracts — `code` on
one surface, `error_code` on another, `suggestion` vs `suggestions[]` — is
the classic real-world drift, and published docs then match only one surface.

## The committed-manifest diff gate

At Tier 3 (generated surfaces), commit the generated wire manifests —
`openapi.json`, `cli-reference.json`, `mcp-tools.json` — and make CI fail if
regeneration produces a diff:

```jsonc
// package.json
"scripts": {
  "generate:manifests": "bun run scripts/generate-manifests.ts",
  "ci": "bun run generate:manifests && git diff --exit-code -- openapi.json cli-reference.json mcp-tools.json && bun test"
}
```

This makes surface changes *reviewable*: a PR that changes an operation shows
the manifest deltas for all three surfaces side by side, and a PR that
changes generation without regenerating fails.

## Debugging a conformance failure

When surfaces disagree, the bug is in an adapter seam, not (usually) the
core — both surfaces ran the same core function. Procedure:

1. Reproduce on the gate; save both envelopes to files.
2. Diff the normalized envelopes. The differing field names the seam: a
   missing field means one adapter drops it in formatting; a differently-typed
   field means one adapter parses input differently (string vs number from
   CLI flags is common); a different `error.code` means one surface produces
   errors before reaching the core (its own validation) — move that
   validation into the core or make it identical.
3. Fix in the adapter (or hoist into the core), rerun the gate.
