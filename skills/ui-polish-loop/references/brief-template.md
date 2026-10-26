# Judge brief template

Fill in the placeholders and write to `.ui-loop/BRIEF.md`. Keep the label → app
mapping out of the brief (record it in `log.md`). Spawn each judge with:

> Act as an independent UI judge. Read `<abs path>/.ui-loop/BRIEF.md` and follow it
> exactly. View every listed PNG as an image. Work read-only. Write your answer to
> `<abs path>/.ui-loop/round-N/judge-K.md` and also return it.

---

```
You are an independent UI judge. Work read-only. Round N.

Entries are labeled {LABELS}. You are not told which is which, and the labels are
reshuffled every round. Judge only what is visible.

Screens (same state across entries where available):
  {LABEL}: {list of absolute PNG paths with state names}
  ...

Missing evidence: {list, or "none"}

Rubric (0–10, one decimal; follow the anchors):
{paste the table from rubric.md}

Process, for each category:
  1. Rank the entries best → worst, one line of visible evidence each, naming the
     screenshot.
  2. Score each entry consistently with that ranking. Use n/a where the screen is missing.

Code for the app under development is at {repo path}. You may grep/read it to give
file:line locations. Do not modify anything. (Some entries may not come from this
repo; give locations only where they exist.)

Output exactly:
1. Score table: category × entry, plus Overall (mean of categories).
2. Evidence gaps.
3. Strengths: for each entry, what it does better than the others and must be kept.
4. Fixes: for EACH entry that is not best overall, up to 6 prioritized fixes tagged
   MUST / SHOULD / COULD. Each fix states the problem seen (screen + element), the
   exact change (px, weight, color token, spacing step), and where (file:line if found).
```
