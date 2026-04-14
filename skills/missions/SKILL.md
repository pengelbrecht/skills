---
name: missions
description: >
  Break large engineering tasks into planned, validated missions executed by
  specialized agents. Use this skill whenever the user wants to tackle a task
  that is too large or complex for a single session — multi-feature work,
  full-stack buildouts, large refactors, or any project that benefits from
  structured planning, parallel execution, and independent validation.
  Triggers on phrases like "start a mission", "plan a mission", "mission to
  build X", "break this into milestones", "I need a structured plan for X",
  "orchestrate building X", "multi-step project", or any request that implies
  decomposing large work into validated stages. Also triggers on "/missions".
metadata:
  version: 0.1.0
---

# Missions

Break large engineering work into planned, validated missions executed by
specialized agents — each with clean context, tight scope, and independent
validation.

## Why This Exists

Single-agent sessions work well for narrow tasks, but real engineering work is
often too large and messy for one context window. As an agent accumulates
context, its focus and reliability degrade. Two specific failure modes:

- **Irrelevant context buildup.** Wide scope means the agent carries
  information that has nothing to do with its current sub-task. Signal-to-noise
  drops.
- **Self-evaluation bias.** An agent that just built something is a poor judge
  of whether it built it correctly. Its own reasoning biases it toward thinking
  what it did was right.

Missions addresses both: each worker gets a fresh, tightly-scoped context, and
correctness is judged by separate validators who never saw the implementation.

## Design Principles

1. **Separate concerns and incentives.** Each role has exactly one goal.
   Orchestrator plans. Workers implement. Validators judge. No role does
   another's job.
2. **Test-driven at two scales.** Workers write tests before code. The
   orchestrator writes a validation contract before defining features. Contract
   first, plan second — so the contract reflects requirements, not the plan.
3. **Externalize state.** No single agent holds the whole project. State lives
   in shared files. Each agent pulls only what's relevant.
4. **Specialize models by role.** Strong reasoner for orchestration (opus),
   reliable executor for workers (sonnet), thorough critic for validation
   (opus or sonnet).

---

## Prerequisites

The `mission.sh` shell library must be sourced before any mission operations.
It lives alongside this SKILL.md:

```bash
source "$(dirname "$0")/mission.sh"   # when running from skill dir
```

Or Claude Code can source it directly:

```bash
source /path/to/skills/missions/mission.sh
```

Required tools: `git`, `yq` (for YAML parsing — install via `brew install yq`
or `pip install yq`). If `yq` is not available, fall back to parsing YAML
manually in bash or have Claude read the files directly.

---

## Runtime Directory Structure

Missions live in a `./missions/` directory at the project root. Each mission
gets a numbered subdirectory:

```
./missions/
  001-add-auth/
    plan.yaml                   # Mission metadata + milestone ordering
    validation-contract.md      # Behavioral assertions — written FIRST
    features.json               # Feature specs, each claiming assertions
    AGENTS.md                   # Procedures + guardrails for workers
    knowledge/                  # Grows over time — validator learnings
      milestone-1-learnings.md
    status.yaml                 # Progress tracking (resumable)
  002-realtime-messaging/
    plan.yaml
    validation-contract.md
    ...
```

Add `missions/` to `.gitignore` or commit it — user's choice. The knowledge
files are valuable project artifacts worth keeping.

---

## Phase 1: Intake

When the user requests a mission, start an interactive planning conversation.
The goal is unambiguous requirements before any planning begins.

### Process

1. Ask the user to describe what they want built or changed.
2. Investigate the codebase — read key files, understand the stack, identify
   constraints. Delegate deep investigation to subagents to keep your own
   context lean.
3. Ask clarifying questions using the **AskUserQuestion** tool. Push for
   specifics on:
   - Scope boundaries (what's in, what's explicitly out)
   - Success criteria (how will we know it's done?)
   - Constraints (tech stack, existing patterns, performance requirements)
   - Dependencies (external services, APIs, existing code that must not break)
   Use AskUserQuestion for each clarification round rather than dumping all
   questions inline. This ensures the user sees a focused prompt and you get
   a clear answer before moving on.
4. Summarize the requirements back to the user (via AskUserQuestion) and get
   explicit confirmation before proceeding.

**Key rule:** Do NOT start planning until the user confirms the requirements
are correct and complete. Use AskUserQuestion to gate every transition between
phases — intake to contract, contract to decomposition, decomposition to
execution.

---

## Phase 2: Validation Contract

Before defining any features, write the validation contract. This is a finite
checklist of testable behavioral assertions that together define "done and
correct" for this mission.

### Why contract first

If you define features first and then derive a contract, the contract will be
subtly shaped by the implementation plan. Writing the contract first ensures it
reflects what the requirements actually demand.

### Contract format

Create `validation-contract.md` in the mission directory. Each assertion has:

| Field | Description |
|-------|-------------|
| **ID** | Unique identifier (A1, A2, ...) |
| **Behavior** | One-sentence behavioral description from the user's perspective |
| **Method** | How to verify — `test-runner`, `cli-check`, `browser-agent`, `agent-screencast`, `code-review`, `manual` |
| **Evidence** | What constitutes proof — passing tests, screenshots, specific output |

See `references/contract-format.md` for the full schema and
`samples/sample-contract.md` for an example.

### Process

1. Draft the contract based on confirmed requirements.
2. Present it to the user via **AskUserQuestion**: "Does this fully capture
   what 'done' means? Should any assertions be added, removed, or revised?"
3. Iterate until the user approves. Each revision round uses AskUserQuestion
   to present the updated contract and ask for confirmation.
4. Write the approved contract to the mission directory.

---

## Phase 3: Feature Decomposition

Break the work into bounded features, grouped into milestones.

### Features

Each feature is a self-contained unit of work that one worker can complete in
a single session. A feature:

- Has a clear description and acceptance criteria
- Claims one or more assertions from the validation contract
- Lists file paths it will likely touch (helps workers orient)
- Declares dependencies on other features (if any)

### Milestones

A milestone is a group of features that together produce a coherent chunk of
functionality. Every milestone ends with a validation gate — work doesn't
proceed to the next milestone until the current one passes validation.

### Ordering

- Features within a milestone can run in parallel if they have no dependencies
  on each other.
- Milestones run sequentially — each builds on the last.
- Order features so that foundational work (models, schemas, utilities) comes
  before features that depend on it.

### Process

1. Draft features and milestones based on the contract and requirements.
2. For each feature, note which contract assertions it satisfies. Every
   assertion must be claimed by at least one feature.
3. Present the plan to the user via **AskUserQuestion** for approval.
   Include the milestone structure, feature list, and parallelism decisions.
4. Write `features.json` and `plan.yaml` to the mission directory.

See `references/plan-format.md` for the file schemas.

---

## Phase 4: Shared State Setup

Create the remaining state files before execution begins.

### AGENTS.md

Worker procedures and guardrails. This file is included in every worker's
prompt. It contains:

- Project context (tech stack, directory structure, key patterns)
- Coding standards and conventions to follow
- Things to avoid (patterns, anti-patterns, known pitfalls)
- Test requirements (framework, coverage expectations, test-first mandate)
- How to signal completion or blockers

See `references/agents-template.md` for the template.

### status.yaml

Initialize with all features as `pending` and all milestones as `pending`.
This file is updated throughout execution and enables resuming interrupted
missions.

### knowledge/

Create the directory. It starts empty. Validators will populate it with
learnings as milestones complete.

### Shell setup

```bash
source /path/to/skills/missions/mission.sh
mission_init "add-auth"
# Creates: ./missions/001-add-auth/ with subdirectories
# Creates and checks out branch: mission/001-add-auth
```

**Note:** `mission_init` creates a dedicated `mission/<id>-<slug>` branch off
the current branch. All mission work happens on this branch. The parent branch
(e.g. `main`) is recorded in `plan.yaml` so the mission can be merged or PR'd
back when complete.

---

## Phase 5: Execution

This is the deterministic runner loop. Follow the plan mechanically — do not
improvise during execution.

### For each milestone

#### 5a. Launch agents for each feature

Each feature is implemented by a separate `Agent()` tool call with
`isolation: "worktree"`. The skill calls these "workers" — that's just a role
label, not a special system concept. A worker is an Agent subagent.

**Prompt construction** (see `references/worker-prompt.md` for template):

1. Include the feature spec from `features.json` (description, assertions,
   file hints)
2. Include `AGENTS.md` (procedures and guardrails)
3. Include relevant knowledge files from previous milestones
4. Instruct the agent to write tests FIRST, then implement
5. Instruct the agent to commit its work with a clear message

**Running features in parallel:** If features within a milestone have no
dependencies on each other, call multiple `Agent()` tools in a **single
response message**. Claude Code runs all Agent calls from one message
concurrently. Use `model: "sonnet"` unless the feature requires complex
reasoning.

Example — launching two independent features in parallel (both Agent calls
in the same response):

```
// Call 1 (in the same response)
Agent(
  description: "Feature F1: user model",
  isolation: "worktree",
  model: "sonnet",
  prompt: <constructed prompt for F1>
)

// Call 2 (in the same response — runs concurrently with Call 1)
Agent(
  description: "Feature F2: auth middleware",
  isolation: "worktree",
  model: "sonnet",
  prompt: <constructed prompt for F2>
)
```

**Sequential features:** If a feature depends on another (`dependencies` is
non-empty), wait for the dependency to complete and merge before launching
the dependent feature.

#### 5b. Merge completed worktrees

After each worker completes, if it made changes:
- The Agent tool returns the worktree branch name
- Merge the worker's branch back to the **mission branch**:

```bash
mission_merge <mission-dir> <branch-name>
```

Workers always merge into the mission branch (`mission/<id>-<slug>`), never
directly into the parent branch. This keeps all mission work isolated until
the full mission is validated and ready.

If merge conflicts occur, attempt to resolve them. If resolution requires
human judgment, use **AskUserQuestion** to present the conflict and ask
the user how to proceed.

#### 5c. Update status

After each feature completes, update `status.yaml`:

```bash
mission_feature_done <mission-dir> <feature-id>
```

---

## Phase 6: Validation

Once all features in a milestone are complete, run validation with fresh
agents. There are two types:

### 6a. Scrutiny validators

For each feature in the milestone, launch a scrutiny validator agent that:

1. Reads the feature's implementation (the actual code changes)
2. Reviews for quality, correctness, edge cases, and potential regressions
3. Writes learnings to `knowledge/milestone-N-learnings.md`
4. Reports issues as a structured list: `{severity, description, file, suggestion}`

Use `references/scrutiny-validator-prompt.md` for the prompt template.

### 6b. User-testing validators

Launch validator agents that interact with the built system as a black box:

1. Read the validation contract
2. For each assertion assigned to this milestone's features:
   - Execute the specified verification method (run tests, check CLI output, etc.)
   - Collect the required evidence
3. Report pass/fail for each assertion with evidence

Use `references/user-test-validator-prompt.md` for the prompt template.

**Parallelism:** Launch scrutiny and user-testing validators in parallel.
Use `model: "sonnet"` or `model: "opus"` depending on complexity.

---

## Phase 7: Fix Loop

If validation surfaces issues:

1. Read all validator reports.
2. For each actionable issue, create a targeted **fix-feature** — a small,
   scoped unit of work that addresses the specific problem.
3. Add fix-features to `features.json` with status `pending`.
4. Execute the fix-features (same as Phase 5 — worker agents with worktrees).
5. Re-run validation for the milestone.
6. Repeat until validation passes.

**Convergence expectation:** Most milestones converge in 2–4 validation rounds.
If a milestone hasn't converged after 4 rounds, escalate.

---

## Phase 8: Escalation

If something blocks that the system can't resolve:

- Merge conflicts that require human judgment
- Ambiguous requirements discovered during implementation
- Validation failures that persist after 4 fix rounds
- External dependencies that are unavailable

**Stop the mission**, preserve all state (status.yaml reflects exactly where
things stand), and use **AskUserQuestion** to present the blocker:

1. What was attempted
2. Why it failed
3. What the user needs to decide or provide
4. How to resume once the blocker is resolved

AskUserQuestion is essential here — it pauses execution and waits for the
user's input before continuing. Do not attempt to work around the blocker.

---

## Phase 9: Finalize

Once the full mission passes validation (all milestones complete), merge the
mission branch back to the parent branch or open a PR:

### Option A: Open a PR (recommended)

```bash
mission_pr <mission-dir>
# Pushes mission branch, opens PR against parent branch
```

### Option B: Direct merge

```bash
git checkout <parent-branch>
git merge mission/<id>-<slug> --no-ff -m "mission: complete <slug>"
```

Use **AskUserQuestion** to ask the user which approach they prefer before
finalizing.

---

## Resuming a Mission

Missions are resumable. To resume:

1. Read `status.yaml` to determine where execution stopped.
2. Read `features.json` to find pending/failed features.
3. Continue from the next incomplete feature or re-run the failed validation.

```bash
mission_status ./missions/001-add-auth
# Shows: Milestone 2/4, Feature 3/7 complete, validation pending
```

---

## Listing Missions

```bash
mission_list
# 001-add-auth        ✓ completed   2026-04-10
# 002-realtime-msgs   ◆ in-progress 2026-04-11  M2/F3
```

---

## Quick Reference: Shell Commands

| Command | Description |
|---------|-------------|
| `mission_init <slug>` | Create new mission directory |
| `mission_list` | List all missions with status |
| `mission_status <dir>` | Show detailed progress for a mission |
| `mission_feature_done <dir> <id>` | Mark feature complete in status.yaml |
| `mission_milestone_done <dir> <id>` | Mark milestone complete |
| `mission_merge <dir> <branch>` | Merge a worker's branch into mission branch |
| `mission_pr <dir>` | Push mission branch and open PR to parent branch |
| `mission_next_id` | Get next sequential mission number |

---

## Quick Reference: Agent Roles

| Role | Agent() params | Purpose |
|------|----------------|---------|
| Orchestrator | *(you — not a subagent)* | Plans, decomposes, manages execution |
| Worker | `model: "sonnet"`, `isolation: "worktree"` | Implements a single feature. Tests first. |
| Scrutiny validator | `model: "sonnet"` or `"opus"` | Reviews implementation quality, writes learnings |
| User-test validator | `model: "sonnet"` or `"opus"` | Black-box behavioral testing against contract |
| Research subagent | `model: "haiku"` or `"sonnet"` | Investigates codebase questions for orchestrator |

All roles except Orchestrator are `Agent()` tool calls. "Worker", "validator",
etc. are role labels in the prompt — not special system concepts. To run
agents in parallel, include multiple `Agent()` calls in a single response.
