---
type: decision
source: canonical
covers: [skills/repo-wiki/**, repo-wiki/INDEX.md]
verified_against: 2cb8fa3
status: active
---

## Compiled Truth

The wiki's write policy is **apply-and-report**, not propose-not-apply. Agents write
changes to `repo-wiki/` **directly** — they do not block to ask permission first. Git
review is the safety net: every change is already a reviewable, revertable diff, and in a
single-maintainer repo the "proposal" and the reviewed commit are the same artifact, so a
pre-write approval gate is pure friction that buys nothing.

The human stays in the loop via **reporting + revert**, not pre-approval: an agent
**names significant writes** in its turn (a new page, a rewritten Compiled Truth, a
superseded decision) so the user can review or `git`-revert. Trivial writes (a Timeline
append, a dedup, a `from-code` refresh) are silent. Decisions remain append-only —
supersede, don't edit.

This supersedes the **propose-not-apply** principle from [[0002-repo-wiki-design-principles]].
The `source` axis (`canonical` / `from-code` / `from-doc`) is **retained** — but only as a
*recoverability* label that drives the freshness model, not as a gate on the act of
writing. (Previously `canonical` rewrites were flagged for a human; now they're applied
and reported like everything else.)

**Why the reversal:** the owner found "always propose" didn't make sense — it asks on
every write when the real risk is narrow. The chosen point on the spectrum is maximum
freedom (apply everything, including canonical) with report-and-revert as the check,
rather than a confidence gate on canonical claims. The owner accepts that an occasional
wrong canonical write is caught at diff-review and reverted, in exchange for zero write
friction.

**Rejected alternatives:**
- *Keep propose-not-apply* — too much friction; the git diff already is the proposal.
- *Confidence-gated on canonical* (apply freely, ask before inventing/rewriting an
  uncertain canonical claim) — considered and declined: the owner wanted no ask-first
  path at all, trusting diff review to catch the rare bad canonical write.
- *Free except canonical edits* (always ask before touching an existing canonical page) —
  declined for the same reason.

## Timeline

- 2026-06-23 — owner: "propose don't add doesn't make sense — I want agents to freely
  update, only ask when in doubt", then chose full freedom ("apply everything, never
  ask") with the refinement "if an agent makes significant changes it should inform the
  user, so the user can ask to change/undo." — verified @ebe5cdf
