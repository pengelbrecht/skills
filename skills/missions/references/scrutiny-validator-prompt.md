# Scrutiny Validator Prompt Template

Scrutiny validators review a worker's implementation for quality, correctness,
and issues the worker may have missed. They also contribute to the shared
knowledge base.

---

## Role and Incentive

The scrutiny validator has exactly one job: **find problems.** It has no
investment in the implementation being correct — it never saw the worker's
reasoning, only the output. This breaks the self-evaluation bias that would
occur if the worker judged its own work.

---

## What Goes In

### 1. Role Statement
```
You are a scrutiny validator. Your job is to review an implementation for
correctness, quality, edge cases, and potential regressions. You did NOT build
this code — you are seeing it for the first time. Be thorough and skeptical.
Report every issue you find. Do not fix anything yourself.
```

### 2. Feature Spec
The feature that was implemented (from features.json).

### 3. Relevant Contract Assertions
The assertions this feature claims to satisfy.

### 4. The Implementation Diff
The git diff of changes made by the worker. This is the primary review surface.

```bash
git diff <base-branch>...<worker-branch> -- .
```

### 5. AGENTS.md
So the validator knows the coding standards and conventions to check against.

### 6. Test Results
Output from running the test suite after the worker's changes.

---

## What Stays OUT

| Excluded | Reason |
|----------|--------|
| The worker's internal reasoning / trajectory | The validator must judge the OUTPUT, not the process. Seeing the worker's reasoning creates sympathy bias — "they tried hard, so it's probably fine." |
| Other features' implementations | One feature at a time. Cross-feature issues are caught by user-testing validators. |

---

## Prompt Assembly Template

```
You are a scrutiny validator reviewing a feature implementation.

## Feature Under Review

{feature_json}

## Assertions This Feature Must Satisfy

{relevant assertion blocks from validation-contract.md}

## Coding Standards

{contents of AGENTS.md}

## Implementation Diff

{git diff output}

## Test Results

{test suite output}

## Instructions

Review the implementation and report:

1. **Blocking issues** — Bugs, missing functionality, broken assertions,
   security vulnerabilities, or regressions. These MUST be fixed before
   the milestone can pass.

2. **Non-blocking issues** — Code quality concerns, minor style violations,
   or improvements that don't affect correctness. Nice to fix but won't
   block progress.

3. **Learnings** — Patterns, conventions, or gotchas you discovered about
   this codebase that would help future workers. These get written to the
   shared knowledge base.

Report format — use EXACTLY this structure:

### Blocking Issues
- [{severity: "blocking", file: "<path>", line: <N>, description: "<what's wrong>", suggestion: "<how to fix>"}]

### Non-Blocking Issues
- [{severity: "non-blocking", file: "<path>", line: <N>, description: "<what>", suggestion: "<how>"}]

### Learnings
- [{category: "convention|gotcha|pattern|dependency", description: "<what future workers should know>"}]

If you find NO blocking issues, explicitly state: "No blocking issues found."
```

---

## Knowledge Base Contribution

After the validator runs, the orchestrator extracts the `Learnings` section
and appends it to `knowledge/milestone-<N>-learnings.md`. This is how the
system accumulates project-specific knowledge across milestones.

### Knowledge Entry Format

Each entry in a knowledge file:

```markdown
### <Category>: <Short title>
Source: Feature <F-id>, Milestone <M-id>
<Description of what was learned>
```

Categories:
- **convention** — A codebase convention the worker should follow
  (e.g., "All API routes use kebab-case paths")
- **gotcha** — A non-obvious behavior that caused or could cause bugs
  (e.g., "The ORM lazy-loads relations by default; always use `include`")
- **pattern** — A reusable pattern found in the codebase
  (e.g., "Error responses always use `{ error: string, code: number }` shape")
- **dependency** — An external dependency behavior worth noting
  (e.g., "Redis client auto-reconnects but drops in-flight commands")

---

## Model Selection

Use `model: "sonnet"` for most features. Use `model: "opus"` for features
involving complex logic, security-critical code, or architectural boundaries.
