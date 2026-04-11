# Plan & Features Format

Two files define the mission plan: `plan.yaml` for structure and ordering,
`features.json` for the detailed feature specs.

---

## File: `plan.yaml`

```yaml
mission: "add-auth"               # slug
id: 1                             # sequential ID
created: "2026-04-11"
base_branch: "main"               # git branch this mission builds on
status: planning                  # planning | executing | validating | completed | blocked

milestones:
  - id: M1
    name: "Database foundation"
    description: "Schema, models, and migrations for auth entities"
    features: [F1, F2]            # ordered — F1 before F2 unless parallel
    parallel: false               # can features run in parallel?
    status: pending               # pending | executing | validating | completed

  - id: M2
    name: "Auth API"
    description: "Registration, login, session management endpoints"
    features: [F3, F4, F5]
    parallel: true                # F3, F4, F5 have no interdependencies
    status: pending
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `mission` | yes | Slug identifier |
| `id` | yes | Sequential number |
| `created` | yes | ISO date |
| `base_branch` | yes | Git branch to build on |
| `status` | yes | Overall mission status |
| `milestones` | yes | Ordered list of milestones |
| `milestones[].id` | yes | Unique ID (M1, M2, ...) |
| `milestones[].name` | yes | Human-readable name |
| `milestones[].features` | yes | Ordered list of feature IDs |
| `milestones[].parallel` | yes | Whether features can run concurrently |
| `milestones[].status` | yes | Milestone status |

---

## File: `features.json`

```json
[
  {
    "id": "F1",
    "milestone": "M1",
    "name": "User model and migration",
    "description": "Create users table with email (unique), password_hash, created_at, updated_at. Add Prisma model and generate migration.",
    "assertions": ["A1", "A2"],
    "dependencies": [],
    "files_hint": ["prisma/schema.prisma", "prisma/migrations/"],
    "status": "pending",
    "type": "implementation"
  },
  {
    "id": "F1-fix-1",
    "milestone": "M1",
    "name": "Fix: missing email uniqueness constraint",
    "description": "Validator found that email uniqueness is not enforced at the DB level. Add unique constraint to users.email.",
    "assertions": ["A1"],
    "dependencies": ["F1"],
    "files_hint": ["prisma/schema.prisma"],
    "status": "pending",
    "type": "fix"
  }
]
```

### Feature Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique ID. Implementation features: `F<N>`. Fix features: `F<N>-fix-<M>` |
| `milestone` | yes | Which milestone this belongs to |
| `name` | yes | Short descriptive name |
| `description` | yes | Detailed spec — what the worker needs to know |
| `assertions` | yes | Which contract assertions this feature satisfies |
| `dependencies` | yes | Feature IDs that must complete first (empty array if none) |
| `files_hint` | no | Likely file paths (helps workers orient quickly) |
| `status` | yes | `pending`, `in_progress`, `completed`, `failed` |
| `type` | yes | `implementation` or `fix` |

### Rules

1. Every assertion in the contract must appear in at least one feature's
   `assertions` array.
2. Fix-features are added during the fix loop (Phase 7), not during initial
   planning.
3. Dependencies must reference features within the same milestone.
   Cross-milestone dependencies are handled by milestone ordering.
