---
name: metricly-author
description: Conventions for writing dbt YAML descriptions and the org's business_context doc. Use when editing dbt/models/**.yml, dbt/context/business_context.md, or any file that feeds Metricly's semantic layer or org context.
---

# Authoring Metricly's data-layer context

You are editing files that an analytical agent will read at query time.
Lazy descriptions silently degrade every query that touches the
affected entity. This skill exists so the conventions stay tight.

## 1. The contract

The descriptions on metrics, dimensions, and semantic models are
**authoritative**. Consumer agents trust them as the source of truth
for unit, computation, source rollup, applicable filter rules, and
known caveats. They are not commentary.

Two surfaces matter:

- **Per-entity descriptions** (dbt YAML) — ride directly in the tool
  responses to `list_metrics` / `list_dimensions`. No length cap.
  This is where 80% of "knowledge" should live.
- **Per-org `business_context`** — a single markdown document that
  covers cross-cutting facts. Hard cap: 2000 chars. Wired into the
  MCP `instructions` blob so external agents see it from turn 1.

If it attaches to one entity, put it on that entity. If it doesn't,
put it in `business_context`.

## 2. Metric description anatomy

A complete metric description has six ordered elements. Skip an
element only if it genuinely doesn't apply.

1. **Canonical sentence** — what this metric measures, in one line.
2. **Unit** — DKK, count, %, hours, customers, etc. Always explicit.
3. **Source rollup** — which systems / tables contribute.
4. **Caveats** — known bugs, temporal discontinuities, methodology
   changes. Date them.
5. **Standing filter rules** — "for B2B, pair with..."; "exclude
   internal test orders by setting `status != 'test'`".
6. **Derived-field pointers** — "use `event_segment`, not raw
   `event_type`".

### Good example

```yaml
- name: total_revenue
  description: |
    Total invoiced revenue from paid Stripe invoices.
    Unit: DKK (gross, before VAT).
    Source: stg_stripe__invoices, joined to dim_customer.
    Caveat: pre-2024-04-01 numbers exclude refunds (ETL bug
    fixed 2024-04-15; segment if comparing across that boundary).
    Filter rule: pair with status='paid' to exclude voided invoices.
    Use the derived `customer_segment`, not raw `customer.tier`.
```

### Bad example

```yaml
- name: total_revenue
  description: Total revenue.
```

The bad version forces every consumer agent to guess unit, source,
caveats, and rules. It also makes the metric look interchangeable
with similarly-named metrics in other systems.

## 3. Dimension description rules

For each dimension, document:

- **Allowed values** if it's an enum (`["smb", "midmarket", "enterprise"]`).
- **Derivation pointer** if it's computed (`derived from
  customer.tier in stg_customers`).
- **Use-this-not-that steering** when a raw field is more naive than
  the derived one (`prefer event_segment over event_type — segment
  layers business logic the raw field doesn't`).

```yaml
- name: customer_segment
  description: |
    SMB / Midmarket / Enterprise segmentation. Allowed values:
    smb, midmarket, enterprise.
    Derived in stg_customers from ARR + employee count, not the
    raw customer.tier field (tier hasn't been kept current).
```

## 4. Source / model description rules

For sources and semantic models, document:

- **Refresh cadence** (hourly, daily 06:00 UTC, etc.).
- **Format quirks** ("amount stored as cents in JSON payload, not
  dollars").
- **Coverage gaps** ("`customer_id` is 100% NULL pre-2023-06-01 —
  signups before then aren't tracked").

```yaml
sources:
  - name: stripe_events
    description: |
      Refreshed hourly from Stripe webhook ingest.
      `payload` is JSON; amount is in cents.
      Pre-2023-06-01: `customer_id` is NULL (signup tracking
      added then). Filter out NULL or use the post-2023 window
      for customer-level aggregations.
```

## 5. `business_context` anatomy

A single markdown document, ≤2000 chars (the MCP instructions cap).
Cover the cross-cutting facts that don't attach to any specific
entity.

Recommended structure:

```markdown
# <Org name>

## What we sell
- One sentence on the business model.
- Currency, fiscal calendar.

## Systems we sync from
- Stripe (billing) — refreshed hourly.
- HubSpot (CRM, contacts).
- Zendesk (support tickets).
- We do NOT sync personal staff mailboxes; email-correspondence
  questions cannot be answered.

## Cross-cutting derivations
- B2B vs B2C is `event_segment`, NOT raw `event_type`.
- `customer_segment` (smb/midmarket/enterprise) is derived in
  `stg_customers` — use it instead of `customer.tier`.

## Operational pointers
- Region: EU.
- dbt project lives in `dbt/` of the analytics repo.
- Per-metric specifics live in metric YAML descriptions.
```

What does NOT belong in `business_context`:
- Per-metric meaning, unit, formula — goes on the metric.
- Per-dimension derivation — goes on the dimension.
- Findings / analysis results — those aren't context.

## 6. The filing decision rule

| Type of fact | Goes in… |
|---|---|
| One metric's meaning, computation, unit | That metric's description |
| One metric's caveat, filter rule, derived-field pointer | Same |
| One dimension's allowed values, derivation, steering | That dimension's description |
| One source's refresh cadence, format quirk, NULL coverage | That source's description |
| Cross-cutting derivation rule | `business_context` |
| Org-level system inventory / coverage gap | `business_context` |
| Region, dbt layout, operational pointer | `business_context` |
| Findings, analysis, history | NOT in the context layer |
| Definition logic | dbt model SQL, not descriptions |

When unsure: put it in YAML, accept some duplication.

## 7. Edit surfaces for `business_context`

The canonical edit path is a markdown file in your dbt repo at
`dbt/context/business_context.md`, synced via:

```
metricly business-context import dbt/context/business_context.md
```

Other surfaces (in order of preference for emergencies):

- Web UI: Settings → Data → Business Context. Has a live byte
  counter against the 2000-char cap.
- MCP tool: `business_context_edit` (admin/owner). For agent-
  authored edits.
- CLI: `metricly business-context set` (stdin) or
  `metricly business-context edit` ($EDITOR).

**Convention:** edit the markdown file when possible. UI / MCP
edits should round-trip back into the dbt repo within a day.

## 8. Maintenance discipline

- **Reference rot.** When you rename a metric or dimension, search
  `business_context` and other entity descriptions for stale
  references. CI doesn't lint this yet.
- **Caveat sunset.** When a temporal-discontinuity bug gets fixed,
  remove the caveat — but only after enough time has passed that
  no useful query window starts before the fix.
- **Cross-PR review.** A description rewrite is a behavior change
  to every agent. Treat it like an API change in review.

That's the contract. Boring, dense, useful.
