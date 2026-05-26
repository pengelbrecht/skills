---
name: effect
description: Write, review, refactor, and explain TypeScript code that uses the Effect library. Use when working with Effect, Effect.gen, yield*, pipe, Layer, Context services, typed errors, retries, spans, dependency injection, or when converting Promise/async/await or imperative TypeScript into readable Effect code. Triggers on "Effect", "effect-ts", "Effect.gen", "yield*", ".pipe", "Layer", "Context.Tag", "catchTag", "withSpan", "retry", "typed errors", or requests to make Effect code easier to read or adopt.
---

# Effect

Use this skill to write Effect code that reads like normal TypeScript where business logic matters, while still using Effect's composition model for errors, observability, retries, layers, and dependency wiring.

## First Steps

1. Inspect the project before editing:
   - Check `package.json` for `effect`, `@effect/*`, TypeScript settings, test scripts, and lint/typecheck commands.
   - Search existing code for `Effect.gen`, `pipe`, `Layer`, `Context.Tag`, `Data.TaggedError`, and `catchTag`.
   - Match the repo's import style and Effect version. Do not introduce a second style casually.
2. If the task is nontrivial, read [Gen vs Pipe Patterns](references/gen-vs-pipe.md) before changing code.
3. Prefer a small typed Effect boundary over rewriting an entire module. Keep normal synchronous pure helpers as plain functions unless Effect adds real value.

## Style Rule

Use `Effect.gen` for business logic and `.pipe(...)` for composition.

```ts
const program = Effect.gen(function* () {
  // business flow, dependencies, branching, sequential steps
}).pipe(
  // composition: tracing, retry, error recovery, layer provisioning
)
```

## Decision Matrix

Use `Effect.gen` for:

- Injecting or retrieving dependencies with `yield* Service`.
- Sequential workflows where intermediate values matter.
- Conditional logic, branching, early returns, loops, and local variables.
- Business/domain logic that should be easy for a TypeScript developer to read.
- Interacting with the results of multiple Effect programs.

Use `.pipe(...)` for:

- Mapping or transforming the immediate result of one Effect.
- Error handling and recovery (`Effect.catchTag`, `Effect.catchAll`, `Effect.mapError`).
- Retry, timeout, schedule, tracing, logging, and spans.
- Layer building and dependency composition.
- Providing dependencies at the program edge.

Avoid:

- Long `Effect.andThen` chains for domain workflows.
- Hiding branches inside nested `flatMap`/`andThen` when `if` inside `Effect.gen` is clearer.
- Wrapping every pure helper in Effect. Pure functions are still useful.
- Throwing raw exceptions from business logic. Model expected failures as typed errors.

## Implementation Workflow

### 1. Model Services

Use the service pattern already present in the repo. If there is no local convention, prefer `Context.Tag` plus a live `Layer`.

```ts
class Database extends Context.Tag("Database")<
  Database,
  { readonly users: { create: (input: UserInput) => Effect.Effect<User, DatabaseError> } }
>() {}
```

Retrieve services inside `Effect.gen`:

```ts
const db = yield* Database
```

### 2. Model Expected Errors

Use tagged errors for domain and infrastructure failures. Keep error names stable and specific enough for `catchTag`.

```ts
class UserValidationError extends Data.TaggedError("UserValidationError")<{
  readonly message: string
}> {}
```

When wrapping Promises, map unknown failures immediately:

```ts
Effect.tryPromise({
  try: () => client.fetchUser(id),
  catch: (cause) => new UserFetchError({ cause })
})
```

### 3. Write Business Logic With Gen

Keep the happy path and domain branches in one readable block.

```ts
const createUser = (input: UserInput) =>
  Effect.gen(function* () {
    const db = yield* Database
    const validated = yield* validateUserInput(input)
    const hashed = yield* hashPassword(validated.password)
    const user = yield* db.users.create({ ...validated, password: hashed })

    return yield* enrichUser(user)
  })
```

### 4. Add Cross-Cutting Behavior With Pipe

Attach retry, spans, logging, and recovery outside the business flow.

```ts
const createUserProgram = createUser(input).pipe(
  Effect.withSpan("create_user"),
  Effect.retry(retryPolicy),
  Effect.catchTag("UserAlreadyExistsError", () => Effect.succeed(null))
)
```

### 5. Compose Layers At The Edge

Keep dependency assembly separate from business logic.

```ts
const AppLayer = Layer.empty.pipe(
  Layer.provide(DatabaseLive),
  Layer.provide(LoggerLive),
  Layer.provideMerge(CacheLive)
)
```

## Refactoring Heuristics

- If a pipeline has 3+ sequential domain steps and named intermediate values would help, convert it to `Effect.gen`.
- If a `gen` block ends with several operators that do not affect the domain path, move those operators to `.pipe(...)`.
- If code uses `try/catch` around async operations, convert the async boundary with `Effect.tryPromise` and model the error.
- If code mixes dependency construction with domain logic, extract a `Layer` or service and inject it.
- If onboarding is the concern, optimize for boring readability over point-free elegance.

## Validation

After editing Effect code, run the smallest meaningful project checks:

```bash
pnpm test
pnpm typecheck
pnpm lint
```

Use the actual package manager/scripts from the repo. If no checks exist, run `tsc --noEmit` when available or at least inspect affected imports and inferred error/environment types.

## References

- [Gen vs Pipe Patterns](references/gen-vs-pipe.md): detailed thread-derived examples and refactoring patterns.
