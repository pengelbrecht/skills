# Schema Design Guidelines

When proposing schema changes (`lore schema propose`), follow these principles to keep the org's data well-structured.

## Before proposing

1. **Check what already exists** — run `lore schema` and `lore context <table>` to understand current tables and their semantics. Don't create a table that duplicates an existing one.
2. **Check past rejections** — review `lore pending` and query `_approval_queue` for rejected proposals. If a similar proposal was rejected before, understand why before re-proposing.
3. **Think about the domain** — a Lore org should model a coherent domain (CRM, inventory, projects, etc.). Each table should represent a distinct entity, not a view or a report.

## Built-in tables — do NOT recreate

The `_users` table contains all org members (team members). **Never create a separate table for users, members, employees, or team.**

```
_users: id, email, name, role, status, created_at, updated_at, last_login
```

When your app needs to track who did something, who's assigned, or who's on a team — use a FK to `_users(id)`:

```sql
-- CORRECT: reference _users for assignees, owners, team members
CREATE TABLE tasks (
  ...
  assignee_id TEXT REFERENCES _users(id),
  created_by TEXT REFERENCES _users(id)
);

-- WRONG: never create a separate users/members/team table
CREATE TABLE team_members (id TEXT, name TEXT, email TEXT, ...);  -- DON'T DO THIS
```

## Table design

- **Primary keys**: always `id TEXT PRIMARY KEY` with a meaningful prefix (e.g. `cust_`, `ord_`, `task_`). Use ULIDs or UUIDs, never auto-incrementing integers.
- **Timestamps**: always `TEXT` in ISO 8601 UTC format (e.g. `created_at TEXT NOT NULL`). Never use `INTEGER` epoch.
- **Foreign keys**: reference other tables by their `id TEXT` column. Name the column `<entity>_id` (e.g. `customer_id TEXT REFERENCES customers(id)`).
- **Status fields**: use `TEXT` with well-defined values (e.g. `status TEXT DEFAULT 'active'`). Document the valid values in the proposal reason.
- **Nullability**: be intentional. Required fields should be `NOT NULL`. Optional fields can be nullable, but document what null means.

## Naming conventions

- **Tables**: plural, snake_case (e.g. `customers`, `order_items`, `support_tickets`)
- **Columns**: singular, snake_case (e.g. `customer_id`, `created_at`, `total_amount`)
- **Avoid abbreviations**: `description` not `desc`, `quantity` not `qty`
- **Boolean columns**: use `is_` prefix (e.g. `is_active`, `is_verified`)

## What makes a good proposal

A well-structured proposal includes:

```bash
lore schema propose \
  "CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    assignee_id TEXT REFERENCES _users(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    due_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
  )" \
  --reason "Task tracking for project management. Status values: open, in_progress, done, cancelled. Links to existing projects table and _users system table."
```

Key elements:
- Clear primary key with prefix convention
- Explicit NOT NULL on required fields
- Foreign keys to existing tables
- TEXT timestamps
- Descriptive `--reason` explaining purpose and valid values

## Foreign key best practices

- **Always use REFERENCES** — declare foreign keys inline with `REFERENCES <table>(id)`. This lets Lore discover relationships automatically and provide richer context to agents.
- **Naming convention** — FK columns should be named `<table_singular>_id` (e.g., `customer_id REFERENCES customers(id)`, `project_id REFERENCES projects(id)`).
- **Set the display column** — after creating a table, call `lore schema set-display <table> <column>` to tell Lore which column to show when rendering FK lookups. For example, `lore schema set-display customers name` means any FK pointing to `customers` will display the `name` value instead of the raw ID.
- **One FK per column** — each FK column references exactly one parent table. Don't reuse a column for multiple relationships.
- **Cascading** — SQLite supports `ON DELETE CASCADE` and `ON UPDATE CASCADE`. Use them when child rows should be removed with their parent. Omit them when orphaned rows should be preserved (e.g., audit logs).

Example with FKs and display column:

```bash
lore schema propose \
  "CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    product_id TEXT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
  )" \
  --reason "Order tracking. Links to customers and products. Status: pending, confirmed, shipped, delivered."

# After approval, set display columns so FK lookups show names:
lore schema set-display customers name
lore schema set-display products title
```

## Referencing org members (`_users`)

Lore users (org members) live in the control plane but are synced into each org's `_users` system table. This table contains denormalized profile data (`id`, `name`, `email`, `role`, `status`). Business tables should reference `_users.id` — never control plane account IDs.

### How `_users` works

- **Populated automatically** — users are added during org provisioning, invites (`POST /v1/users/invite`), and signup. Profile data (name, email) is lazily synced from the control plane on each request.
- **Read-only via API** — `_users` is a system table. You cannot INSERT/UPDATE/DELETE it through `/v1/mutate`. Use the dedicated user management endpoints (`/v1/users/*`) instead.
- **Queryable** — you can SELECT from `_users` and JOIN it with business tables in queries.

### Assigning users to records

Reference `_users(id)` in your FK column:

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  assignee_id TEXT REFERENCES _users(id),
  created_by TEXT NOT NULL REFERENCES _users(id),
  created_at TEXT NOT NULL
);
```

Query with a JOIN to resolve names:

```sql
SELECT t.title, u.name AS assignee_name
FROM tasks t
LEFT JOIN _users u ON t.assignee_id = u.id;
```

### Views and `_users` references

In a ViewSpec, user FK columns render as reference links automatically:

```json
{
  "key": "assignee_id",
  "type": "reference",
  "referencedTable": "_users",
  "referencedDisplayColumn": "name"
}
```

Set the display column so FK lookups show user names:

```bash
lore schema set-display _users name
```

### Listing available users

To populate a user picker in an app, query `_users` directly:

```sql
SELECT id, name, email FROM _users WHERE status = 'active' ORDER BY name;
```

Or use the API endpoint `GET /v1/users` (requires admin/owner role).

## Common mistakes

- **Too many tables too fast** — propose one table at a time, verify it works, then add related tables
- **Denormalization without reason** — don't duplicate data across tables unless there's a clear performance need
- **Missing timestamps** — every table should have at least `created_at`
- **Vague reasons** — "need this table" is not a reason. Explain what problem it solves and how it relates to existing data
- **Ignoring existing knowledge** — if Lore has semantic knowledge about a table, the new table should be consistent with those semantics
