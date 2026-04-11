# Validation Contract Format

The validation contract is the source of truth for mission completeness. It is
written **before** any features are defined, so it reflects requirements — not
the implementation plan.

## File: `validation-contract.md`

Each assertion follows this structure:

```markdown
## A<N>: <Short title>

- **Behavior**: <One sentence describing the expected behavior from the user's
  perspective. Must be testable — no vague qualifiers like "works well" or
  "is fast".>
- **Method**: <How this assertion will be verified>
  - `test-runner` — Run automated tests (unit, integration, e2e)
  - `cli-check` — Execute a CLI command and check output
  - `browser-agent` — Use Vercel's `agent-browser` to navigate UI, click through flows, and take screenshots
  - `agent-screencast` — Record a narrated video walkthrough of UI flows using the agent-screencast skill
  - `code-review` — A validator reads the code and confirms
  - `manual` — Requires human verification (last resort)
- **Evidence**: <What constitutes proof of correctness>
  - Passing test names/suites
  - Expected HTTP status codes or response shapes
  - Screenshots of specific UI states
  - Recorded video of a multi-step UI flow
  - CLI output matching a pattern
  - Specific files existing with expected content
```

## Choosing the Right Method

Pick the method that gives the **strongest evidence with the least ambiguity**
for each assertion. Use this decision order:

| If the assertion is about… | Prefer | Why |
|---|---|---|
| API behavior, data logic, auth, validation rules | `test-runner` | Deterministic, fast, repeatable. The gold standard when tests can cover the behavior. |
| A running process, build output, or env config | `cli-check` | Some things aren't unit-testable — server startup, CLI output, health checks. Run the command and check stdout/stderr. |
| A single UI state or interaction (login form works, button appears) | `browser-agent` | Uses Vercel's `agent-browser` to navigate, click, and screenshot. Best for verifying specific UI states or short interaction flows. |
| A multi-step UI flow (onboarding wizard, drag-and-drop reorder, complex dashboard interaction) | `agent-screencast` | Records a narrated video walkthrough using the agent-screencast skill. Captures temporal flows that a single screenshot can't prove — transitions, animations, multi-page sequences. |
| Internal structure (config shape, file existence, code conventions) | `code-review` | When the assertion is about what the code IS, not what it DOES. The validator reads source files directly. |
| Physical devices, third-party services, subjective quality | `manual` | Last resort. Use only when no automated method can verify the assertion. |

**Bias check:** Don't default everything to `test-runner`. API-only projects
will naturally be test-heavy, but projects with significant UI surface area
should use `browser-agent` and `agent-screencast` for UI assertions. A passing
test suite doesn't prove the UI actually renders correctly.

## Rules

1. **Finite and enumerable.** Every assertion is a discrete, checkable item.
   The contract is not a prose description — it is a checklist.

2. **Behavioral, not structural.** Assertions describe what the system does,
   not how the code is organized. "A user can log in" — not "There is a
   LoginController class."

3. **Independent.** Each assertion can be verified on its own. Avoid assertions
   that require other assertions to be checked first (if you must, note the
   dependency explicitly).

4. **Exhaustive for scope.** Every requirement from the intake phase must map
   to at least one assertion. If a requirement has no assertion, it will not
   be validated.

5. **No assertion without an owner.** During feature decomposition, every
   assertion must be claimed by at least one feature. Unclaimed assertions
   are dead requirements.

## Assertion Lifecycle

```
DRAFT  →  user approves  →  ACTIVE
                                ↓
                          feature claims it
                                ↓
                          worker implements
                                ↓
                          validator checks  →  PASS / FAIL
                                                  ↓ (if FAIL)
                                            fix-feature created
                                                  ↓
                                            re-validated  →  PASS
```

## Example

See `../samples/sample-contract.md` for a complete example.
