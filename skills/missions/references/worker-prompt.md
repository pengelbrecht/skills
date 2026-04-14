# Worker Prompt Template

A "worker" is an `Agent()` subagent call with `isolation: "worktree"` — not a
special system concept. This template defines what goes into the agent's
prompt — and critically, what stays OUT. Context isolation is the single most
important property of a well-functioning worker agent.

---

## What Goes In (and why)

The worker prompt is assembled from exactly these pieces, in this order:

### 1. Role Statement
```
You are a worker agent on a mission. Your sole job is to implement the feature
described below. Write tests first, then implement. Commit your work when done.
Do not investigate or plan beyond your feature scope.
```

### 2. Feature Spec (from features.json)
The single feature object for this worker. Includes:
- `name` and `description` — what to build
- `assertions` — which contract assertions this feature must satisfy
- `files_hint` — where to start looking
- `dependencies` — what has already been built (for context, not for re-doing)

### 3. Relevant Contract Assertions
Only the assertions listed in this feature's `assertions` array. Not the full
contract — the worker doesn't need to know about assertions belonging to other
features.

### 4. AGENTS.md (procedures and guardrails)
The full AGENTS.md file. This gives the worker:
- Project context (tech stack, directory structure)
- Coding standards to follow
- Test requirements
- Things to avoid

### 5. Knowledge from Prior Milestones
If this is milestone 2+, include the knowledge files from all completed
milestones. These contain learnings from validators — bug patterns, codebase
conventions, integration gotchas. This is how the system gets smarter over time.

Only include knowledge from *completed* milestones, not the current one.

---

## What Stays OUT (and why)

| Excluded | Reason |
|----------|--------|
| The full feature list | Worker doesn't need to know about other features. Seeing them invites scope creep and pollutes context. |
| The full validation contract | Worker only needs its own assertions. Other assertions are noise. |
| Other workers' code or output | Fresh context means no bias from other implementations. |
| The mission plan / milestone structure | The worker doesn't need to know where it fits in the big picture. It just builds its feature. |
| Orchestrator reasoning / planning notes | Implementation details of the planning phase are irrelevant to building code. |

---

## Prompt Assembly Template

```
You are a worker agent executing a feature for an engineering mission.

## Your Feature

{feature_json — the single feature object from features.json}

## Success Criteria

Your feature must satisfy these behavioral assertions:

{for each assertion_id in feature.assertions:
  paste the assertion block from validation-contract.md}

## Procedures

{contents of AGENTS.md}

## Prior Learnings

{contents of knowledge/milestone-*-learnings.md from completed milestones,
 or "No prior learnings — this is the first milestone." if milestone 1}

## Instructions

1. Read the files listed in files_hint to orient yourself.
2. Write tests FIRST that encode the expected behavior from the assertions.
3. Implement the feature until the tests pass.
4. Run the full test suite to check for regressions.
5. Commit your work with a message in the format:
   "mission(<feature-id>): <short description>"
6. If you encounter a blocker you cannot resolve, stop and report it clearly.
   Do NOT work around blockers with hacks.

Do not modify files outside your feature's scope unless absolutely necessary
for your feature to work. If you must touch shared code, note it explicitly
in your commit message.
```

---

## Model Selection

Use `model: "sonnet"` for workers by default. Use `model: "opus"` only for
features flagged as architecturally complex during planning.

## Isolation

Always use `isolation: "worktree"`. Every worker gets a clean git worktree.
This means:
- Workers can't see each other's uncommitted changes
- Merge happens after the worker completes
- If the worker makes no changes, the worktree is auto-cleaned
