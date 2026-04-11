# Validation Contract — Task Management API

## A1: User registration

- **Behavior**: A new user can register with an email and password. The API
  returns a 201 with a user object (id, email, created_at). Duplicate emails
  are rejected with a 409.
- **Method**: test-runner
- **Evidence**: Passing tests for successful registration and duplicate rejection.
  Response body matches `{ data: { id: string, email: string, created_at: string } }`.

## A2: User login

- **Behavior**: A registered user can log in with correct credentials and
  receives a JWT. Invalid credentials return 401.
- **Method**: test-runner
- **Evidence**: Passing tests for valid login (200 + token) and invalid login (401).

## A3: Token-protected routes

- **Behavior**: API routes under `/api/tasks` require a valid JWT in the
  Authorization header. Requests without a token or with an expired token
  receive 401.
- **Method**: test-runner
- **Evidence**: Passing tests for authenticated access (200), missing token (401),
  and expired token (401).

## A4: Create a task

- **Behavior**: An authenticated user can create a task with a title and
  optional description. The API returns 201 with the created task. The task
  belongs to the authenticated user.
- **Method**: test-runner
- **Evidence**: Passing test. Response includes `{ data: { id, title, description, user_id, status, created_at } }`.

## A5: List own tasks

- **Behavior**: An authenticated user can list their tasks. They see only their
  own tasks, not other users'. Results are paginated (default 20 per page).
- **Method**: test-runner
- **Evidence**: Passing tests for listing with pagination and user isolation.

## A6: Update task status

- **Behavior**: An authenticated user can update a task's status to "in_progress"
  or "completed". Updating another user's task returns 403.
- **Method**: test-runner
- **Evidence**: Passing tests for status update (200), invalid status (400),
  and forbidden update (403).

## A7: Delete a task

- **Behavior**: An authenticated user can delete their own task. Deleting
  another user's task returns 403. Deleting a non-existent task returns 404.
- **Method**: test-runner
- **Evidence**: Passing tests for delete (204), forbidden (403), not found (404).

## A8: Dev server starts clean

- **Behavior**: Running `npm run dev` starts the server without errors.
  The health endpoint at `GET /api/health` returns 200.
- **Method**: cli-check
- **Evidence**: Server process starts. `curl http://localhost:3000/api/health`
  returns `{ status: "ok" }`.
