# Building the surfaces

How to take a project from zero (or one) surfaces to CLI + MCP + REST over one
core. Examples are TypeScript (Bun-first); the shapes are portable to any
stack.

## Contents

- [Build order](#build-order)
- [The core](#the-core)
- [Hoisting: retrofitting a core into a single-surface project](#hoisting)
- [Adapter shape (all surfaces)](#adapter-shape)
- [REST adapter](#rest-adapter)
- [CLI adapter](#cli-adapter)
- [MCP adapter](#mcp-adapter)
- [The escape hatch: OpenAPI generators](#the-escape-hatch-openapi-generators)

## Build order

1. **Core first.** A callable service layer with typed operations. If the
   project already has one, confirm every operation you plan to expose goes
   through it.
2. **REST** (or an in-process API if you'll never publish HTTP). This is the
   foundation surface and usually the one the hosted product needs anyway.
3. **CLI**, paired with a skill file from day one.
4. **MCP**, when per-user auth / multi-tenancy / hosted agent access is
   needed.
5. **Add the conformance gate the moment surface #2 exists** — that is the
   moment drift becomes possible. Don't defer it to "when we have time";
   retrofitting a gate onto three drifted surfaces is far more work than
   growing it alongside the second one.

## The core

The core is a module of typed operations. At minimum (Tier 1), plain
functions with shared types:

```ts
// core/operations/create-invoice.ts
import { z } from "zod";

export const createInvoiceInput = z.object({
  customerId: z.string(),
  lines: z.array(z.object({ sku: z.string(), qty: z.number().int().min(1) })),
});

export async function createInvoice(
  principal: Principal,
  input: z.infer<typeof createInvoiceInput>,
): Promise<Envelope<Invoice>> { /* ... */ }
```

Two rules make everything downstream work:

- **Every operation takes a `principal` as its first argument.** Auth flows
  differ per surface; authorization must not. See `auth.md`.
- **Every operation returns the shared envelope** (below) — including on
  failure. Throwing transport-specific exceptions from the core forces each
  adapter to invent its own error mapping, which is anti-pattern #3.

```ts
// core/envelope.ts
export type Envelope<T> = {
  data: T | null;
  error: { code: string; message: string; issues?: unknown[] } | null;
};
```

Keep the envelope small and let it grow with real needs (request ids, audit
ids). What matters is that it is the *same* on every surface and that
`error.code` values are stable strings clients can switch on
(`INVOICE_NOT_FOUND`, not `"Error: not found"`).

At Tier 2, the zod input schemas become the generation source for CLI flags
and MCP tool schemas. At Tier 3, operations register into a typed registry
(name, input schema, handler, metadata) and the surfaces below are emitted by
pure functions over that registry instead of being hand-written.

## Hoisting

Retrofitting a core into a REST-only project whose logic lives in route
handlers:

1. Pick one route. Extract everything between "request parsed" and "response
   serialized" into a core function with the signature above.
2. Re-point the route handler at the core function. The handler should shrink
   to a few lines; if it doesn't, logic is still hiding in it.
3. Repeat per route, highest-traffic first. Don't build the CLI or MCP until
   the operations they need are hoisted — building a second surface on
   unhoisted logic means reimplementing it, which is anti-pattern #1.
4. Watch for the flagship-op trap: teams hoist the easy CRUD operations and
   leave the big central operation (the query engine, the search endpoint)
   inline "because it's complicated". That operation is precisely the one
   that must be hoisted — it's the one every surface needs.

## Adapter shape

Every adapter, on every surface, has the same four steps and nothing else:

```
resolve principal → parse args against the op's schema → call core → format envelope
```

An adapter file that grows beyond a trivial shell is a smell: growth means
logic is accumulating where only translation should live. If you find
yourself writing an `if` about business state in an adapter, move it to the
core.

## REST adapter

Hono example (works on Bun, Node, Workers):

```ts
// surfaces/rest.ts
import { Hono } from "hono";
import { createInvoice, createInvoiceInput } from "../core/operations/create-invoice";
import { resolvePrincipal } from "../core/auth";

export const app = new Hono();

app.post("/invoices", async (c) => {
  const principal = await resolvePrincipal(c.req.header("authorization"));
  const parsed = createInvoiceInput.safeParse(await c.req.json());
  if (!parsed.success) {
    return c.json({ data: null, error: { code: "INVALID_INPUT", message: "Invalid input", issues: parsed.error.issues } }, 400);
  }
  const env = await createInvoice(principal, parsed.data);
  return c.json(env, env.error ? 422 : 200);
});
```

Note the HTTP status is advisory; the envelope body is the contract.

## CLI adapter

**Tech: Bun end-to-end.**

- Dev: Bun runs TypeScript directly — no build step, no ts-node.
- Ship: `bun build --compile` produces a single-file per-platform binary;
  users need neither Node nor Bun. This is what makes the install and
  self-update story in `cli-distribution.md` simple. Caveats: binaries are
  large (~50–90 MB, runtime embedded — fine for a dev tool) and rare native
  modules may not embed. If the CLI is tiny and its audience is guaranteed to
  have Node, plain npm distribution is acceptable at ladder step 1.
- Parser: **commander** (boring, stable) or **citty** (lighter, nicer
  subcommand ergonomics). The choice is deliberately low-stakes because the
  CLI layer is thin — at Tier 3 the command tree is generated and the parser
  is invisible.

**Output contract (what makes a CLI agent-grade):**

- `--json` on every command, emitting the **same envelope** REST returns.
  This is what makes cross-surface conformance testable.
- Human-readable format as the default; data on stdout, progress and logs on
  stderr; meaningful exit codes (0 success, 1 operation error, 2 usage
  error).
- On error in `--json` mode, print the envelope with its `error.code` —
  agents parse it exactly like an API response.

```ts
// surfaces/cli.ts
import { Command } from "commander";
import { createInvoice, createInvoiceInput } from "../core/operations/create-invoice";
import { principalFromStoredToken } from "../core/auth";

const program = new Command("acme");

program
  .command("invoice:create")
  .requiredOption("--customer-id <id>")
  .option("--line <sku:qty...>", "repeatable line item")
  .option("--json", "machine-readable output")
  .action(async (opts) => {
    const principal = await principalFromStoredToken();
    const parsed = createInvoiceInput.safeParse(toInput(opts));
    if (!parsed.success) { printEnvelope({ data: null, error: { code: "INVALID_INPUT", message: "Invalid input", issues: parsed.error.issues } }, opts); process.exitCode = 2; return; }
    const env = await createInvoice(principal, parsed.data);
    printEnvelope(env, opts);
    if (env.error) process.exitCode = 1;
  });
```

**Ship a skill file with the CLI.** A `SKILL.md` (or equivalent agent doc)
describing usage patterns, common workflows, and the `--json` contract.
Community evidence is unambiguous: a CLI plus a good skill file outperforms a
bloated MCP server, but a bare CLI with only `--help` underperforms both. At
Tier 2+, generate this doc from the same schemas as everything else.

**Local vs remote:** if the operation needs server-side resources (a
warehouse connection, secrets), the CLI calls the REST surface over HTTP
rather than importing the core — a thin client cannot drift because it has no
local implementation. If everything is local, the CLI imports the core
directly. Do not mix modes per subcommand without a clear rule; a CLI where
some commands hit HTTP and others hit the database directly has two auth
paths and two failure modes.

## MCP adapter

Use the **official TypeScript MCP SDK** (`@modelcontextprotocol/sdk`). Each
tool handler is the same four-step shell:

```ts
// surfaces/mcp.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createInvoice, createInvoiceInput } from "../core/operations/create-invoice";

const server = new McpServer({ name: "acme", version: VERSION });

server.registerTool("invoice_create",
  { description: "Create an invoice for a customer", inputSchema: createInvoiceInput.shape },
  async (input, extra) => {
    const principal = await principalFromMcpAuth(extra);
    const env = await createInvoice(principal, createInvoiceInput.parse(input));
    return { content: [{ type: "text", text: JSON.stringify(env) }], isError: !!env.error };
  });
```

**Tool design** (from Anthropic's writing-tools-for-agents guidance — this is
where hand-rolled MCP servers usually go wrong):

- **Consolidate around workflows, not endpoints.** Five CRUD endpoints often
  make one good `invoice_edit` tool with a discriminated-union input, not
  five tools. Tool count is a context cost every agent pays on connect.
- **Token-efficient responses**: pagination, truncation, and filtering with
  sensible defaults on anything that can return a lot of data. An MCP server
  that dumps tens of thousands of tokens of schema or results at init is the
  community's top complaint.
- **Namespace tools** (`invoice_create`, `invoice_list`) so agents can select
  among many tools reliably.
- Reuse the zod schemas from the core as tool input schemas — at Tier 2 this
  is automatic.

## The escape hatch: OpenAPI generators

If the project already maintains a high-quality OpenAPI spec, generators can
produce surfaces from it: Speakeasy and Stainless generate MCP servers (and
SDKs/CLIs) from OpenAPI; FastMCP converts FastAPI/OpenAPI apps directly.

This satisfies "one source of truth" — with a caveat the vendors themselves
document: **naive endpoint→tool mapping produces tool sprawl** (anti-pattern
#7). Budget curation time: select and merge endpoints into workflow-shaped
tools, rewrite descriptions for agents, and set response size limits. And the
conformance gate still applies — generated surfaces can still disagree if
generation configs drift, so test the surfaces, not the generator's promise.
