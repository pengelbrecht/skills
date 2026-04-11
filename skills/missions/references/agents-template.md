# AGENTS.md Template

This template is used to generate the `AGENTS.md` file for each mission.
The orchestrator fills in project-specific details during Phase 4 (Shared
State Setup).

AGENTS.md is included in every worker's prompt. It provides the operating
context and guardrails that keep workers aligned with the project's conventions.

---

## Template

```markdown
# Mission Agents — Operating Procedures

## Project Context

- **Stack**: {e.g., Next.js 15, Prisma, PostgreSQL, Tailwind}
- **Directory structure**:
  {abbreviated tree of key directories}
- **Entry points**: {e.g., src/app/ for routes, src/lib/ for shared code}
- **Test framework**: {e.g., Vitest, pytest, Jest}
- **Test command**: {e.g., npm test, pytest -x}
- **Build command**: {e.g., npm run build}
- **Dev server**: {e.g., npm run dev → http://localhost:3000}

## Coding Standards

{Extracted from the project's existing patterns. Examples:}

- Use TypeScript strict mode. No `any` types.
- All API routes return `{ data: T }` on success, `{ error: string }` on failure.
- Use named exports, not default exports.
- Database queries go through the repository layer, never raw SQL in routes.
- Component files use PascalCase. Utility files use kebab-case.

## Test Requirements

- **Test first.** Write tests that encode expected behavior BEFORE writing
  implementation code. Tests should describe what the system does, not mirror
  how it's built.
- **Run the full suite** after implementation. Your changes must not break
  existing tests.
- **Coverage**: Aim for the project's existing coverage level. Do not skip
  edge cases.
- **Test location**: {e.g., colocated `*.test.ts` files, or `tests/` directory}

## Things to Avoid

{Project-specific anti-patterns. Examples:}

- Do NOT use `console.log` for error handling. Use the project's logger.
- Do NOT add new dependencies without noting it in your commit message.
- Do NOT modify migration files that have already been applied.
- Do NOT use `any` to work around type errors.

## Completion Protocol

When you finish your feature:

1. Run the test suite. All tests must pass.
2. Commit with message format: `mission(<feature-id>): <description>`
3. If blocked by something you cannot resolve:
   - Stop immediately.
   - Describe the blocker clearly: what you tried, why it failed, what you need.
   - Do NOT work around blockers with hacks or placeholder code.
```

---

## Filling In the Template

During Phase 4, the orchestrator should:

1. Read the project's existing configuration files (package.json, tsconfig,
   pyproject.toml, Makefile, etc.) to determine the stack and commands.
2. Read 2-3 representative source files to identify coding conventions.
3. Check for existing linter/formatter configs (.eslintrc, .prettierrc, ruff.toml).
4. Check for existing test files to determine test framework and patterns.
5. Populate the template with concrete, project-specific information.

The goal is that a worker reading AGENTS.md can start coding immediately
without needing to explore the project structure themselves.
