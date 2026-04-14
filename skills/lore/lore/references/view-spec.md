# ViewSpec Reference

ViewSpecs are JSON objects that define how data is displayed and interacted with in Lore. Agents create ViewSpecs via the CLI or API, and Lore validates and renders them automatically.

## Creating views

```bash
# Auto-generate a list view from table schema
lore views create --name "Customers" --for customers

# Auto-generate a record view with related sections (detects FKs)
lore views create --name "Customer Detail" --for customers --type record

# Create from a custom spec file
lore views create --name "Pipeline" --for deals --spec ./pipeline.json

# Other auto-generated types
lore views create --name "Deal Board" --for deals --type board
lore views create --name "Dashboard" --for deals --type dashboard
```

The `--type record` hint auto-detects reverse foreign keys and generates related sections. For example, if `key_results.objective_id` references `objectives.id`, the objectives record view will include a "Key Results" related section.

Record-type views don't appear in the sidebar nav (they need a `recordId` context). List views auto-register in the sidebar. When a user clicks a row in a list view, Lore checks for a matching record-type view and navigates to it automatically.

## View types

| Type | Purpose | Key fields |
|------|---------|------------|
| `list` | Table of rows | `columns`, `sort`, `filters` |
| `record` | Single record detail with related sections | `sections` |
| `board` | Kanban board | `columns`, `groupBy` |
| `dashboard` | KPI widgets + charts | `widgets` |
| `composite` | Multi-section layout | `compositeSections` |
| `activity_feed` | Timeline of events | — |

## Core ViewSpec fields

```json
{
  "version": 1,
  "type": "list",
  "baseTable": "deals",
  "query": "SELECT * FROM deals WHERE stage != 'lost'",
  "columns": [...],
  "filters": [...],
  "sort": { "key": "created_at", "direction": "desc" },
  "groupBy": "stage",
  "sections": [...],
  "widgets": [...],
  "actions": [...],
  "toolbar": ["export-csv", "leads-only"]
}
```

- `query` overrides the default `SELECT * FROM {baseTable}`. Supports JOINs, WHERE, ORDER BY.
- `groupBy` is required for board views (the column to group cards by).
- `sections` is used by record views. `widgets` is used by dashboard views.
- `actions` and `toolbar` are available on all view types.

## Columns

```json
{
  "key": "amount",
  "label": "Amount",
  "type": "currency",
  "sortable": true,
  "align": "right",
  "required": true
}
```

| Column type | Renders as |
|------------|------------|
| `text` | Plain text |
| `number` | Formatted number |
| `currency` | `$1,234.56` |
| `date` | `Apr 9, 2026` |
| `datetime` | `Apr 9, 2026, 05:42 AM` |
| `boolean` | Toggleable `✓` / `○` in related sections |
| `badge` | Colored pill (cycleable in related sections if `options` defined) |
| `link` | Clickable URL |
| `enum` | Status badge |
| `reference` | FK link to another record |
| `long_text` | Multi-line text |

For `reference` columns:
```json
{
  "key": "customer_id",
  "type": "reference",
  "referencedTable": "customers",
  "referencedDisplayColumn": "name"
}
```

For `enum`/`badge` columns with defined options:
```json
{
  "key": "status",
  "type": "badge",
  "options": [
    { "value": "on_track", "label": "On Track" },
    { "value": "at_risk", "label": "At Risk" },
    { "value": "done", "label": "Done" }
  ]
}
```

## Sections (record views)

Record views use `sections` to lay out content:

### Fields section

```json
{
  "type": "fields",
  "label": "Details",
  "fields": ["title", "description", "owner", "status"],
  "computed": [
    {
      "key": "kr_count",
      "label": "Key Results",
      "sql": "COUNT(*)",
      "table": "key_results",
      "foreignKey": "objective_id",
      "format": "number"
    },
    {
      "key": "progress",
      "label": "Avg Progress",
      "sql": "AVG(current_value * 1.0 / NULLIF(target_value, 0))",
      "table": "key_results",
      "foreignKey": "objective_id",
      "format": "percent"
    }
  ]
}
```

Computed fields run SQL aggregates (`SUM`, `COUNT`, `AVG`) against a related table and display below the regular fields. Formats: `number`, `currency`, `percent`.

### Related section (1:many)

```json
{
  "type": "related",
  "label": "Key Results",
  "table": "key_results",
  "foreignKey": "objective_id",
  "columns": [
    { "key": "title", "label": "Key Result", "type": "text" },
    { "key": "current_value", "label": "Current", "type": "number" },
    { "key": "target_value", "label": "Target", "type": "number" },
    { "key": "status", "label": "Status", "type": "badge" },
    { "key": "completed", "label": "Done", "type": "boolean" }
  ],
  "sort": { "key": "created_at", "direction": "asc" },
  "allowAdd": true,
  "allowEdit": true,
  "allowDelete": true,
  "addDefaults": { "status": "on_track" }
}
```

Related sections:
- Auto-fetch: `SELECT * FROM {table} WHERE {foreignKey} = {parentId}`
- Show count in header: "Key Results (3)"
- Empty state: "No key results yet." with "+ Add" button
- Inline add form: FK auto-populated, fields inferred from PRAGMA
- Boolean columns render as toggleable `✓`/`○`
- Row click navigates to the record's detail page
- Auto-detected by `--type record` via reverse FK introspection

## Actions

Actions surface in the Cmd+K command palette and optionally as toolbar buttons.

```json
{
  "actions": [
    { "id": "export", "label": "Export CSV", "icon": "download",
      "keywords": ["export"], "action": { "type": "query", "download": "csv" } },
    { "id": "leads", "label": "Leads only", "icon": "filter",
      "action": { "type": "filter", "key": "stage", "operator": "eq", "value": "lead", "toggle": true } },
    { "id": "big", "label": "Big deals (>$50k)", "icon": "dollar-sign",
      "action": { "type": "filter", "sql": "amount > 5000000", "toggle": true } }
  ],
  "toolbar": ["export", "leads", "big"]
}
```

`toolbar` lists action IDs to render as buttons above the view. Actions not in `toolbar` are still searchable via Cmd+K.

### Action types

| Type | Fields | Cmd+K? | Toolbar? | What it does |
|------|--------|--------|----------|-------------|
| `navigate` | `target` | Yes | Yes | Go to `"app-slug"` or `"app-slug:View Name"` |
| `mutate` | `sql`, `params?`, `confirm?` | Yes | Yes | Run SQL mutation. Inline confirm if `confirm` set. |
| `query` | `sql?`, `download` (`csv`\|`json`), `filename?` | Yes | Yes | Run query + download result. Omit `sql` to export view's own data. |
| `filter` (simple) | `key`, `operator`, `value`, `toggle?` | No | Yes | Client-side column filter. Toggle on/off. |
| `filter` (SQL) | `sql`, `toggle?` | No | Yes | Server-side WHERE clause. Re-fetches with appended SQL. |
| `sort` | `key`, `direction` | No | Yes | Client-side sort override. |
| `open` | `url` | Yes | Yes | Open external URL in new tab. |

Filter operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `in`.

Navigate target format: `"crm"` (app) or `"crm:Pipeline"` (view within app). Resolved at runtime by name.

Template variables in `mutate` and `query` SQL: `{recordId}` (current record ID), `{baseTable}` (view's base table).

## Widgets (dashboard views)

```json
{
  "type": "kpi",
  "label": "Total Revenue",
  "query": "SELECT SUM(amount) as value FROM deals WHERE stage = 'closed_won'",
  "colSpan": 1
}
```

Widget types: `kpi`, `line_chart`, `bar_chart`.

## Complete examples

### OKR Objective Detail

```json
{
  "version": 1,
  "type": "record",
  "baseTable": "objectives",
  "sections": [
    {
      "type": "fields",
      "label": "Details",
      "fields": ["title", "description", "owner", "quarter", "status"],
      "computed": [
        { "key": "kr_count", "label": "Key Results", "sql": "COUNT(*)", "table": "key_results", "foreignKey": "objective_id", "format": "number" },
        { "key": "progress", "label": "Avg Progress", "sql": "AVG(current_value * 1.0 / NULLIF(target_value, 0))", "table": "key_results", "foreignKey": "objective_id", "format": "percent" }
      ]
    },
    {
      "type": "related",
      "label": "Key Results",
      "table": "key_results",
      "foreignKey": "objective_id",
      "columns": [
        { "key": "title", "label": "Key Result", "type": "text" },
        { "key": "current_value", "label": "Current", "type": "number" },
        { "key": "target_value", "label": "Target", "type": "number" },
        { "key": "unit", "label": "Unit", "type": "text" },
        { "key": "status", "label": "Status", "type": "badge" },
        { "key": "completed", "label": "Done", "type": "boolean" }
      ],
      "allowAdd": true
    }
  ]
}
```

### Deals list with toolbar

```json
{
  "version": 1,
  "type": "list",
  "baseTable": "deals",
  "columns": [
    { "key": "title", "label": "Deal", "type": "text" },
    { "key": "amount", "label": "Amount", "type": "currency" },
    { "key": "stage", "label": "Stage", "type": "badge" }
  ],
  "sort": { "key": "amount", "direction": "desc" },
  "actions": [
    { "id": "export", "label": "Export CSV", "icon": "download", "action": { "type": "query", "download": "csv" } },
    { "id": "leads", "label": "Leads only", "icon": "filter", "action": { "type": "filter", "key": "stage", "operator": "eq", "value": "lead", "toggle": true } },
    { "id": "big", "label": "Big deals", "icon": "dollar-sign", "action": { "type": "filter", "sql": "amount > 5000000", "toggle": true } },
    { "id": "pipeline", "label": "Pipeline", "icon": "columns", "action": { "type": "navigate", "target": "crm:Pipeline" } }
  ],
  "toolbar": ["export", "leads", "big"]
}
```

## Validation

The server validates ViewSpecs on `POST /v1/views` and `PUT /v1/views/:id`. Validation rules:
- `version`, `type`, `baseTable` required
- `columns` required for `list` and `board` views
- `groupBy` required for `board` views
- `widgets` required for `dashboard` views
- `sections[].type` must be `fields`, `related`, or `custom`
- Related sections require `table` and `foreignKey`
- Action IDs must be unique within the view
- Action types must be valid (`navigate`, `mutate`, `query`, `filter`, `sort`, `open`)
- Each action type has required fields (e.g. `navigate` requires `target`)
- `toolbar` entries must reference existing action IDs
- Filter actions require either `sql` or `key` + `operator`

## Auto-generation

```bash
# Generate on the fly (not saved)
GET /v1/views/generate?table=customers&hint=record

# hint values: table (default), board, dashboard, chart, record
```

The `record` hint:
- Introspects all tables for reverse FKs pointing to the target table
- Generates a `fields` section with all non-system columns
- Generates a `related` section for each child table with FK detection
- Detects boolean-like INTEGER columns by name (`completed`, `is_*`, `has_*`, etc.)
