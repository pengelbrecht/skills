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
which agent-browser || echo "MISSING: npm i -g agent-browser && agent-browser install"
which ffmpeg        || echo "MISSING: brew install ffmpeg"
# edge-tts is bundled with the agent-screencast package
```

Install the agent-screencast Python package (one-time setup):

```bash
cd <repo-root>/skills/agent-screencast
uv sync
```

Where `<repo-root>` is the directory containing the skills repo. You can find the
installed location by checking the skill's source path.

## How It Works

The pipeline has two key passes — this separation is what makes it work well:

1. **Research pass** — Visit pages, snapshot them, understand what's on screen
2. **Script + execute** — Write a segment script, then the tool generates audio,
   records the browser synced to audio timing, and assembles the final MP4

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

### Step 3: Run the pipeline

Save the script JSON, then run from the agent-screencast directory:

```bash
cd <skill-install-path>/skills/agent-screencast
uv run agent-screencast <path-to-script.json> -o output.mp4 --session-dir ./session
```

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
| `--skip-narration` | Reuse existing audio (for re-recording only) |
| `--skip-recording` | Reuse existing video (for re-assembling only) |

#### Re-running parts of the pipeline

If the recording looks wrong but audio is fine:
```bash
uv run agent-screencast script.json -o output.mp4 --session-dir ./session --skip-narration
```

If you just need to re-assemble (e.g. after tweaking subtitles):
```bash
uv run agent-screencast script.json -o output.mp4 --session-dir ./session --skip-narration --skip-recording
```

### Step 4: Review and iterate

Play the output video. Common issues and fixes:

| Problem | Fix |
|---------|-----|
| Actions happen too fast | Add `{"cmd": "wait", "arg": "500"}` between actions |
| Wrong element clicked | Re-snapshot the page, check refs are current |
| Narration doesn't match screen | The research pass snapshots may be stale — redo them |
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

# 3. Run pipeline
cd <skill-install-path>/skills/agent-screencast
uv run agent-screencast /path/to/demo-script.json -o feature-demo.mp4 --session-dir ./session

# 4. Output: feature-demo.mp4 with narration + subtitles
```

## Subtitle note

If ffmpeg has libass support, subtitles are burned into the video. Otherwise
they're embedded as a soft subtitle track (toggle-able in video players).
To get burned-in subtitles: `brew install ffmpeg` with libass support.
