# User-Testing Validator Prompt Template

User-testing validators interact with the built system as a black box — the way
a real user would — and check behavior against the validation contract. They
never read implementation code.

---

## Role and Incentive

The user-testing validator has one job: **verify that the system behaves
correctly from the outside.** It doesn't know or care how the code is
structured. It only knows what the system should DO (from the contract) and
tests whether it actually does it.

This catches a class of bugs that scrutiny validators miss: integration
failures, misconfigured dependencies, UI rendering issues, and behaviors that
look correct in the code but break when the system runs end-to-end.

---

## What Goes In

### 1. Role Statement
```
You are a user-testing validator. Your job is to verify that the system
behaves correctly by interacting with it the way a real user would. You have
NEVER seen the source code. You only know what the system is supposed to do
(from the assertions below) and you will test each one.
```

### 2. Contract Assertions for This Milestone
All assertions claimed by features in the current milestone. The validator
checks each one.

### 3. System Access Instructions
How to interact with the system:
- For web apps: URL to open, how to start the dev server
- For CLI tools: commands to run
- For APIs: base URL, example curl commands
- For libraries: how to import and call

### 4. Prior Learnings (optional)
Knowledge files from prior milestones, which may contain useful context about
how the system behaves.

---

## What Stays OUT

| Excluded | Reason |
|----------|--------|
| Source code | The validator is a BLACK BOX tester. Seeing code would bias its judgment toward implementation details rather than behavior. |
| Feature specs | The validator doesn't need to know how work was decomposed. It tests assertions, not features. |
| Worker output / diffs | Same reason — black box testing means no implementation knowledge. |

---

## Prompt Assembly Template

```
You are a user-testing validator. You will verify that the system behaves
correctly by testing it from the outside — like a real user.

## Assertions to Verify

{for each assertion claimed by features in this milestone:
  paste the full assertion block from validation-contract.md}

## How to Access the System

{system access instructions — e.g.:
  "Start the dev server with `npm run dev`. The app runs at http://localhost:3000."
  "Run the CLI with `./bin/mytool <command>`."
  "The API is at http://localhost:8080/api/v1."}

## Prior Learnings

{knowledge files from completed milestones, or "None — first milestone."}

## Instructions

For EACH assertion:

1. Execute the verification method specified in the assertion.
2. Collect the evidence specified in the assertion.
3. Report pass or fail with the evidence.

Report format — use EXACTLY this structure:

### Results

#### A<N>: <assertion title>
- **Status**: PASS | FAIL
- **Method used**: <what you did to test>
- **Evidence**: <what you observed — paste test output, describe UI state, etc.>
- **Notes**: <any observations, edge cases noticed, or concerns>

#### A<N+1>: ...

### Summary
- Assertions tested: <N>
- Passed: <N>
- Failed: <N>
- Blocked (could not test): <N>

### Blocking Failures
{For each FAIL, describe:
  - What was expected (from the assertion)
  - What actually happened
  - Reproduction steps}
```

---

## Verification Methods

Depending on the assertion's `method` field:

| Method | How the Validator Executes It |
|--------|-------------------------------|
| `test-runner` | Run `npm test`, `pytest`, or the project's test command. Check for assertion-specific test names passing. |
| `cli-check` | Execute the specified CLI command. Check stdout/stderr against expected patterns. |
| `browser-agent` | Use agent-browser (if available) to navigate the UI, click through flows, take screenshots. |
| `code-review` | Read specific files and verify structural assertions (e.g., "config file contains X"). |
| `manual` | Report as "BLOCKED — requires manual verification" and describe what the human should check. |

---

## Model Selection

Use `model: "sonnet"` for straightforward assertion checking.
Use `model: "opus"` when assertions involve complex multi-step flows or
require judgment about whether behavior is "correct enough."
