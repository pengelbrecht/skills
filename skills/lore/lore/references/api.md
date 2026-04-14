# Lore API Reference

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/data/:table/:id` | GET | Get a single record by primary key |
| `/v1/data/:table` | GET | List records (filterable, paginated) |
| `/v1/data/:table/count` | GET | Count matching records |
| `/v1/data/:table` | POST | Create a record |
| `/v1/data/:table/:id` | PATCH | Update a record |
| `/v1/data/:table/:id` | DELETE | Delete a record |
| `/v1/context?scope=<table>` | GET | Get knowledge for a table |
| `/v1/schema` | GET | Full schema with metadata |
| `/v1/query` | POST | Read-only SQL (governed) |
| `/v1/mutate` | POST | INSERT/UPDATE/DELETE (governed) |
| `/v1/import/:table` | POST | CSV bulk import |
| `/v1/ingest/:table` | POST | JSON webhook ingress |
| `/v1/schema/propose` | POST | Propose DDL change |
| `/v1/learn` | POST | Contribute knowledge |
| `/v1/pending` | GET | Pending approvals |
| `/v1/apps` | GET/POST | List/create apps |
| `/v1/views` | GET/POST | List/create views |
| `/v1/keys` | GET/POST/DELETE | API key management |
| `/v1/permissions` | GET | What can I do? |
| `/v1/search/:table?q=<query>` | GET | Full-text search |
| `/v1/audit` | GET | Audit trail (filterable) |
| `/v1/error-reports` | GET/POST | Error reporting |
| `/v1/skill` | GET | Skill metadata |
| `/v1/skill/instructions` | GET | Skill instructions |
| `/v1/skill/resources` | GET | List skill resources |
| `/v1/skill/resources/:filename` | GET | Read a skill resource |
| `/v1/views/generate?table=<name>` | GET | Generate a ViewSpec on the fly (not saved) |
| `/v1/custom-domains` | GET | List custom domains (admin/owner) |
| `/v1/custom-domains` | POST | Add a custom domain (admin/owner) |
| `/v1/custom-domains/:id/verify` | POST | Verify DNS and activate domain |
| `/v1/custom-domains/:id` | DELETE | Remove a custom domain |
| `/v1/org/export` | GET | Download org database as SQL dump (admin/owner) |
| `/v1/org/restore` | POST | Restore org database from SQL dump (owner only, session auth only) |

## Authentication

All `/v1/*` endpoints require authentication via:

- **API key**: `Authorization: Bearer <key>` — create keys from web UI under System > API Keys. API keys inherit their creator's org membership role (e.g., a key created by an admin can perform admin operations).
- **Bearer session token**: `Authorization: Bearer <token>` — central session token (web UI sends these; validated against the control plane)
- **Session cookie**: `lore_session=<token>` + `lore_org=<orgId>` — set by web UI login

The auth middleware tries Bearer tokens as central sessions first, then falls back to API key resolution.

## Data (structured CRUD)

Structured CRUD endpoints — no SQL required. Recommended for simple operations. Use `/v1/query` and `/v1/mutate` for complex SQL.

**Get a record:**
```bash
curl -s "$LORE_API_URL/v1/data/customers/cust_100" \
  -H "Authorization: Bearer $LORE_API_KEY"
# → { "row": { "id": "cust_100", "name": "Acme Corp", ... } }
```

**List records (with filters):**
```bash
curl -s "$LORE_API_URL/v1/data/customers?where=status:eq:active&limit=10&order=name:asc" \
  -H "Authorization: Bearer $LORE_API_KEY"
# → { "rows": [...], "count": 42, "limit": 10, "offset": 0 }
```

**Filter format:** `where=<column>:<op>:<value>` (repeatable, AND'd). Operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `like`, `null`, `notnull`.

Additional query params: `limit` (default 50, max 1000), `offset`, `order` (format `col:asc` or `col:desc`), `columns` (comma-separated).

**Count records:**
```bash
curl -s "$LORE_API_URL/v1/data/customers/count?where=status:eq:active" \
  -H "Authorization: Bearer $LORE_API_KEY"
# → { "count": 42 }
```

**Create a record:**
```bash
curl -s "$LORE_API_URL/v1/data/customers" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "Acme Corp", "email": "info@acme.com"}, "desc": "New customer"}'
# → 201 { "row": { "id": "cust_01ARZ...", "name": "Acme Corp", ... }, "rowsAffected": 1 }
```

If the table has a TEXT primary key and no ID is provided, a ULID is auto-generated.

**Update a record:**
```bash
curl -s -X PATCH "$LORE_API_URL/v1/data/customers/cust_100" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"data": {"status": "churned"}, "desc": "Customer churned"}'
# → { "row": { "id": "cust_100", "status": "churned", ... }, "rowsAffected": 1 }
```

Returns 404 if the record doesn't exist.

**Delete a record:**
```bash
curl -s -X DELETE "$LORE_API_URL/v1/data/customers/cust_100" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"desc": "Duplicate entry"}'
# → { "rowsAffected": 1 }
```

Returns 404 if the record doesn't exist. The request body (with `desc`) is optional.

Governance is fully enforced: access policies, system table blocking, bulk mutation detection, and audit trail — same as `/v1/mutate`.

## Query

```bash
curl -s "$LORE_API_URL/v1/query" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM customers WHERE status = ?", "params": ["active"]}'
```

Response includes:
- `rows` — query results
- `columns` — column names and types
- `knowledgeUsed` — which knowledge entries Lore consulted
- `learningHint` — suggestions for contributing knowledge

## Mutate (governed)

**Parameterized SQL:**
```bash
curl -s "$LORE_API_URL/v1/mutate" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
    "params": ["cust_100", "Acme Corp", "info@acme.com"],
    "table": "customers",
    "action": "insert"
  }'
```

**JSON ingress (simpler):**
```bash
curl -s "$LORE_API_URL/v1/ingest/customers" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": "cust_100", "name": "Acme Corp", "email": "info@acme.com"}'
```

Governance enforces:
- Only INSERT/UPDATE/DELETE (no DDL)
- System tables (`_users`, `_knowledge`, etc.) blocked
- Access policies checked per actor

## CSV Import

Bulk import rows from a CSV string or file into an existing table. Bypasses the bulk mutation approval queue — access policies still enforced.

**JSON body (CLI and MCP use this):**
```bash
curl -s "$LORE_API_URL/v1/import/customers" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "csv": "name,email,segment\nAcme,acme@co.com,enterprise\nBeta,beta@co.com,startup",
    "options": { "onError": "skip", "dryRun": false }
  }'
```

**Multipart form (file upload):**
```bash
curl -s "$LORE_API_URL/v1/import/customers" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -F "file=@customers.csv" \
  -F "onError=skip" \
  -F "dryRun=false"
```

**Response:**
```json
{
  "table": "customers",
  "rowsImported": 2,
  "rowsSkipped": 0,
  "errors": [],
  "dryRun": false
}
```

**Options:**
- `onError`: `"skip"` (default) — import good rows, collect errors. `"abort"` — stop on first error.
- `dryRun`: `true` — validate without inserting.

**Features:** CSV headers are normalized to snake_case (`"Customer Name"` → `customer_name`). If the table has an `id` column and the CSV omits it, ULIDs are auto-generated. Types are coerced based on column definitions (integers, reals, booleans, nulls).

**Limits:** 10,000 rows per call, ~10 MB. Batched internally in chunks of 100 rows.

## Schema proposals

**Never run DDL directly.** Always propose:

```bash
curl -s "$LORE_API_URL/v1/schema/propose" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT DEFAULT '\''open'\'')",
    "reason": "Need task tracking for the project management app"
  }'
```

Check status: `GET /v1/pending`

## Learn

```bash
# Semantic: what data means
curl -s "$LORE_API_URL/v1/learn" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "semantic", "scope": "orders", "content": "amount is stored in cents, divide by 100 for display"}'

# Correction: fix a misunderstanding
curl -s "$LORE_API_URL/v1/learn" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "correction", "scope": "customers", "content": "status=lead means prospect, not existing customer"}'

# Pattern: a useful query
curl -s "$LORE_API_URL/v1/learn" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "pattern", "scope": "deals", "content": "SELECT stage, COUNT(*), SUM(value) FROM deals GROUP BY stage", "tables": ["deals"]}'
```

Knowledge types: `semantic`, `correction`, `pattern`, `rule`

## View generation

Generate a ViewSpec on the fly for any table without saving it. Useful for ad-hoc data browsing:

```bash
curl -s "$LORE_API_URL/v1/views/generate?table=customers" \
  -H "Authorization: Bearer $LORE_API_KEY"
```

Accepts an optional `hint` query parameter to steer the view type:

```bash
curl -s "$LORE_API_URL/v1/views/generate?table=customers&hint=record" \
  -H "Authorization: Bearer $LORE_API_KEY"
```

**Hint values:** `table` (default list), `board`, `dashboard`, `chart`, `record`

Without a hint, returns a list-type ViewSpec. With `hint=record`, returns a record view with auto-detected `related` sections for 1:many relationships (reverse foreign keys). Column types are inferred from the schema, including datetime detection for `_at` columns and boolean detection for INTEGER columns with boolean-like names (`is_*`, `has_*`, `completed`, etc.).

## ViewSpec: actions, sections, related data

See **[references/view-spec.md](view-spec.md)** for the full ViewSpec reference covering:
- View types (list, record, board, dashboard)
- Actions + toolbar (navigate, mutate, query, filter, sort, open)
- Sections (fields with computed aggregates, related 1:many)
- Column types and inline toggles
- Auto-generation with `--type record` and reverse FK detection
- Complete examples (OKR detail, deals list with toolbar)

## Custom domains

Manage custom domains for standalone apps. All endpoints require admin or owner role. See [Standalone Apps — Custom Domains](../standalone-apps/SKILL.md#custom-domains) for the full setup guide.

```bash
# List all custom domains
# → { domains: [{ id, domain, app_slug, status, cf_hostname_id, verified_at, created_at }] }
curl -s "$LORE_API_URL/v1/custom-domains" \
  -H "Authorization: Bearer $LORE_API_KEY"

# Add a custom domain (auto-provisions TLS via CF4SaaS)
# Body: { domain: string, appSlug: string }
# → 201 { id, domain, status: "pending", cname: "standalone.thelore.dev", cfSslStatus }
curl -s "$LORE_API_URL/v1/custom-domains" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"domain": "dashboard.acme.com", "appSlug": "my-app"}'
# Next: create CNAME record: dashboard.acme.com → standalone.thelore.dev

# Verify DNS + TLS and activate
# → 200 { status: "active", verifiedAt, cfStatus, cfSslStatus }
# → 400 { error, cname, cfStatus, cfSslStatus } (not ready)
curl -s -X POST "$LORE_API_URL/v1/custom-domains/<id>/verify" \
  -H "Authorization: Bearer $LORE_API_KEY"

# Remove a custom domain (also deletes CF4SaaS hostname)
# → 200 { deleted: true }
curl -s -X DELETE "$LORE_API_URL/v1/custom-domains/<id>" \
  -H "Authorization: Bearer $LORE_API_KEY"
```

**Error codes:** `VALIDATION_ERROR` (400) invalid domain format, `NOT_FOUND` (404) app or domain doesn't exist, `CONFLICT` (409) domain already registered.
