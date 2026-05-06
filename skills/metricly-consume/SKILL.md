---
name: metricly-consume
description: How to query Metricly correctly to answer analytical questions. Use when the user is asking analytical/business questions, when an agent is connected to a Metricly MCP server, when running `metricly query ...` from the terminal, or when scripting against Metricly's REST API. Covers all three surfaces (MCP, CLI, REST) — same principles, different invocations.
---

# Querying Metricly to answer analytical questions

You are querying Metricly. Three surfaces are available — pick the
one the caller is using:

- **MCP** — agent connected to a Metricly MCP server (Claude
  Desktop, Claude Code via stdio, etc.). Tool calls.
- **CLI** — `metricly` from the terminal. Shell commands.
- **REST** — direct HTTP. Scripts, integrations.

The principles below are surface-agnostic. The conventions come
from real production traces; departing from them produces
misleading numbers.

## Surface cheatsheet

| Operation                  | MCP tool                              | CLI                                                     | REST                                                                  |
|---|---|---|---|
| List metrics               | `list_metrics()`                       | `metricly metrics list`                                 | `GET /api/semantic-layer/metrics`                                     |
| List dimensions            | `list_dimensions()`                    | `metricly dimensions list`                              | `GET /api/semantic-layer/dimensions`                                  |
| Explain one metric         | `explain_metric(metric_name)`          | `metricly metrics show <name>`                          | `GET /api/semantic-layer/metrics/<name>`                              |
| Query                      | `query_metrics(params)`                | `metricly query -m <name> [-d ...] [-g month] ...`      | `POST /query` with JSON body                                          |
| Read business_context      | `metricly://context` resource          | `metricly business-context get`                         | `GET /api/context`                                                    |
| Check business_context size| `business_context_edit show_size`      | `metricly business-context size`                        | (no dedicated route — use `GET /api/context` and measure)             |
| Org's published skill      | (this skill, served via SKILL.md)      | `metricly skill instructions consume`                   | `GET /api/v1/skill/consume/instructions`                              |

All three surfaces hit the same backend, semantic layer, and
authorisation rules. The org's `business_context` document and
each metric's `description` are the same bytes in all three.

## 1. The discovery pattern

For any analytical question, start with two calls:

1. **List metrics** — every metric in the org, with descriptions.
2. **List dimensions** — every groupable dimension, with descriptions.

Then run the actual query. Don't skip the catalog; metric names
are not self-describing, and "obvious" metrics like
`total_revenue` differ across orgs in unit, source, and standing
filter rules.

You can keep the catalog in conversation context (MCP) or in a
shell variable / scripting state (CLI / REST) across follow-up
questions. Drilldowns go straight to query; only re-list if the
user pivots to a topic the catalog doesn't cover.

## 2. Read the description fields

The `description` on each metric and dimension is **authoritative**
— it's the source of truth for unit, computation, source rollup,
filter rules, and caveats. Read it. Do not paraphrase from the
metric name. Don't infer from the metric name what unit it's in.

What the description tells you:

- **Unit** — DKK, count, %, hours. State it back to the user
  explicitly in the answer.
- **Source rollup** — which systems contribute. If the user asks
  "how much revenue from Stripe?" and the metric rolls up Stripe
  + Shopify, say so.
- **Caveats** — temporal discontinuities, methodology changes,
  bug-fix dates. Honor them (see §5).
- **Standing filter rules** — "for B2B, pair with…". Apply them
  unless the user explicitly overrides.
- **Derived-field pointers** — "use `event_segment`, not raw
  `event_type`". Follow them (see §4).

The descriptions are byte-identical across MCP, CLI, and REST —
authored once in dbt YAML, served everywhere.

## 3. Apply standing filter rules from descriptions

If a metric's description says "pair with `status='paid'` to exclude
voided invoices", include that filter unless the user explicitly
asks for the unfiltered view. The author wrote it because querying
without it is a known footgun.

- **MCP**: pass through `query_metrics(filter=...)` (where supported)
  or call out the rule in your answer when the surface can't apply
  it programmatically.
- **CLI**: `metricly query` doesn't yet expose ad-hoc filters; if a
  filter rule applies, mention it in your answer to the user.
- **REST**: include the filter in the POST body to `/query`.

Don't argue. Don't substitute your own interpretation. The
description is closer to the warehouse than you are.

## 4. Prefer derived dimensions when descriptions point that way

Descriptions often steer you to a derived dimension over a raw one
(`customer_segment` over `customer.tier`, `event_segment` over
`event_type`). The derived version layers business logic the raw
field doesn't capture; the raw field is usually stale or
misleading.

Use the qualified name verbatim from the dimensions catalog (e.g.
`pos_order_line__venue_name`, not `venue_name`). The prefix names
the semantic model the dimension lives on.

## 5. Honor temporal discontinuities

When a metric description warns "pre-X date is unreliable" or "ETL
bug fixed Y date", segment your query and tell the user about the
discontinuity in your answer.

Example: if a description says "pre-2024-04-01 numbers exclude
refunds; ETL bug fixed 2024-04-15", and the user asks for the
year-over-year trend across that boundary, run two queries
(before/after) and call out the methodology change rather than
silently quoting a single misleading trend.

This applies regardless of surface — same warehouse, same
boundaries.

## 6. Refuse hopeless queries honestly

If a question requires data the catalog doesn't expose, or the
`business_context` warns the relevant system isn't synced, say so.
Don't run a query against the closest-named metric and report a
misleading number.

Examples of honest refusals:

- "I can't answer how many emails went out — `business_context`
  notes the org doesn't sync staff mailboxes."
- "I can't answer attribution by paid-search keyword — there's no
  metric or dimension in the catalog that captures search keyword."

## 7. Tool / response error recovery

Errors come back with a `code` and a `suggestion` (the canonical
spec name; older paths still expose `hint` as an alias). Follow
the suggestion.

Codes you'll see:

- `METRIC_NOT_FOUND` — suggestion lists available metric names.
  Don't retry with the same name; pick from the suggestion or ask
  the user what they meant.
- `QUICK_METRIC_NOT_FOUND` — same pattern for `qm:` prefixed
  derived metrics.
- `NO_DATA` — the metric exists but the date range / filter
  combination returned nothing. Tell the user; don't fabricate a
  zero.
- `NO_BASE_METRICS` — quick metric expression has no dependencies
  to resolve. Almost always a config bug; surface it.
- `EXCEEDS_INSTRUCTIONS_CAP` — `business_context_edit` write
  rejected because the new content would exceed the 2000-byte
  UTF-8 cap. The error includes `current_bytes` and `cap_bytes`;
  trim the content, don't loop.

When the error message is a qualified-dimension complaint (e.g.
`venue_name` was rejected, expecting
`pos_order_line__venue_name`), retry with the qualified name once.
Don't loop on the same error.

Surface differences:

- **MCP**: errors come back as a `{error, code, suggestion}` dict
  in the tool response. `suggestion` is the canonical field;
  `hint` mirrors it for back-compat.
- **CLI**: the error prints with a friendly "✗ Error: …" prefix
  and a hint line. Exit code is 1.
- **REST**: HTTP 4xx/5xx with JSON body
  `{"detail": {"message", "code", "suggestion", ...}}`.

## 8. Multi-turn / multi-call efficiency

After the catalog is loaded once:

- Drilldowns ("show me the same broken down by region") go
  straight to the query call. No re-discovery needed.
- Comparison questions ("how does this compare to last year?")
  are a second query call with adjusted dates.
- Refinements ("can you exclude internal accounts?") add a
  filter; respect any standing rules from the metric description
  on top of the user's ad-hoc filter.

The catalog is only stale if the user pivots to a brand-new
analytical area; in that case, re-list.

## 9. The org's `business_context` document

Cross-cutting org orientation lives in `business_context` — what
the org sells, what's synced, what's NOT synced, cross-cutting
derivation rules. Hard cap: 2000 UTF-8 bytes.

How it reaches you:

- **MCP**: the `business_context` is appended to the server's
  `instructions` blob at `initialize` (within Claude Code's 2KB
  total cap). You see it from turn 1 — no fetch needed. Apply it
  consistently; refuse honestly when it says a system isn't
  synced.
- **CLI**: `metricly business-context get` prints it.
  `metricly business-context size` shows the byte budget.
- **REST**: `GET /api/context` returns `{"content": "..."}`.

Treat `business_context` as part of the same authoritative layer
as metric descriptions. Same provenance (dbt repo via the
manifest workflow), same trust level.

That's the working agreement. Same principles, three surfaces —
do this and the answers will be right.
