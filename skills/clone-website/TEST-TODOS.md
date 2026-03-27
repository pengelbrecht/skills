# Test TODOs — clone-website skill

Commands that could not be tested because `agent-browser` is not available in the development environment. These must be manually verified before the skill is considered production-ready.

## Phase 1: Reconnaissance

### Step 1: Open & Screenshot
- [ ] `agent-browser open [URL]` — verify page opens and waits for networkidle
- [ ] `agent-browser screenshot --full ./docs/design-references/desktop-full.png` — verify full-page screenshot captured
- [ ] Viewport resize via `window.innerWidth = 390` — verify mobile screenshot is actually at mobile width (may need `agent-browser` viewport API instead of JS resize)

### Step 3: Asset Discovery Script
- [ ] The combined asset discovery `eval --stdin` script — verify it returns valid JSON with images, videos, backgroundImages, svgCount, favicons
- [ ] Background image detection — verify `getComputedStyle(el).backgroundImage` works across shadow DOM elements

### Step 4: Font Detection & Extraction
- [ ] Font detection script — verify it correctly identifies Google Fonts vs self-hosted `@font-face` fonts
- [ ] `CSSFontFaceRule` detection — verify `r instanceof CSSFontFaceRule` works in the agent-browser Chromium context
- [ ] Font URL extraction from `src` property — verify the regex correctly extracts `.woff2`/`.woff` URLs
- [ ] Commercial font download — verify `curl` can download `.woff2` files from extracted URLs (some may be CORS-restricted)

### Step 5: Deep CSS Extraction (getComputedStyle Walker)
- [ ] The DOM walker `eval --stdin` script — verify it returns valid JSON with styles, hierarchy, and text content
- [ ] Depth limit (4 levels) — verify it doesn't hang on deeply nested DOMs
- [ ] Large pages — verify the script doesn't timeout on pages with 1000+ elements

### Step 7: Interaction Sweep
- [ ] `window.scrollTo()` via eval — verify screenshots capture the scrolled state (not just the initial render)
- [ ] Smooth scroll library detection — verify Lenis/Locomotive detection works (test on a site known to use Lenis)
- [ ] Scroll-snap detection — verify the `scrollSnapType` check works
- [ ] Sticky element detection — verify `position: sticky` detection works
- [ ] `agent-browser click` — verify click triggers state changes (tab switching, accordion open)

### Step 8: Multi-State CSS Extraction
- [ ] Before/after scroll state capture — verify `window.scrollTo` + immediate `getComputedStyle` captures the post-transition state (may need a delay for CSS transitions to apply)
- [ ] Header shrink detection — test on a site with known scroll-triggered header changes

## Phase 4: Parallel Build

- [ ] Agent tool with `isolation: "worktree"` — verify builder agents can create files in their worktree and that changes are mergeable
- [ ] Multiple parallel builder agents — verify they don't conflict when writing to different file paths
- [ ] `npm run build` inside worktree — verify Astro build works in a worktree context (paths, config resolution)

## Phase 5: Visual QA

- [ ] Side-by-side screenshot comparison — verify agent-browser can take screenshots of the clone (localhost) alongside the original
- [ ] Responsive QA at 768px — verify viewport resize produces correct tablet layout

## Font Handling

- [ ] Google Font download via `@fontsource` — verify the package name mapping is correct (e.g., `@fontsource/inter` for "Inter")
- [ ] Commercial font `@font-face` declaration — verify locally downloaded `.woff2` files load correctly in the Astro dev server
- [ ] Font fallback suggestion — when user declines commercial font license, verify the suggested Google Font alternative is reasonable
