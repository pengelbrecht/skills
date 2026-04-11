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
  - `browser-agent` — Launch a browser agent to interact with UI
  - `code-review` — A validator reads the code and confirms
  - `manual` — Requires human verification (last resort)
- **Evidence**: <What constitutes proof of correctness>
  - Passing test names/suites
  - Expected HTTP status codes or response shapes
  - Screenshots of specific UI states
  - CLI output matching a pattern
  - Specific files existing with expected content
```

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
