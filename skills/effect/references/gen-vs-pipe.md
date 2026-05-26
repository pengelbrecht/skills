# Gen vs Pipe Patterns

Source: Dillon Mulroy X thread, June 2025, on writing Effect with `Effect.gen` versus `.pipe(...)`: https://x.com/dillon_mulroy/status/1936530534936486009

Thread coverage: reviewed the full conversation returned by `bird thread` (29 tweets), including Dillon's 9-tweet main chain, the 7 attached code images, and related replies. The reusable guidance below is based on the main chain; replies only inform adoption notes where relevant.

Core rule:

```ts
Effect.gen(function* () {
  // business logic lives here
}).pipe(
  // composition happens here
)
```

Use `Effect.gen` when the code should read like a domain workflow. Use `.pipe(...)` when the code applies reusable operators to an Effect.

## Sequential Workflows

Prefer `Effect.gen` for multi-step operations with intermediate values.

```ts
const createUser = (userData) =>
  Effect.gen(function* () {
    const db = yield* Database
    const validated = yield* validateUserData(userData)
    const hashed = yield* hashPassword(validated.password)
    const user = yield* db.users.create({ ...validated, password: hashed })
    return yield* enrichUserData(user)
  })
```

Why: each line names the domain state. This is easier to review and onboard than a long chain.

## Conditional Logic

Use normal TypeScript control flow inside `Effect.gen`.

```ts
const processPayment = (payment) =>
  Effect.gen(function* () {
    const config = yield* Config

    if (payment.amount > config.largePaymentThreshold) {
      return yield* processLargePayment(payment)
    }

    return yield* processStandardPayment(payment)
  })
```

Avoid turning obvious branches into nested `Effect.flatMap`, `Effect.andThen`, or `Effect.map` chains.

## Layer Composition

Use `.pipe(...)` for layer and dependency composition.

```ts
const appLayer = Layer.empty.pipe(
  Layer.provide(Database.layer),
  Layer.provide(Logger.layer),
  Layer.provideMerge(Metrics.layer),
  Layer.provideMerge(Cache.layer)
)
```

Why: layers are composition, not business logic.

## Simple Transforms

Small local transforms can stay in `.pipe(...)`.

```ts
const usernames = yield* getActiveUsers().pipe(
  Effect.map((users) => users.map((user) => user.username))
)
```

Use this when each operator transforms the previous result directly. If the transform grows branches, multiple named values, or domain decisions, move it into `Effect.gen`.

## Business Logic Inside, Cross-Cutting Concerns Outside

Put the domain path in `Effect.gen`, then attach operational behavior in `.pipe(...)`.

```ts
const fetchUserPosts = (userId) =>
  Effect.gen(function* () {
    const db = yield* Database
    const cache = yield* Cache

    const cached = yield* cache.get(`posts:${userId}`)
    if (cached) return cached

    const posts = yield* db.posts.findByUser(userId)
    yield* cache.set(`posts:${userId}`, posts)

    return posts
  }).pipe(
    Effect.withSpan("fetch_user_posts"),
    Effect.retry(retryPolicy),
    Effect.catchTag("DatabaseError", () => Effect.succeed([]))
  )
```

Good pipe candidates:
- `Effect.withSpan`
- `Effect.retry`
- `Effect.timeout`
- `Effect.catchTag`
- `Effect.catchAll`
- `Effect.tap` for narrow logging/metrics
- `Effect.provide` / layer provisioning at edges

## Avoid Long andThen Chains

Do not express a domain workflow as a long chain just because it is possible.

```ts
// Avoid for business workflows.
Effect.succeed(order).pipe(
  Effect.andThen(validateOrder),
  Effect.andThen(calculateTotals),
  Effect.andThen(applyDiscounts),
  Effect.andThen(processPayment),
  Effect.andThen(sendConfirmation)
)
```

Prefer:

```ts
Effect.gen(function* () {
  const validated = yield* validateOrder(order)
  const withTotals = yield* calculateTotals(validated)
  const discounted = yield* applyDiscounts(withTotals)
  const payment = yield* processPayment(discounted)

  return yield* sendConfirmation(payment)
})
```

## Review Checklist

When reviewing Effect code, ask:

- Can a TypeScript developer read the business path top-to-bottom?
- Are dependencies retrieved near where they are used?
- Are domain branches expressed with normal control flow?
- Are operational concerns outside the core logic?
- Are expected failures typed and catchable by tag?
- Are simple transforms left as simple transforms?
- Would a named intermediate value make the code easier to understand?

## Adoption Note

One reply asked about onboarding less experienced developers. Dillon's answer: the perceived ramp-up is higher than the actual ramp-up, and most developers become productive in a few days. Treat this as a style constraint: prefer Effect code that looks like readable TypeScript first. Reach for clever composition only when it materially improves the program.
