---
name: lore
description: Connect to a Lore backend — query data, mutate with governance, propose schema changes, contribute knowledge. Use when an agent needs to interact with a Lore instance for reading/writing data, proposing DDL, or learning. Triggers on "connect to lore", "query lore", "lore schema", "propose table", or any task involving a Lore API.
---

# Lore Skill

You are an agent connected to a Lore backend — a self-learning app backend with governance.

## Setup

```bash
lore auth status
```

**New user (no account yet)?** Sign up first — an invite code is required:

```bash
lore auth signup
```

This opens a browser to create an account. You'll need an invite code from an existing Lore admin.

**Existing user?** Log in:

```bash
lore auth login                     # interactive (opens browser)
lore auth login --magic-link        # email-based login
lore auth login --key <api-key>     # API key auth (for agents/CI)
```

API keys are created from the Lore web UI under **System > API Keys**.

## Core workflow

### 1. Get context before acting

Always start by understanding the schema and knowledge:

```bash
# What tables exist?
lore schema

# What does Lore know about a specific table?
lore context customers
```

Context includes: schema metadata, semantic knowledge, query patterns, corrections, and rules. **Read context before querying** to avoid mistakes other agents already made.

### 2. Read and write data (structured CRUD)

For simple operations, use the structured CRUD commands — no SQL needed:

```bash
# Read
lore get customers cust_100                            # single record by ID
lore list customers --where status=active --limit 10   # filtered list
lore list customers --order created_at:desc            # sorted
lore list customers --columns name,email               # select columns
lore count customers --where status=active             # count matching rows

# Write
lore create customers name="Acme Corp" email="info@acme.com"
lore update customers cust_100 status=churned --desc "Customer churned"
lore delete customers cust_100 --desc "Duplicate entry"
```

**Filter operators** for `--where`: `=`, `!=`, `>`, `>=`, `<`, `<=`, `LIKE`, `IS NULL`, `IS NOT NULL`. Multiple `--where` flags are AND'd. For complex queries (JOINs, OR, IN, subqueries), use `lore query` with raw SQL.

**Pagination:** `--limit N` (default 50, max 1000) and `--offset N`. The response includes total `count`.

**Auto-generated IDs:** When creating a record without specifying an ID, a ULID is auto-generated (e.g., `cust_01ARZ3NDEKTSV4RRFFQ69G5FAV`).

### 3. Query and mutate (raw SQL)

For complex operations beyond simple CRUD, use raw SQL:

```bash
# Read-only SQL
lore query "SELECT stage, COUNT(*), SUM(value) FROM deals GROUP BY stage"

# Governed mutations
lore mutate "INSERT INTO customers (id, name, email) VALUES ('cust_100', 'Acme Corp', 'info@acme.com')" \
  --desc "Add new customer Acme Corp"
```

The query response includes `knowledgeUsed` (what Lore consulted) and `learningHint` (suggestions for improvement).

Governance enforces:
- Only INSERT/UPDATE/DELETE (no DDL)
- System tables blocked
- Access policies checked

### 4. Propose schema changes

**Never run DDL directly.** Think carefully about data structure before proposing — a well-designed schema keeps the org's data coherent and queryable. See [Schema Design Guidelines](references/schema-design.md) for naming conventions, column types, and common mistakes.

```bash
lore schema propose \
  "CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT DEFAULT 'open', created_at TEXT NOT NULL)" \
  --reason "Task tracking for project management. Status values: open, in_progress, done."
```

Check status: `lore pending`

Approving/rejecting proposals requires explicit human confirmation:

```bash
lore approve <id> --approved-by-human
lore reject <id> --reason "..." --approved-by-human
```

The `--approved-by-human` flag is required. If you omit it, the CLI will remind you to confirm with the user first. Never pass this flag without the human explicitly agreeing.

### 6. Contribute knowledge

```bash
# Semantic: what data means
lore learn semantic "amount is stored in cents, divide by 100 for display" --scope orders

# Correction: fix a misunderstanding
lore learn correction "status=lead means prospect, not existing customer" --scope customers

# Pattern: a useful query
lore learn pattern "SELECT stage, COUNT(*), SUM(value) FROM deals GROUP BY stage" --scope deals
```

### 7. Custom domains

Standalone apps can be served on custom domains (e.g., `dashboard.acme.com`) instead of the default path. Setup: register domain → create CNAME to `standalone.thelore.dev` → verify. CF4SaaS handles TLS automatically.

```bash
lore domain add dashboard.acme.com --app my-app  # register
# → create CNAME: dashboard.acme.com → standalone.thelore.dev
lore domain verify <id>                           # activate after DNS propagates
lore domains                                      # list all
lore domain remove <id>                           # remove
```

See [Standalone Apps — Custom Domains](standalone-apps/SKILL.md#custom-domains) for the full setup guide, routing details, TLS lifecycle, troubleshooting, and API reference.

### 8. Import CSV data

Import bulk data from CSV files into existing tables. Ideal for ETL jobs, seed data, and migrations from external systems.

```bash
# Basic import
lore import customers ./customers.csv

# Validate without inserting (dry run)
lore import customers ./customers.csv --dry-run

# Abort on first error (default: skip bad rows)
lore import customers ./customers.csv --on-error abort
```

**Features:**
- **Header normalization** — `"Customer Name"` → `customer_name` automatically
- **Auto-generated IDs** — if the table has an `id` column and the CSV omits it, ULIDs are generated
- **Type coercion** — numbers, booleans, and nulls are inferred from column types
- **Error modes** — `skip` (default) imports good rows and reports bad ones; `abort` stops on first error
- **No approval queue** — imports bypass the bulk mutation threshold (access policies still enforced)

**MCP:**
```json
{
  "tool": "import",
  "arguments": {
    "table": "customers",
    "csv": "name,email,segment\nAcme,acme@co.com,enterprise\n...",
    "options": { "onError": "skip", "dryRun": false }
  }
}
```

**Limits:** 10,000 rows per call, ~10 MB. For larger datasets, split into multiple calls.

### 9. Export database

Export the org database as a SQL dump (admin or owner required):

```bash
# Download to current directory (filename includes org slug and date)
lore org export

# Download to a specific path
lore org export --output ./backups/my-org.sql
```

Restore is owner-only and must be done through the web UI (Settings > Organization > Data) for safety. The restore flow requires typing the org name to confirm, validates the dump contains required system tables, and runs pending migrations after restore.

### 10. Manage views

```bash
# List all saved views
lore views

# Create a list view (auto-generates spec from table schema)
lore views create --name "Active Customers" --for customers

# Create a record view (server-side generation with FK detection)
lore views create --name "Customer Detail" --for customers --type record

# Create other view types (board, dashboard, chart — all use server-side generation)
lore views create --name "Task Board" --for tasks --type board

# Create a view with a custom spec file (supports commands for Cmd+K palette)
lore views create --name "Deals (with actions)" --for deals --spec ./spec.json

# Delete a view
lore views delete <view-id>

# Generate a ViewSpec on the fly without saving (ad-hoc browsing)
# Via API: GET /v1/views/generate?table=<tableName>&hint=<type>
# Hint values: table, board, dashboard, chart, record
```

See **[ViewSpec Reference](references/view-spec.md)** for the full spec format — view types, sections, actions, toolbar, computed fields, 1:many relations, and examples.

## Building apps — ViewSpec vs Standalone

When asked to build an app, dashboard, or tool, **always prefer ViewSpec-based Lore apps** unless there's a specific reason to use standalone.

### Decision criteria

```
User wants an app
    │
    ├── Data tables + views + navigation?
    │   → ViewSpec app (default)
    │   Create tables, views, nav_spec via CLI/API.
    │   The platform renders everything — no HTML/JS needed.
    │
    ├── Needs custom UI, CDN libraries, or complex interactivity?
    │   → Standalone app
    │   Examples: D3 charts, Three.js, custom forms, rich editors
    │
    ├── Needs external user auth (customers, partners)?
    │   → Standalone app with external auth mode
    │
    └── User explicitly asks for standalone/HTML app?
        → Standalone app
```

### ViewSpec apps (preferred)

- **Zero frontend code** — define tables, columns, views, and navigation as JSON
- **Automatic UI** — the platform renders list views, record views, boards, dashboards
- **Built-in features** — inline editing, FK navigation, search, related sections, @-mentions
- **Faster to build** — no HTML/CSS/JS debugging, no iframe sandbox issues

```bash
# Create a complete app in minutes
lore schema propose "CREATE TABLE tasks (...)" --reason "Task tracker"
lore approve <id> --approved-by-human
lore views create --name "All Tasks" --for tasks
lore views create --name "Task Board" --for tasks --type board
# Configure nav_spec via the web UI or API
```

### Standalone apps (when needed)

Use only when ViewSpec can't handle the requirement. See [Standalone Apps](standalone-apps/SKILL.md).

## Rules

1. **Always get context first** — `lore context <table>` before querying
2. **Never bypass governance** — schema changes go through `lore schema propose`, not raw DDL
3. **Use parameterized queries** — never interpolate untrusted values
4. **Contribute what you learn** — patterns, corrections, semantics
5. **Check past feedback** — before proposing schema changes, check if similar proposals were rejected
6. **Use `_users` for people** — never create tables for users, members, employees, or team. The `_users` table is the org's member directory. Reference it via FK (e.g., `assignee_id TEXT REFERENCES _users(id)`)

## Reference docs

- [API Reference](references/api.md) — full REST endpoint list, request/response examples
- [Governance Model](references/governance.md) — access policies, approval workflow, audit trail
- [Knowledge System](references/knowledge.md) — query-learn loop, knowledge types, passive inference
- [Schema Design](references/schema-design.md) — naming conventions, column types, proposal guidelines
- [ViewSpec Reference](references/view-spec.md) — view types, sections, actions, toolbar, computed fields, 1:many relations
- [Standalone Apps](standalone-apps/SKILL.md) — standalone HTML apps with auth modes (internal, external, public)
