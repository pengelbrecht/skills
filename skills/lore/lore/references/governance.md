# Lore Governance Model

## How governance works

Every mutation in Lore flows through governance checks. This protects data integrity and ensures human oversight for structural changes.

## What's enforced

| Rule | Scope | Effect |
|------|-------|--------|
| No DDL in mutate | All mutations | DDL statements rejected; use `/v1/schema/propose` |
| System table protection | `_users`, `_knowledge`, `_access_policies`, etc. | Cannot INSERT/UPDATE/DELETE via API |
| Access policies | Per actor + scope | Checked before every operation |
| Approval workflow | Schema proposals | Human must approve before DDL executes |
| Audit trail | All mutations | Every change recorded in `_events` with actor attribution |

## Access policies

Policies are scoped by actor and table:

```
actor: "agent:mcp-agent"  scope: "customers"  permission: "read"
actor: "*"                 scope: "*"          permission: "admin"
```

Check your permissions: `GET /v1/permissions`

## Schema change workflow

1. Agent proposes: `POST /v1/schema/propose` with SQL + reason
2. Proposal enters approval queue: `GET /v1/pending`
3. Human reviews and approves/rejects (web UI or `lore approve <id>`)
4. On approval, Lore executes the DDL automatically
5. Rejection includes feedback — check before re-proposing

## Before proposing schema changes

Always check if similar proposals were previously rejected:

```bash
curl -s "$LORE_API_URL/v1/query" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT feedback, feedback_type FROM _approval_queue WHERE status = '\''rejected'\'' AND feedback IS NOT NULL ORDER BY reviewed_at DESC LIMIT 10"}'
```

This avoids re-proposing changes that humans already declined.
