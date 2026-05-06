---
name: metricly-consume
description: How to use Metricly's MCP correctly to answer analytical questions. Use when connected to a Metricly MCP server, when the user is asking analytical/business questions, or when an agent needs to query metrics, dimensions, or run analytical queries against Metricly.
---

# Using Metricly to answer analytical questions

You are connected to a Metricly MCP server. The data layer the user
cares about lives there. The conventions below come from real
production traces; departing from them produces misleading numbers.

## 1. The discovery pattern

For any analytical question, start with two calls:

1. `list_metrics` — every metric in the org, with descriptions.
2. `list_dimensions` — every groupable dimension, with descriptions.

Then call `query_metrics(...)`. Don't skip the catalog; metric
names are not self-describing, and "obvious" metrics like
`total_revenue` differ across orgs in unit, source, and standing
filter rules.

You can keep the catalog in conversation context across follow-up
questions. Drilldowns go straight to `query_metrics`; only re-call
`list_*` if the user pivots to a topic the catalog doesn't cover.

## 2. Read the description fields

The `description` on each metric and dimension is **authoritative**
— it's the source of truth for unit, computation, source rollup,
filter rules, and caveats. Read it. Do not paraphrase from the
metric name.

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

## 3. Apply standing filter rules from descriptions

If a metric's description says "pair with `status='paid'` to exclude
voided invoices", include that filter unless the user explicitly
asks for the unfiltered view. The author wrote it because querying
without it is a known footgun.

Don't argue. Don't substitute your own interpretation. The
description is closer to the warehouse than you are.

## 4. Prefer derived dimensions when descriptions point that way

Descriptions often steer you to a derived dimension over a raw one
(`customer_segment` over `customer.tier`, `event_segment` over
`event_type`). The derived version layers business logic the raw
field doesn't capture; the raw field is usually stale or
misleading.

Use the qualified name verbatim from `list_dimensions` (e.g.
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

## 7. Tool error recovery

When `query_metrics` returns an error with a `code` and
`suggestion` field, follow the suggestion. The error shapes are
deliberate:

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

When the error message is a qualified-dimension complaint (e.g.
`venue_name` was rejected, expecting
`pos_order_line__venue_name`), retry with the qualified name once.
Don't loop on the same error.

## 8. Multi-turn efficiency

After the catalog is in conversation context:

- Drilldowns ("show me the same broken down by region") go
  straight to `query_metrics`. No re-discovery needed.
- Comparison questions ("how does this compare to last year?")
  are a second `query_metrics` call with adjusted dates.
- Refinements ("can you exclude internal accounts?") add a
  filter; respect any standing rules from the metric description
  on top of the user's ad-hoc filter.

The catalog is only stale if the user pivots to a brand-new
analytical area; in that case, re-list.

## 9. The org's `business_context` document

When you connected, the MCP `instructions` blob included the org's
`business_context` (within a 2000-byte cap). It covers the things
that don't attach to any specific entity: what the org sells,
what's synced, what's NOT synced, and cross-cutting derivation
rules. Treat it as part of the same authoritative layer as metric
descriptions — apply it consistently, refuse honestly when it
says a system isn't synced.

That's the working agreement. Do this and the answers will be
right.
