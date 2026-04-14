# Building Standalone Apps

Standalone apps are self-contained HTML/JS/CSS applications served from Lore's cloud with built-in authentication and data access. Think of them as rich, interactive artifacts with a permanent URL, a real backend, and auth.

## How It Works

1. You write a single HTML file with inline JS/CSS (CDN imports work — Tailwind, React, D3, etc.)
2. Publish it via CLI or API with an **auth mode**
3. Lore serves it at `/apps/{org-slug}/{your-slug}` with automatic auth
4. Users see a login form on first visit, then the app loads in a sandboxed iframe with the Lore SDK injected

## Auth Modes

Standalone apps support three authentication modes:

| Mode | Users | Use Case |
|------|-------|----------|
| **internal** (default) | Lore platform users (org members) | Admin dashboards, internal tools |
| **external** | Records in your org's own data table | Customer portals, partner dashboards |
| **public** | No auth required | Status pages, marketing sites |

### Internal Mode (default)

Users sign in with their Lore account. The SDK provides `lore.user` (Lore account info) and `lore.org` (org info). This is the existing behavior.

### External Mode

External users authenticate against a table in your org's database (e.g., `customers`). They never need a Lore platform account.

**How it works:**
1. Configure `auth_config` pointing to your identity table (which table, which columns for email/password/name)
2. Define **scopes** — which data tables the app can access and which column links rows to the user
3. External users sign in at `/apps/{org}/{app}/auth/sign-in` with email + password
4. Row-level filtering is automatic — users only see rows where `{filter_column} = their_id`

**Publish with external auth:**
```bash
POST /v1/standalone-apps
{
  "slug": "customer-portal",
  "title": "Customer Portal",
  "html": "<html>...",
  "authMode": "external",
  "authConfig": {
    "table": "customers",
    "id_column": "id",
    "email_column": "email",
    "password_column": "password_hash",
    "display_name_column": "name",
    "default_role": "app:customer-portal:user",
    "status_column": "status",
    "active_status_value": "active",
    "allow_registration": false,
    "session_ttl_hours": 24,
    "scopes": [
      { "table": "orders", "permission": "read", "filter_column": "customer_id" },
      { "table": "support_tickets", "permission": "write", "filter_column": "customer_id" }
    ]
  }
}
```

**Key differences from internal mode:**
- `lore.user` contains the external user's info (from identity table), not a Lore account
- `lore.app` replaces `lore.org` — external users see app context, not org context
- All queries are automatically filtered by `filter_column` — Alice only sees her orders
- Complex SQL (CTEs, subqueries, UNION, window functions) is rejected for external actors
- System tables (`_*`) are never accessible

**External auth endpoints (all under `/apps/{org}/{app}/auth/`):**
- `POST /sign-in` — email + password → session cookie
- `POST /sign-out` — clear session
- `POST /bootstrap` — get short-lived token for API calls
- `POST /register` — self-registration (when `allow_registration: true`)
- `POST /reset-password/request` — request password reset
- `POST /reset-password/confirm` — confirm with token + new password
- `GET /sessions` — list active sessions
- `POST /sessions/revoke-all` — revoke all sessions except current

**Password auto-hashing:** When you INSERT/UPDATE the identity table's password column via `/v1/mutate`, plaintext values are automatically hashed with PBKDF2-SHA512. You can write `'plaintext123'` and it's stored hashed.

### Public Mode

No authentication. `lore.user` is null. Suitable for static content or status pages.

## The SDK

Your app gets `window.lore` automatically. Always wait for it to initialize:

```javascript
const lore = await window.lore._ready;
```

### Available APIs

```javascript
// User & context (populated after _ready resolves)
lore.user   // { id, name, email, role }
lore.org    // { id, name, slug }  — internal mode only
lore.app    // { id, slug, title } — external mode only

// Query data (read)
const result = await lore.api.query({
  sql: "SELECT * FROM customers WHERE status = ?",
  params: ["active"]
});
// result: { rows: [...], columns: [...], rowCount: N }

// Mutate data (insert/update/delete — goes through governance)
const result = await lore.api.mutate({
  sql: "UPDATE tickets SET status = ? WHERE id = ?",
  params: ["closed", "ticket_123"]
});
// result: { rowsAffected: 1 }

// Live updates — re-query when data changes
const unsub = lore.api.subscribe("customers", (event) => {
  // event: { table, action, rowId, ts }
  // Re-query your data here
});
// Use '*' to subscribe to all tables
// Call unsub() to stop listening

// Search (full-text)
const result = await lore.api.search("customers", { q: "acme" });
// result: { rows: [...] }

// Raw API call (any /v1/* endpoint)
const result = await lore.api.fetch("/v1/schema", { method: "GET" });
```

## Recommended: Arrow.js for Reactive Apps

Arrow.js is the recommended UI library for standalone apps. It is ~3kb, requires no build step, provides reactive DOM updates, and is designed for CDN usage.

```javascript
import { reactive, html } from 'https://esm.sh/@arrow-js/core'
```

### Pattern

Wrap mutable state in `reactive()`, then use `${() => expr}` for reactive bindings in templates. When state properties change, only the affected DOM nodes update.

```javascript
import { reactive, html } from 'https://esm.sh/@arrow-js/core'

const state = reactive({
  loading: true,
  error: null,
  rows: [],
})

html`
  <div>
    ${() => state.loading
      ? html`<p>Loading...</p>`
      : html`<ul>
          ${() => state.rows.map(r => html`<li>${r.name}</li>`)}
        </ul>`
    }
  </div>
`(document.getElementById('app'))

// Updating state automatically updates the DOM:
state.rows = [{ name: 'Acme' }, { name: 'Globex' }]
state.loading = false
```

## Rich SDK — @lore/sdk

The `@lore/sdk` package provides higher-level reactive data bindings that combine `query()` and `subscribe()` into auto-refreshing objects. Import via CDN:

```javascript
import { createReactiveTable, createReactiveRecord } from 'https://esm.sh/@lore/sdk'
```

### createReactiveTable

Auto-refreshing query — re-queries on data changes with 200ms debounce. Extracts the table name from your SQL to auto-subscribe.

```javascript
const customers = createReactiveTable(
  lore,
  'SELECT * FROM customers WHERE status = ?',
  ['active']
)

// Properties (all update automatically when data changes):
customers.rows      // unknown[] — query result rows
customers.loading   // boolean — true during queries
customers.error     // string | null — error message if query fails

// Methods:
customers.refresh() // manual refresh (returns Promise)
customers.destroy() // cleanup — unsubscribes from changes
```

### createReactiveRecord

Single record binding — auto-refreshes when the underlying table changes.

```javascript
const deal = createReactiveRecord(lore, 'deals', 'deal_123')

// Properties:
deal.data     // Record<string, unknown> | null — the row, or null if not found
deal.loading  // boolean
deal.error    // string | null

// Methods:
deal.refresh() // manual refresh
deal.destroy() // cleanup
```

### Using with Arrow.js

Wrap the SDK objects with Arrow's `reactive()` for automatic DOM updates:

```javascript
import { reactive, html } from 'https://esm.sh/@arrow-js/core'
import { createReactiveTable } from 'https://esm.sh/@lore/sdk'

const lore = await window.lore._ready
const table = reactive(createReactiveTable(lore, 'SELECT * FROM customers'))

// Initial load
await table.refresh()

html`
  ${() => table.loading
    ? html`<p>Loading...</p>`
    : html`<ul>${() => table.rows.map(r => html`<li>${r.name}</li>`)}</ul>`
  }
`(document.getElementById('app'))
```

## Optional: @thelore/ui Component Library

`@thelore/ui` is an **optional** set of Arrow.js template functions with Tailwind classes. It gives you polished defaults for common UI patterns — buttons, forms, dialogs, tables — without hand-crafting CSS. **You don't have to use it.** Customers who want full design control can skip it entirely and style from scratch.

```javascript
import { Button, Field, Dialog, Card, Badge, Alert, Table, Skeleton } from 'https://esm.sh/@thelore/ui'
```

Assumes Tailwind CDN is loaded (which every standalone app already includes). Components accept a `class` prop for Tailwind overrides. Supports light + dark mode via Tailwind `dark:` variants. ~2.5KB gzipped.

### Quick example

```javascript
import { reactive, html } from 'https://esm.sh/@arrow-js/core'
import { Button, Field, Card, Badge } from 'https://esm.sh/@thelore/ui'

const state = reactive({ name: '' })

html`
  <div class="max-w-md mx-auto p-8 space-y-4">
    ${Card({ title: 'New Customer', content: html`
      ${Field({ label: 'Name', value: state.name, oninput: e => state.name = e.target.value })}
      ${Field({ label: 'Email', type: 'email', placeholder: 'you@company.com' })}
      ${Button({ label: 'Save', onclick: () => console.log(state.name) })}
    `})}
  </div>
`(document.getElementById('app'))
```

### Available components

| Component | Props | Notes |
|-----------|-------|-------|
| `Button` | `label, variant (primary/secondary/ghost/destructive), size (sm/md/lg), disabled, onclick` | Focus ring, min-height touch targets |
| `Field` | `label, type (text/email/password/number/date/textarea/select), value, options, error, oninput` | Error state styling, label spacing |
| `Dialog` | `open, onclose, title, content, footer` | Native `<dialog>`, backdrop blur |
| `Card` | `title, subtitle, content` | Stat cards or content panels |
| `Badge` | `label, variant (default/success/warning/destructive)` | Status indicators |
| `Alert` | `title, message, variant (info/success/warning/destructive)` | Left border accent |
| `Table` | `columns, rows, onrowclick, label` | Sortable headers, hover rows |
| `Skeleton` | `width, height, lines` | Block or text placeholder |

All components accept `class` for Tailwind overrides: `Button({ label: 'Go', class: 'w-full' })`.

## Multi-File Apps

For apps that need multiple pages (e.g., a customer portal with dashboard, orders, settings), use multi-file mode. Each page is its own HTML file, and Lore routes URLs to the right file.

### When to use multi-file

- Your app has 3+ distinct pages/sections
- A single HTML file would exceed ~500 lines
- You want agents to edit individual pages without touching the whole app
- You need real URL-based navigation between pages

### Route patterns

Routes map URL paths to HTML files. Patterns support `:param` segments:

```json
{
  "/": "index.html",
  "/orders": "orders.html",
  "/orders/:id": "order-detail.html",
  "/settings": "settings.html"
}
```

Exact matches take priority over parameterized routes. `/orders` always serves `orders.html`, not `order-detail.html`.

### SDK: lore.route

In multi-file apps, the SDK includes route information:

```javascript
const lore = await window.lore._ready;
console.log(lore.route);
// { path: "/orders/ord_123", params: { id: "ord_123" } }
```

Single-file apps have `lore.route = null`.

### Navigation between pages

Use standard `<a>` tags. The iframe sandbox allows top-level navigation, so clicking a link loads the new page through Lore's router:

```html
<nav>
  <a href="/apps/acme/portal/">Dashboard</a>
  <a href="/apps/acme/portal/orders">Orders</a>
  <a href="/apps/acme/portal/settings">Settings</a>
</nav>
```

Each page load is independent — the SDK reinitializes, auth is re-validated. This is by design: no shared client-side state between pages means no stale state bugs.

### Shared code

Non-HTML files (JS, CSS) are served as static assets. Reference them with relative paths:

```html
<!-- In orders.html -->
<link rel="stylesheet" href="/apps/acme/portal/styles.css">
<script src="/apps/acme/portal/shared.js"></script>
```

### Publishing multi-file apps

**REST API:**
```bash
POST /v1/standalone-apps
{
  "slug": "portal",
  "title": "Customer Portal",
  "files": {
    "index.html": "<!DOCTYPE html>...",
    "orders.html": "<!DOCTYPE html>...",
    "order-detail.html": "<!DOCTYPE html>...",
    "styles.css": "body { ... }",
    "shared.js": "// shared logic"
  },
  "routes": {
    "/": "index.html",
    "/orders": "orders.html",
    "/orders/:id": "order-detail.html"
  }
}
```

**CLI:**
```bash
lore app publish-standalone portal --title "Portal" --dir ./portal \
  --routes '{ "/": "index.html", "/orders": "orders.html", "/orders/:id": "order-detail.html" }'
```

### Per-file updates

Edit one file at a time without republishing the entire app:

```bash
# REST
PUT /v1/standalone-apps/portal/files/orders.html
Content-Type: text/plain
<new HTML content>

# CLI
lore app update-file portal orders.html --file ./orders.html
```

### Listing files

```bash
# REST
GET /v1/standalone-apps/portal/files

# CLI
lore app list-files portal
```

## Constraints

### Single-file apps
- **Single HTML file** — all JS/CSS must be inline or loaded from CDNs
- **Max 5MB** — keep it reasonable

### Multi-file apps
- **Max 20MB total** across all files
- **Safe filenames only** — alphanumeric, hyphens, underscores, dots, forward slashes
- **Routes required** — every route must reference a file in the files map
- **At least one HTML file** required

### Both modes
- **CDN imports work** — Tailwind, React, D3, Chart.js, Three.js, etc. all load fine
- **Must await `_ready`** — the SDK initializes asynchronously via postMessage
- **fetch path must start with `/v1/`** — the SDK bridge only proxies API paths

## CLI Commands

```bash
# Publish single-file app — requires admin/owner role
lore app publish-standalone <slug> --title "My App" --file ./app.html

# Publish multi-file app from a directory
lore app publish-standalone <slug> --title "My App" --dir ./app \
  --routes '{ "/": "index.html", "/orders": "orders.html" }'

# Update a single file in a multi-file app
lore app update-file <slug> <filename> --file ./updated.html

# List files in a multi-file app
lore app list-files <slug>

# Get app metadata
lore app get-standalone <slug>

# List all standalone apps
lore app list-standalone

# Delete an app
lore app delete-standalone <slug>
```

## REST API

```bash
# Publish single-file app (internal mode — default)
POST /v1/standalone-apps
Body: { "slug": "my-app", "title": "My App", "html": "<html>..." }

# Publish multi-file app
POST /v1/standalone-apps
Body: { "slug": "portal", "title": "Portal",
        "files": { "index.html": "...", "orders.html": "..." },
        "routes": { "/": "index.html", "/orders": "orders.html" } }

# Publish with external auth (works with both single and multi-file)
POST /v1/standalone-apps
Body: { "slug": "portal", "title": "Portal", "html": "<html>...",
        "authMode": "external", "authConfig": { ... } }

# Publish (public mode)
POST /v1/standalone-apps
Body: { "slug": "status", "title": "Status", "html": "<html>...",
        "authMode": "public" }

# List
GET /v1/standalone-apps

# Get metadata (includes appMode, routes, files for multi-file apps)
GET /v1/standalone-apps/:slug

# List files in a multi-file app
GET /v1/standalone-apps/:slug/files

# Get file content
GET /v1/standalone-apps/:slug/files/:filename

# Update a single file
PUT /v1/standalone-apps/:slug/files/:filename
Content-Type: text/plain

# Delete
DELETE /v1/standalone-apps/:slug
```

Publish and delete require admin or owner role.

## Slug Rules

- 3-63 characters
- Lowercase letters, numbers, and hyphens only
- Must start and end with a letter or number
- Pattern: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`

## Complete Example — Arrow.js Reactive Dashboard

A working dashboard with Arrow.js, live updates via `subscribe()`, and Tailwind styling:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Data Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="module">
    import { reactive, html } from 'https://esm.sh/@arrow-js/core'

    const state = reactive({
      loading: true,
      error: null,
      user: null,
      org: null,
      rows: [],
    })

    html`
      <div class="max-w-4xl mx-auto p-8">
        ${() => state.loading
          ? html`<p class="text-gray-500">Loading...</p>`
          : state.error
            ? html`<p class="text-red-500">${() => state.error}</p>`
            : html`
              <div class="flex items-center justify-between mb-8">
                <h1 class="text-2xl font-bold text-gray-900">
                  ${() => state.org?.name} Dashboard
                </h1>
                <p class="text-sm text-gray-500">
                  ${() => state.user?.name}
                </p>
              </div>
              <div class="bg-white rounded-xl shadow-sm border divide-y">
                ${() => state.rows.map(row => html`
                  <div class="flex items-center justify-between px-4 py-3">
                    <span class="font-mono text-sm">${row.table_name}</span>
                    <span class="text-xs text-gray-400">${row.description || ''}</span>
                  </div>
                `)}
              </div>
            `
        }
      </div>
    `(document.getElementById('app'))

    async function loadTables(lore) {
      const schema = await lore.api.query({
        sql: 'SELECT table_name, description FROM _schema_registry ORDER BY table_name'
      })
      state.rows = schema.rows
    }

    async function init() {
      try {
        const lore = await window.lore._ready
        state.user = lore.user
        state.org = lore.org

        await loadTables(lore)
        state.loading = false

        // Live updates — re-query when schema changes
        lore.api.subscribe('_schema_registry', () => loadTables(lore))
      } catch (e) {
        state.error = e.message
        state.loading = false
      }
    }

    init()
  </script>
</head>
<body class="bg-gray-50 min-h-screen">
  <div id="app"></div>
</body>
</html>
```

## Basic Example (without Arrow.js)

A simpler vanilla JS dashboard for reference:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Data Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
  <div class="max-w-4xl mx-auto p-8">
    <div id="loading" class="text-gray-500">Initializing...</div>
    <div id="app" class="hidden">
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-2xl font-bold text-gray-900" id="title"></h1>
        <p class="text-gray-500" id="subtitle"></p>
      </div>
      <div class="bg-white rounded-xl shadow-sm border p-6">
        <h2 class="text-lg font-semibold mb-4">Tables</h2>
        <div id="tables" class="space-y-2"></div>
      </div>
    </div>
  </div>
  <script>
    (async function() {
      try {
        const lore = await window.lore._ready;

        document.getElementById('title').textContent = lore.org.name + ' Dashboard';
        document.getElementById('subtitle').textContent = 'Signed in as ' + lore.user.name;

        const schema = await lore.api.query({
          sql: "SELECT table_name, description FROM _schema_registry ORDER BY table_name"
        });

        const tablesEl = document.getElementById('tables');
        if (schema.rows.length === 0) {
          tablesEl.innerHTML = '<p class="text-gray-400">No tables found</p>';
        } else {
          tablesEl.innerHTML = schema.rows.map(row =>
            '<div class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50">' +
              '<span class="font-mono text-sm">' + row.table_name + '</span>' +
              '<span class="text-xs text-gray-400">' + (row.description || '') + '</span>' +
            '</div>'
          ).join('');
        }

        document.getElementById('loading').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
      } catch(err) {
        document.getElementById('loading').textContent = 'Error: ' + err.message;
      }
    })();
  </script>
</body>
</html>
```

## Custom Domains

Standalone apps can be served on a custom domain (e.g., `dashboard.acme.com`) instead of the default `/apps/{org-slug}/{slug}` path. One custom domain maps to one standalone app.

### End-to-end setup

There are three steps: register the domain, configure DNS, then verify.

**Step 1 — Register the domain with Lore:**

```bash
lore domain add dashboard.acme.com --app my-app
# → Output:
#   Domain added: dashboard.acme.com
#   Next steps:
#     1. Create a CNAME record: dashboard.acme.com → standalone.thelore.dev
#        (Set proxy status to "DNS only" if using Cloudflare)
#     2. Run: lore domain verify cd_XXXXX
#   TLS status: initializing
```

This creates a `pending` entry in the control plane's `_custom_domains` table and auto-registers a CF4SaaS Custom Hostname for TLS provisioning. The returned `cd_XXXXX` ID is needed for verify/remove.

**Step 2 — Create the DNS record:**

In the customer's DNS provider, create a CNAME record:

```
dashboard.acme.com  CNAME  standalone.thelore.dev
```

If the customer uses Cloudflare for their own DNS, the CNAME **must** be set to "DNS only" (grey cloud), not "Proxied" (orange cloud) — otherwise CF4SaaS certificate validation fails because Cloudflare intercepts the validation request.

Apex domains (e.g., `acme.com` without a subdomain) cannot use CNAME records per DNS standards. Some providers support CNAME flattening (Cloudflare, Route53 ALIAS) which works, but subdomains are strongly preferred.

**Step 3 — Verify and activate:**

```bash
lore domain verify cd_XXXXX
# → If DNS + TLS ready: status changes to 'active', domain starts serving
# → If not ready: returns current cfStatus and cfSslStatus with guidance
```

Verification checks two things:
1. **DNS resolution** — the CNAME points to `standalone.thelore.dev`
2. **TLS certificate** — CF4SaaS has provisioned and validated the certificate

Both must pass for the domain to become `active`. TLS provisioning typically takes 1-5 minutes after DNS is configured, but can take up to 15 minutes.

### Status lifecycle

```
pending → active     (DNS verified + TLS provisioned)
pending → pending    (DNS not yet configured, or TLS still provisioning)
active  → (removed)  (via lore domain remove)
```

### CLI reference

```bash
# List all custom domains for the org
lore domains
# → Shows: id, domain, app_slug, status, verified_at

# Add a domain (requires admin or owner role)
lore domain add <domain> --app <app-slug>
# → Returns: id, CNAME target, TLS status

# Verify DNS and activate
lore domain verify <id>
# → Returns: status, cfStatus, cfSslStatus

# Remove a domain (also deletes CF4SaaS hostname)
lore domain remove <id>
```

### REST API reference

All endpoints require admin or owner role.

```bash
# List domains
GET /v1/custom-domains
# → { domains: [{ id, domain, app_slug, status, cf_hostname_id, verified_at, created_at }] }

# Add domain
POST /v1/custom-domains
Content-Type: application/json
{ "appSlug": "my-app", "domain": "dashboard.acme.com" }
# → 201 { id, domain, status: "pending", cname: "standalone.thelore.dev", cfSslStatus }

# Verify and activate
POST /v1/custom-domains/:id/verify
# → 200 { status: "active", verifiedAt, cfStatus, cfSslStatus }
# → 400 { error, cname, cfStatus, cfSslStatus }  (not ready yet)

# Remove domain
DELETE /v1/custom-domains/:id
# → 200 { deleted: true }
```

### How routing works

The Lore Worker uses **hostname-first routing**. On every request:

1. Extract hostname from the request URL
2. Check if it's a known Lore domain (`*.thelore.dev`, `*.pages.dev`, `localhost`) — if yes, use normal routing
3. Otherwise, look up the hostname in `_custom_domains` where `status = 'active'`
4. If found → resolve the org, connect to the org's database, rewrite root path to `/apps/{org-slug}/{app-slug}`
5. If not found → return `404: No application is configured for {hostname}`

This means custom domain apps work identically to path-routed apps — same auth, same SDK, same API access. The URL is just different.

### How TLS works (CF4SaaS)

Lore uses Cloudflare for SaaS Custom Hostnames to provision TLS certificates automatically:

1. When you run `lore domain add`, the API calls the Cloudflare Custom Hostnames API to register the hostname with `ssl.method: "http"` (HTTP DCV validation)
2. Cloudflare provisions a DV certificate for the hostname
3. The certificate auto-renews — no manual intervention needed
4. `cfSslStatus` values: `initializing` → `pending_validation` → `active`

If the CF4SaaS API is unavailable (missing env vars, API error), the domain is still created with `pending` status. Verification falls back to DNS-over-HTTPS resolution (checking that the CNAME resolves). The Worker can serve traffic once DNS points to `standalone.thelore.dev` regardless of CF4SaaS registration.

### Validation rules

- Domain must contain at least one dot (`dashboard.acme.com`, not `localhost`)
- No protocol prefix (`dashboard.acme.com`, not `https://dashboard.acme.com`)
- No path suffix (`dashboard.acme.com`, not `dashboard.acme.com/app`)
- The standalone app must exist before adding a domain
- Each domain can only be registered once across all orgs (UNIQUE constraint)

### Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `VALIDATION_ERROR` | 400 | Invalid domain format |
| `NOT_FOUND` | 404 | App or domain ID doesn't exist |
| `CONFLICT` | 409 | Domain already registered (by any org) |

### Troubleshooting

**Verify returns "DNS not configured":**
- CNAME record may not have propagated yet (can take up to 48 hours, usually minutes)
- Check with: `dig dashboard.acme.com CNAME` — should show `standalone.thelore.dev`
- If using Cloudflare DNS, make sure proxy status is "DNS only" (grey cloud)

**TLS stuck on `pending_validation`:**
- HTTP DCV validation requires the CNAME to be resolvable. Ensure DNS is configured first.
- If the customer's domain is behind another CDN/proxy, it may block the validation request
- Wait 15 minutes, then re-run `lore domain verify`

**Domain shows `active` but returns 404 in browser:**
- The standalone app may have been deleted after the domain was added
- Check: `lore app get-standalone <slug>` — if not found, re-publish the app

**"Domain is already registered" conflict:**
- Another org has already claimed this domain
- Each domain is globally unique — it cannot be shared across orgs

## Arrow.js Reactive Proxy Pitfall

Arrow.js `reactive()` wraps objects in Proxy. When you pass reactive data to plain DOM APIs (innerHTML, createElement, FormData), the proxy can silently break serialization.

**The rule:** Extract data from reactive state into plain JS before passing to non-Arrow code.

```javascript
// BAD — reactive proxy leaks into plain DOM
openDialog({ options: state.goals.map(g => ({ value: g.id, label: g.title })) })

// GOOD — extract to plain objects first
const options = []
for (const g of state.goals) {
  options.push({ value: String(g.id), label: String(g.title) })
}
openDialog({ options })
```

For dialogs and forms built with `document.createElement` (not Arrow.js `html` templates), keep form state in a **plain object** — not inside `reactive()`:

```javascript
// Plain object for dialog state — NOT reactive
const dialogState = { fields: [], submit: null }

// Only UI flags in reactive state
const state = reactive({ dialogOpen: false, dialogTitle: '' })
```

## Security Model

### Sandbox differences by app mode

| Mode | Sandbox | Cookies | DOM access |
|------|---------|---------|------------|
| **Single-file** | `allow-scripts allow-forms` | No | No |
| **Multi-file** | `allow-scripts allow-forms allow-top-navigation allow-same-origin` | Yes | Yes |

**Multi-file apps have broader sandbox permissions** because page-to-page navigation via `<a>` tags requires `allow-top-navigation`, and cookie persistence across page loads requires `allow-same-origin`. This means multi-file app code can access `document.cookie` and `window.parent` — it runs with the same privileges as the parent shell.

**This is safe because only admins and owners can publish standalone apps** (`requireAdminOrOwner()` middleware). The trust model assumes publishers don't inject malicious code. If you extend publishing to non-admin roles in the future, revisit the sandbox — consider postMessage-based navigation instead of `allow-top-navigation` + `allow-same-origin`.

### What app code should NOT do

- Don't read `document.cookie` to extract session tokens — use the SDK
- Don't manipulate `window.parent` — use `lore.api.*` for all data access
- Don't make direct `fetch()` calls to `/v1/*` endpoints — use the SDK bridge which handles auth

These are conventions, not enforced restrictions (due to `allow-same-origin`).

## Tips

- Error handling: wrap all API calls in try/catch
- The SDK uses postMessage under the hood — keep payloads JSON-serializable
- Use `lore.api.subscribe(table, callback)` for live updates instead of polling — subscribe to `'*'` for all tables
- Use Arrow.js `reactive()` for automatic DOM updates when data changes
- Use `createReactiveTable()` from `@lore/sdk` for the simplest reactive data binding
- Re-publishing the same slug bumps the version — old content is preserved in storage
- The app URL is `/apps/{org-slug}/{slug}` — for internal apps, share with org members; for external apps, share with your customers
- External apps enforce row-level filtering automatically — you don't need to add WHERE clauses for the current user
- External auth_config validates column existence at publish time — you'll get clear errors if columns are missing
- Rate limiting on external sign-in: 5 attempts per 15 minutes per email (DB-based, survives Worker restarts)
