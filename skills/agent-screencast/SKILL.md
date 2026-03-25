---
name: agent-screencast
description: >
  Record narrated, captioned screen recording videos of web applications.
  Use this skill whenever the user wants to create a video demo, screencast,
  walkthrough, or recording of a web app — whether local (localhost) or public.
  Triggers on phrases like "record a demo", "make a video of this feature",
  "create a walkthrough", "screencast with voiceover", "demo video for a PR",
  "narrated recording", "generate a video demo", "show me how this works on video",
  or any request involving recording a web app with spoken narration and subtitles.
  Also trigger when users want to attach video evidence to pull requests, generate
  onboarding walkthroughs, or create feature demos for stakeholders. Even if the
  user just says "make a video" or "record this" in the context of a web app,
  use this skill.
---

# Agent Screencast

Record narrated, captioned screen recordings of web applications. The pipeline
uses agent-browser for browser automation, edge-tts for free voice synthesis,
and ffmpeg for assembly. No API keys required.

## Prerequisites

Before starting, verify the tools are available:

```bash
which uv            || echo "MISSING: curl -LsSf https://astral.sh/uv/install.sh | sh"
which agent-browser || echo "MISSING: npm i -g agent-browser && agent-browser install"
which ffmpeg        || echo "MISSING: brew install ffmpeg"
```

No installation step is needed — `uv run` handles Python dependencies automatically
via inline script metadata.

## How It Works

The pipeline has three passes:

1. **Research pass** — Visit pages, snapshot them, understand what's on screen
2. **Dry-run validation** — Replay the script without recording, taking screenshots
   per segment to verify actions work (login succeeds, pages load, clicks land)
3. **Script + execute** — Generate audio, record browser synced to audio timing,
   assemble final MP4

The insight: generate all narration audio first, *then* record the browser with
precise wait durations matching each segment's audio length. This avoids dead air
and ensures narration matches what's actually visible.

## Workflow

### Step 1: Research the target pages

Use agent-browser to visit and snapshot each page/state you want to demo:

```bash
agent-browser open http://localhost:4321
agent-browser wait --load networkidle
agent-browser snapshot -i
```

The snapshot gives you the accessibility tree with interactive element refs
(`@e1`, `@e2`, etc.) that you'll use in the segment script actions.

Take multiple snapshots if the demo spans several pages or states. Note which
refs correspond to which elements — refs are invalidated after navigation, so
each page gets its own set.

For pages that need clicking or interaction to reveal UI, do that during research:

```bash
agent-browser click @e5
agent-browser wait --load networkidle
agent-browser snapshot -i   # fresh refs for the new state
```

### Step 2: Write the segment script

Create a JSON file describing each segment of the video. Each segment has
narration text and browser actions that will play during that narration.

```json
{
  "title": "Feature demo",
  "base_url": "http://localhost:4321",
  "voice": "en-US-GuyNeural",
  "segments": [
    {
      "id": "intro",
      "narration": "Here's the new dashboard. Let's explore the key metrics.",
      "actions": [
        { "cmd": "open", "arg": "http://localhost:4321/dashboard" },
        { "cmd": "wait", "arg": "--load networkidle" },
        { "cmd": "wait", "arg": "500" }
      ],
      "caption_overlay": "Dashboard Overview"
    },
    {
      "id": "interact",
      "narration": "Clicking the revenue card opens a detailed breakdown by region.",
      "actions": [
        { "cmd": "click", "arg": "@e3" },
        { "cmd": "wait", "arg": "--load networkidle" },
        { "cmd": "scroll", "arg": "down 300" },
        { "cmd": "wait", "arg": "500" }
      ],
      "caption_overlay": null
    }
  ]
}
```

#### Segment fields

| Field | Description |
|-------|-------------|
| `id` | Unique identifier for the segment (used for filenames) |
| `narration` | Spoken text. Write in present tense ("Watch as..." not "You will see..."). Keep each segment 5-15 seconds of speech. |
| `actions` | Array of `{"cmd": "...", "arg": "..."}` — agent-browser commands to execute during this segment |
| `caption_overlay` | Optional floating text label shown on screen (e.g. "New Feature!"). Set `null` to skip. |

#### Available actions

| cmd | arg example | Notes |
|-----|-------------|-------|
| `open` | `http://localhost:4321/page` | Navigate to URL |
| `wait` | `--load networkidle` | Wait for network idle |
| `wait` | `1000` | Wait N milliseconds |
| `click` | `@e5` | Click element ref from snapshot |
| `scroll` | `down 300` | Scroll direction + pixels |
| `find` | `text "Sign In" click` | Semantic locator (find + act) |
| `eval` | `document.querySelector('.btn').click()` | Run JS in browser (piped via --stdin, so quotes are safe) |
| `fill` | `@e2 "search query"` | Type into an input |
| `select` | `@e1 "option"` | Select dropdown value |

#### Writing robust actions

Element refs (`@e1`, `@e2`) are fragile — they change when the DOM changes
(cookie banners, modals, dynamic content). Prefer these approaches in order:

1. **`eval` with DOM queries** (most robust) — Use CSS selectors or attribute
   lookups that survive DOM changes:
   ```json
   { "cmd": "eval", "arg": "document.querySelector('input[name=\"email\"]').focus()" }
   ```

2. **`find` with semantic locators** — More stable than refs, but syntax must
   match exactly (`find text "Sign In" click`, not `find text "Sign in" click`):
   ```json
   { "cmd": "find", "arg": "text \"Sign In\" click" }
   ```

3. **`@e` refs** — Only use for elements that are stable (no preceding dynamic
   content like cookie banners). Always re-snapshot after navigation.

**For form filling**, use `eval` with the native value setter pattern to work
with reactive frameworks (Vue, React):
```json
{
  "cmd": "eval",
  "arg": "(() => { const el = document.querySelector('input[name=\"email\"]'); const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; s.call(el, 'user@test.com'); el.dispatchEvent(new Event('input', { bubbles: true })); return 'ok'; })()"
}
```

**For button clicks**, match by text content to avoid ref fragility:
```json
{
  "cmd": "eval",
  "arg": "document.querySelectorAll('button').forEach(b => { if (b.textContent.trim() === 'Sign In') b.click() }); 'ok'"
}
```

#### Writing good narration

- Reference what the viewer will actually see: "Watch the quantities update" not
  "The system recalculates values"
- Use present tense throughout
- Keep segments between 5-15 seconds of speech (~15-40 words each)
- Total video: 30-90 seconds for PR demos, up to 3 minutes for walkthroughs
- Don't narrate obvious UI actions ("I'm clicking the button") — describe *why*
  or *what happens*

#### Voice options

Run `uv run edge-tts --list-voices` for the full list. Good defaults:

| Voice | Style |
|-------|-------|
| `en-US-GuyNeural` | Clear, neutral male (default) |
| `en-US-JennyNeural` | Friendly, warm female |
| `en-US-AriaNeural` | Professional female |
| `en-GB-SoniaNeural` | British female |
| `da-DK-ChristelNeural` | Danish female |
| `da-DK-JeppeNeural` | Danish male |

### Step 3: Validate with dry-run

**Always dry-run before recording.** This replays all actions without recording
or generating audio, taking a screenshot after each segment. It catches broken
selectors, failed logins, and navigation issues before you waste time on a
full recording.

```bash
uv run <skill-dir>/agent-screencast.py <path-to-script.json> --dry-run --session-dir ./session
```

This outputs:
- Per-segment pass/fail status
- Screenshots in `./session/dry-run/` (one per segment)
- Current URL after each segment (to verify navigation worked)

**Review the screenshots** (use the Read tool to view PNGs) before proceeding.
If any segment fails, fix the script and re-run `--dry-run` until all pass.

### Step 4: Run the pipeline

Save the script JSON, then run the self-contained script (uv resolves deps automatically):

```bash
uv run <skill-dir>/agent-screencast.py <path-to-script.json> -o output.mp4 --session-dir ./session
```

Where `<skill-dir>` is the path to this skill's directory (the folder containing this SKILL.md).

This executes all three phases automatically:
1. **Narration** — generates MP3 + SRT subtitles per segment via edge-tts
2. **Recording** — opens headless browser, replays actions synced to audio durations
3. **Assembly** — merges video + audio + subtitles into final MP4 via ffmpeg

#### CLI options

| Flag | Description |
|------|-------------|
| `-o FILE` | Output MP4 path (default: `demo.mp4`) |
| `--session-dir DIR` | Working directory for intermediate files |
| `--voice VOICE` | Override TTS voice for all segments |
| `--headed` | Show browser window during recording |
| `--auto-connect` | Connect to user's running Chrome via CDP |
| `--cdp PORT` | Connect to Chrome on specific CDP port |
| `--dry-run` | Validate script actions without recording (screenshots per segment) |
| `--skip-narration` | Reuse existing audio (for re-recording only) |
| `--skip-recording` | Reuse existing video (for re-assembling only) |

#### Re-running parts of the pipeline

If the recording looks wrong but audio is fine:
```bash
uv run <skill-dir>/agent-screencast.py script.json -o output.mp4 --session-dir ./session --skip-narration
```

If you just need to re-assemble (e.g. after tweaking subtitles):
```bash
uv run <skill-dir>/agent-screencast.py script.json -o output.mp4 --session-dir ./session --skip-narration --skip-recording
```

### Step 5: Review and iterate

Play the output video. Common issues and fixes:

| Problem | Fix |
|---------|-----|
| Actions happen too fast | Add `{"cmd": "wait", "arg": "500"}` between actions |
| Wrong element clicked | Use `eval` with CSS selectors instead of `@e` refs |
| Login/auth fails silently | Use `eval` with native value setter for form fields (see robust actions above) |
| Cookie banner shifts refs | Dismiss banners via `eval` before other actions |
| Narration doesn't match screen | Run `--dry-run` first to verify, then record |
| Dead air / long pauses | Remove unnecessary `wait` actions, shorten narration |
| Page not loaded when actions start | Add `{"cmd": "wait", "arg": "--load networkidle"}` after `open` |

## Example: Full workflow

Here's what a typical session looks like end-to-end:

```bash
# 1. Research
agent-browser open http://localhost:3000
agent-browser wait --load networkidle
agent-browser snapshot -i
# See: @e1 [link] "Dashboard", @e2 [button] "New Project", ...

agent-browser click @e1
agent-browser wait --load networkidle
agent-browser snapshot -i
# See: @e1 [heading] "Dashboard", @e3 [card] "Revenue", ...

# 2. Write script based on what you saw (save as demo-script.json)
#    Prefer eval with CSS selectors over @e refs for robustness

# 3. Validate with dry-run (catches broken selectors, failed logins, etc.)
uv run <skill-dir>/agent-screencast.py demo-script.json --dry-run --session-dir ./session
# Review screenshots in ./session/dry-run/*.png

# 4. Record (only after dry-run passes)
uv run <skill-dir>/agent-screencast.py demo-script.json -o feature-demo.mp4 --session-dir ./session

# 5. Output: feature-demo.mp4 with narration + subtitles
```

## Subtitle note

If ffmpeg has libass support, subtitles are burned into the video. Otherwise
they're embedded as a soft subtitle track (toggle-able in video players).
To get burned-in subtitles: `brew install ffmpeg` with libass support.
