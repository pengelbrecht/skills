
## Orchestration

**Problem:** wave-2 merge conflicted; implementer worktrees diverged.
**Cause:** isolation worktrees branch from the default branch (main), not the epic integration branch.
**Rule:** every implementer prompt must start with `git merge <epic-branch> --no-edit` before building (per claude-runner template).
