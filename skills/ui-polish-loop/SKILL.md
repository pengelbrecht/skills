---
name: ui-polish-loop
description: >
  Iteratively improve a web app's UI with a capture → judge → fix loop: agent-browser
  screenshots, scored by independent, blinded, read-only judge sub-agents against an
  anchored rubric, then concrete fixes, repeated until a stopping rule fires. Works in
  two modes: benchmark (compare against reference apps) or solo (just keep improving
  the app against its own baseline). Use when the user asks to polish, refine, or
  "make the UI better", compare their UI to another product, run a design review loop,
  or score UI quality over several rounds.
---

# UI Polish Loop

A loop of **capture → judge → fix → re-capture**. You (the implementer) never grade
your own work: fresh, read-only judge sub-agents do, blinded, against a fixed rubric
and fixed anchor screenshots. Judging quality is what makes or breaks this loop, so
most of the rules below exist to keep scores honest and comparable across rounds.

## Prerequisites

```bash
agent-browser --version || echo "MISSING: npm i -g agent-browser && agent-browser install"
```

If missing, stop and tell the user. Run agent-browser commands **sequentially**
(they share a session). If a subcommand below differs in the installed version,
check `agent-browser --help` rather than falling back to raw Playwright.

## 0. Setup (once)

Settle with the user (infer from the repo where you can):

| Item | Default |
|---|---|
| Mode | **solo** unless the user supplies reference apps → **benchmark** |
| Run command / URL | from `package.json` scripts |
| Screens × states | 3–6, e.g. empty state, populated list, main task view, settings; × dark/light if both exist |
| References (benchmark) | 1–3 products, screenshots in the same states, supplied by the user or captured from public URLs |
| Max rounds | 4 |
| Scope fence | which dirs the fixes may touch (e.g. `src/components/**`, styles/tokens) |

Create the work dir `.ui-loop/` in the project root (add to `.gitignore`):

```
.ui-loop/
  capture.sh        # written once, replayed every round (see references/capture.md)
  baseline/         # starting state; captured once, never overwritten
  refs/<name>/      # benchmark mode only; never changes
  round-N/          # current branch each round
  round-N/judge-{1,2,3}.md
  BRIEF.md          # judge brief for the current round (references/brief-template.md)
  scores.csv        # round,judge,label,app,category,score
  log.md            # fixes applied/rejected per round, stop decision
```

Write `capture.sh` and run it for `baseline/` (and refs if capturable). Look at the
baseline images yourself once to confirm every state actually rendered.

## 1. Capture

Replay `capture.sh` into `round-N/`. Determinism matters more than anything else
here — if two rounds differ in data, viewport, or timing, the judges are scoring
noise. Rules are in `references/capture.md`. If a state can't be reached, record it
as missing in the brief; never substitute a different screen.

## 2. Judge

Spawn **3 judge sub-agents in parallel**, fresh context, read-only, given only
`BRIEF.md`. They do not see the diff, your reasoning, or earlier rounds' fixes.

Build the brief from `references/brief-template.md` with the rubric from
`references/rubric.md`. Core calibration rules:

- **Blind labels.** Apps/versions are A, B, C… with the mapping reshuffled every
  round and kept only in `log.md`. The judge must not know which is "current" —
  this removes the pull to reward change for its own sake.
- **Fixes for every non-best entry.** Asking for fixes for all of them keeps the
  judge from inferring which is the target.
- **Pairwise first, scores second.** Per category, rank the entries with one line of
  visible evidence each, then score consistent with the ranking.
- **Anchored rubric, evidence or abstain.** Scores follow the written 5/7/9 anchors;
  each cites an element in a named screenshot; missing evidence → `n/a`.
- **Concrete fixes.** Exact values (px, weight, token, spacing step), component,
  and file:line found by read-only grep of the repo.

### What the judges see, per mode

| | Benchmark | Solo |
|---|---|---|
| Entries | baseline, current, each reference | baseline, previous round, current |
| Fixed anchor (drift check) | references | baseline |
| Primary signal | current vs. best reference | current vs. previous round (pairwise) |

### Aggregate

- **Median** per category per entry across the 3 judges. Overall = mean of category medians.
- **Disagreement:** a category where judges spread > 1.0 → re-judge just that
  category with a 4th agent before acting on it.
- **Drift check:** the fixed anchor never changes, so its median should stay within
  ±0.3 of round 1. If it moves more, this round's judging is uncalibrated: discard
  and re-run the judges (once; if it drifts again, stop and report).
- **Pairwise win rate** (solo, and benchmark from round 2): fraction of
  judge × category comparisons where current beats previous round.

Append everything to `scores.csv`.

## 3. Fix

Unblind (via `log.md`). Build the fix queue:

1. Fixes raised by ≥ 2 judges, MUST before SHOULD.
2. Drop anything that contradicts a strength judges listed for the current version.
3. Drop anything outside the scope fence; note it in `log.md` for the user.

Apply in small, attributable commits — one per fix, message `ui-loop rN: <fix id> <summary>`.
Do not refactor along the way.

## 4. Decide: continue or stop

After re-capturing and re-judging round N+1, check in this order:

1. **Regression guard** — any category median drops > 0.3 vs. the previous round →
   revert the commit(s) most plausibly responsible, re-capture, re-judge. Doesn't
   count as a round.
2. **Stop** if any of these holds:

| Rule | Benchmark | Solo |
|---|---|---|
| Target reached | current overall ≥ best reference − 0.2 (or the user's target) | every category ≥ 8.5 **and** win rate vs. baseline ≥ 90% |
| Plateau | overall gain < 0.1 for 2 consecutive rounds | win rate vs. previous round < 60% for 2 consecutive rounds |
| Empty queue | no MUST/SHOULD raised by ≥ 2 judges | same |
| Budget | max rounds reached | same |
| Calibration failure | anchor drift twice in a row | same |

Solo mode deliberately leans on pairwise win rate rather than absolute scores:
without an external reference, absolute numbers creep upward round over round,
while "is this better than last round?" stays answerable.

Record the rule that fired in `log.md`.

## 5. Report

Give the user:

- A small line chart of overall score per round (current, baseline, references).
- Fixes applied, fixes rejected and why (including out-of-scope ones).
- Before/after image pairs for the 2–3 most changed screens.
- Which stopping rule fired, and what the judges would do next if the loop continued.
