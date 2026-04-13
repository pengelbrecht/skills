# Lore Knowledge System

## How knowledge works

Lore accumulates knowledge about your data over time. When an agent queries, Lore serves relevant knowledge from `/v1/context` to help the agent succeed on the first try.

## Knowledge types

| Type | Purpose | Example |
|------|---------|---------|
| `semantic` | What data means | "amount is stored in cents, divide by 100 for display" |
| `correction` | Fix misunderstandings | "status=lead means prospect, not existing customer" |
| `pattern` | Useful query templates | "SELECT stage, COUNT(*), SUM(value) FROM deals GROUP BY stage" |
| `rule` | Business constraints | "orders.total must never be negative" |

## The query-learn loop

1. **Read context** — `GET /v1/context?scope=<table>` returns all knowledge for a table
2. **Query with context** — use the knowledge to write correct SQL
3. **Learn from experience** — if you discover something new, `POST /v1/learn`
4. **Future agents benefit** — next agent to query that table gets your contribution

## Contributing knowledge

```bash
curl -s "$LORE_API_URL/v1/learn" \
  -H "Authorization: Bearer $LORE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "semantic", "scope": "orders", "content": "amount is stored in cents"}'
```

Required fields: `type`, `scope` (table name or "global"), `content`
Optional: `tables` (array of related table names, useful for patterns)

## Passive inference

Even without explicit learning calls:
- When context is read then a query succeeds, `usage_count` is bumped on the entries served
- When context is read then a correction is posted, confidence is reduced on contradicted entries
- Knowledge that is frequently used and rarely corrected rises in confidence automatically
