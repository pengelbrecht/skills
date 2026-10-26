# Deterministic capture with agent-browser

`capture.sh` is written once in setup and replayed unchanged every round:

```bash
#!/usr/bin/env bash
# usage: capture.sh <out-dir>
set -euo pipefail
OUT="$1"; mkdir -p "$OUT"
AB="agent-browser --session ui-loop"
URL="${UI_LOOP_URL:-http://localhost:3000}"

$AB open "$URL"
$AB set viewport 1440 900
$AB set media dark
$AB wait --load networkidle
# kill animations/transitions and the blinking caret so frames are stable
echo 'var s=document.createElement("style");s.textContent="*,*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent!important}";document.head.appendChild(s)' | $AB eval --stdin

# --- state: empty ---
$AB screenshot "$OUT/empty-dark.png"

# --- state: populated sidebar --- (navigate/click with stable selectors)
$AB open "$URL/threads"
$AB wait --load networkidle
$AB screenshot "$OUT/sidebar-dark.png"

# ...repeat per state, then switch media for light:
$AB set media light
# ...

$AB close
```

Rules:

- **Same viewport, scale, theme, fonts, and file names every round.**
- **Seeded data.** Use fixtures, a seed script, or a mock API so lists, names, and
  timestamps are identical. Freeze relative times ("2h ago") if the app supports it.
- **Stable selectors.** Use CSS selectors, URLs, or `find` by role/text — not
  snapshot `@ref`s, which change between runs.
- **Wait for the real thing.** `wait --load networkidle`, then wait for a known
  element of the state before the screenshot.
- **Same app build mode** each round (dev vs. prod builds can differ visually).
- After writing the script, run it twice and compare the two outputs (pixel diff or
  just view them). If they differ, fix the nondeterminism before round 1.
- Reference apps (benchmark mode): capture them the same way if they're public URLs;
  otherwise ask the user for screenshots in the same states and note any states
  that can't be matched.
