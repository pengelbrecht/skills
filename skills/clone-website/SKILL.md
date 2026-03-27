---
name: clone-website
description: |
  Reverse-engineer and clone any website into production-ready Astro 6 code. Extracts assets,
  exact CSS, content, and behaviors section-by-section, writes component specs, then dispatches
  parallel builder agents in worktrees. Use when user asks to: clone website, vibe clone,
  replicate landing page, copy website design, rebuild this site, recreate this page, clone
  specific sections (hero, pricing, footer, etc).
  Triggers: "clone this website", "vibe clone [url]", "replicate this landing page",
  "rebuild this site in Astro", "clone the hero section from [url]", "copy this design".
---

# Clone Website Skill

Reverse-engineer any website into production-ready Astro 6 code using agent-browser for headless scraping. Extraction and construction happen in parallel — as each section is inspected, a detailed spec is written and handed to a builder agent working in an isolated git worktree.

## Guiding Principles

1. **Completeness Beats Speed** — Every builder must have everything: screenshot, exact CSS values, downloaded assets with local paths, real text, component structure. Extract the extra property rather than ship an incomplete brief.
2. **Small Tasks, Perfect Results** — Single-component sections get one builder agent; multi-variant sections get one agent per variant. If a builder prompt exceeds ~150 lines of spec, split the section.
3. **Real Content, Real Assets** — Extract actual text via `element.textContent`, download every `<img>` and `<video>`, convert inline `<svg>` to components. Check for layered compositions (background + foreground + overlay).
4. **Foundation First** — Global CSS tokens, fonts, TypeScript types, and global assets must exist before any section building. Sequential, non-negotiable. Everything after is parallel.
5. **Extract How It Looks AND How It Behaves** — Document appearance (exact computed CSS via `getComputedStyle()`) AND behavior (what changes, trigger, transition). Not "looks like `text-lg`" but the actual computed value.
6. **Identify Interaction Model Before Building** — Answer definitively: Is this click-driven, scroll-driven, hover-driven, time-driven, or mixed? **Scroll first before clicking.** If things change as you scroll, extract the mechanism. If not, then click/hover test. This is the #1 most expensive mistake — wrong interaction model requires a complete rewrite.
7. **Extract Every State, Not Just Default** — Click each tab/button, extract content per state. For scroll-dependent elements: capture computed styles at position 0, scroll past trigger, capture again, diff them.
8. **Spec Files Are Source of Truth** — Every component gets a spec file BEFORE dispatch. The spec is the contract between extraction and builder. Non-optional.
9. **Build Must Always Compile** — Every builder verifies the build passes before finishing. Broken build is never acceptable, even temporarily.

## Prerequisites

Before starting, verify tools are installed:

```bash
agent-browser --version   # Required: headless scraping
node --version             # Required: Astro project
npm --version              # Required: package management
curl --version             # Optional: downloading images
```

If `agent-browser` is not installed:
```bash
npm install -g agent-browser && agent-browser install
```

If any required tool is missing, **stop and inform the user** with install instructions before proceeding.

## Workflow

Execute these 5 phases in order. **Never skip Phase 2 or Phase 5.**

### Phase 1: Reconnaissance

**IMPORTANT: Run all agent-browser commands sequentially, one at a time.** They share a single browser session. Do NOT run them as parallel tool calls — if one fails, parallel siblings get cancelled.

**IMPORTANT: Shell escaping with `agent-browser eval`.** Complex JS with nested quotes, arrow functions, or template literals often breaks due to shell escaping. Prefer these approaches:
- Use `agent-browser get text`, `get html`, `get attr` built-in commands instead of eval when possible
- For eval, keep JS simple — avoid nested quotes and callbacks
- For complex JS, pipe via stdin: `echo 'your code here' | agent-browser eval --stdin`
- Or use base64: `agent-browser eval -b "$(echo 'your code' | base64)"`

#### Step 1: Open & Screenshot

```bash
agent-browser open [TARGET_URL]
agent-browser wait --load networkidle

# Full-page screenshots at desktop and mobile
agent-browser screenshot --full ./docs/design-references/desktop-full.png
agent-browser eval "window.innerWidth = 390; window.innerHeight = 844; void(0)"
agent-browser screenshot --full ./docs/design-references/mobile-full.png
agent-browser eval "window.innerWidth = 1440; window.innerHeight = 900; void(0)"
```

#### Step 2: Extract Page Content & Meta

```bash
agent-browser eval "document.documentElement.outerHTML"
agent-browser get text "body"
agent-browser eval "document.title"
agent-browser snapshot

echo 'JSON.stringify(Array.from(document.querySelectorAll("meta")).map(function(m) { return { name: m.name || m.getAttribute("property"), content: m.content } }))' | agent-browser eval --stdin
```

#### Step 3: Comprehensive Asset Discovery

Run this single script to find all images, videos, background images, SVGs, fonts, and favicons:

```bash
cat <<'JSEOF' | agent-browser eval --stdin
JSON.stringify({
  images: Array.from(document.querySelectorAll("img")).map(function(img) {
    return {
      src: img.src || img.currentSrc, alt: img.alt,
      naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight,
      parentClasses: img.parentElement ? img.parentElement.className : "",
      position: getComputedStyle(img).position,
      zIndex: getComputedStyle(img).zIndex
    };
  }),
  videos: Array.from(document.querySelectorAll("video, video source, iframe[src*=vimeo], iframe[src*=youtube], iframe[src*=wistia]")).map(function(el) {
    return {
      tag: el.tagName, src: el.src || el.getAttribute("src"),
      poster: el.poster || null, autoplay: el.autoplay || null,
      loop: el.loop || null, muted: el.muted || null
    };
  }),
  backgroundImages: Array.from(document.querySelectorAll("*")).filter(function(el) {
    var bg = getComputedStyle(el).backgroundImage;
    return bg && bg !== "none";
  }).map(function(el) {
    return {
      url: getComputedStyle(el).backgroundImage,
      element: el.tagName + "." + (el.className || "").toString().split(" ")[0]
    };
  }),
  svgCount: document.querySelectorAll("svg").length,
  favicons: Array.from(document.querySelectorAll("link[rel*=icon]")).map(function(l) {
    return { href: l.href, sizes: l.sizes ? l.sizes.toString() : null };
  })
});
JSEOF
```

#### Step 4: Font Detection & Extraction

Detect all fonts — Google Fonts, self-hosted/commercial, and system fonts:

```bash
cat <<'JSEOF' | agent-browser eval --stdin
var fontLinks = Array.from(document.querySelectorAll("link[href*='fonts.googleapis.com'], link[href*='fonts.gstatic.com'], link[href*='use.typekit.net']")).map(function(l) {
  return { href: l.href, type: "hosted-service" };
});
var fontFaces = Array.from(document.styleSheets).flatMap(function(s) {
  try { return Array.from(s.cssRules); } catch(e) { return []; }
}).filter(function(r) { return r instanceof CSSFontFaceRule; }).map(function(r) {
  var src = r.style.getPropertyValue("src");
  return {
    family: r.style.getPropertyValue("font-family").replace(/['"]/g, ""),
    weight: r.style.getPropertyValue("font-weight"),
    style: r.style.getPropertyValue("font-style"),
    src: src,
    isGoogle: src.indexOf("fonts.gstatic.com") > -1,
    urls: (src.match(/url\(["']?([^"')]+)["']?\)/g) || []).map(function(u) {
      return u.replace(/url\(["']?|["']?\)/g, "");
    })
  };
});
var usedFamilies = Array.from(new Set(
  Array.from(document.querySelectorAll("*")).slice(0, 300).map(function(el) {
    return getComputedStyle(el).fontFamily;
  })
));
JSON.stringify({ fontLinks: fontLinks, fontFaces: fontFaces, usedFamilies: usedFamilies });
JSEOF
```

**Font handling strategy:**
- **Google Fonts**: Use the detected Google Fonts URL or configure via `@fontsource`
- **Commercial/self-hosted fonts**: Ask user "I detected commercial font [name]. Do you have a license? (y/n)". If yes: download the `.woff2` files from the extracted URLs and configure via `@font-face` in `global.css`. If no: suggest the closest Google Font alternative.
- **System fonts**: Use as-is in the font stack

#### Step 5: Deep CSS Extraction (getComputedStyle Walker)

Extract exact computed styles for any element and its children (up to 4 levels deep). Use this per-section during Phase 3 spec writing:

```bash
# Replace SELECTOR with actual CSS selector (e.g., "section.hero", "#pricing", "nav")
cat <<'JSEOF' | agent-browser eval --stdin
(function(selector) {
  var el = document.querySelector(selector);
  if (!el) return JSON.stringify({ error: "Element not found: " + selector });
  var props = [
    "fontSize","fontWeight","fontFamily","lineHeight","letterSpacing","color",
    "textTransform","textDecoration","backgroundColor","background",
    "padding","paddingTop","paddingRight","paddingBottom","paddingLeft",
    "margin","marginTop","marginRight","marginBottom","marginLeft",
    "width","height","maxWidth","minWidth","maxHeight","minHeight",
    "display","flexDirection","justifyContent","alignItems","gap",
    "gridTemplateColumns","gridTemplateRows",
    "borderRadius","border","borderTop","borderBottom","borderLeft","borderRight",
    "boxShadow","overflow","overflowX","overflowY",
    "position","top","right","bottom","left","zIndex",
    "opacity","transform","transition","cursor",
    "objectFit","objectPosition","mixBlendMode","filter","backdropFilter",
    "whiteSpace","textOverflow","WebkitLineClamp"
  ];
  function extractStyles(element) {
    var cs = getComputedStyle(element);
    var styles = {};
    props.forEach(function(p) {
      var v = cs[p];
      if (v && v !== "none" && v !== "normal" && v !== "auto" && v !== "0px" && v !== "rgba(0, 0, 0, 0)")
        styles[p] = v;
    });
    return styles;
  }
  function walk(element, depth) {
    if (depth > 4) return null;
    var children = Array.from(element.children);
    return {
      tag: element.tagName.toLowerCase(),
      classes: (element.className || "").toString().split(" ").slice(0, 5).join(" "),
      text: element.childNodes.length === 1 && element.childNodes[0].nodeType === 3
        ? element.textContent.trim().slice(0, 200) : null,
      styles: extractStyles(element),
      images: element.tagName === "IMG"
        ? { src: element.src, alt: element.alt, naturalWidth: element.naturalWidth, naturalHeight: element.naturalHeight }
        : null,
      childCount: children.length,
      children: children.slice(0, 20).map(function(c) { return walk(c, depth + 1); }).filter(Boolean)
    };
  }
  return JSON.stringify(walk(el, 0), null, 2);
})("SELECTOR");
JSEOF
```

#### Step 6: Design Token Extraction

```bash
# Extract CSS custom properties
cat <<'JSEOF' | agent-browser eval --stdin
var props = Array.from(document.styleSheets)
  .flatMap(function(s) { try { return Array.from(s.cssRules); } catch(e) { return []; } })
  .filter(function(r) { return r.selectorText === ":root"; })
  .flatMap(function(r) { return r.cssText.match(/--[^:]+:[^;]+/g) || []; });
JSON.stringify(props);
JSEOF

# Extract key colors from semantic elements
cat <<'JSEOF' | agent-browser eval --stdin
var sels = ["h1","h2","h3","p","a","button","nav","footer","header","section"];
var result = sels.map(function(sel) {
  var el = document.querySelector(sel);
  if (!el) return null;
  var s = getComputedStyle(el);
  return { el: sel, color: s.color, bg: s.backgroundColor, font: s.fontFamily, size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight };
}).filter(function(x) { return x !== null; });
JSON.stringify(result);
JSEOF
```

#### Step 7: Interaction Sweep

**Mandatory.** Observe behaviors before building — wrong interaction model requires a complete rewrite.

```bash
# 1. Slow scroll top-to-bottom — observe what changes
agent-browser eval "window.scrollTo(0, 0)"
agent-browser screenshot ./docs/design-references/scroll-top.png
agent-browser eval "window.scrollTo(0, 300)"
agent-browser screenshot ./docs/design-references/scroll-300.png
agent-browser eval "window.scrollTo(0, document.body.scrollHeight)"
agent-browser screenshot ./docs/design-references/scroll-bottom.png
agent-browser eval "window.scrollTo(0, 0)"
```

While scrolling, note:
- Does the header shrink, gain a shadow, or change background?
- Do elements fade/slide in as they enter the viewport?
- Is there scroll-snap behavior?
- Are there parallax layers?
- Do tabs/accordions auto-switch based on scroll position?

```bash
# 2. Detect smooth scroll libraries (Lenis, Locomotive Scroll)
cat <<'JSEOF' | agent-browser eval --stdin
JSON.stringify({
  hasLenis: !!document.querySelector(".lenis") || !!document.querySelector("[data-lenis]") || typeof window.lenis !== "undefined",
  hasLocomotiveScroll: !!document.querySelector("[data-scroll-container]") || !!document.querySelector(".locomotive-scroll"),
  hasScrollSnap: Array.from(document.querySelectorAll("*")).some(function(el) {
    var ss = getComputedStyle(el).scrollSnapType;
    return ss && ss !== "none";
  }),
  hasStickyElements: Array.from(document.querySelectorAll("*")).filter(function(el) {
    return getComputedStyle(el).position === "sticky";
  }).map(function(el) { return el.tagName + "." + (el.className || "").toString().split(" ")[0]; })
});
JSEOF
```

```bash
# 3. Click interactive elements — observe state changes
# For each tab, button, accordion trigger: click and screenshot
agent-browser click "[data-tab]:first-child"
agent-browser screenshot ./docs/design-references/tab-state-1.png
agent-browser click "[data-tab]:nth-child(2)"
agent-browser screenshot ./docs/design-references/tab-state-2.png
```

```bash
# 4. Responsive check at key breakpoints
agent-browser eval "window.innerWidth = 768; void(0)"
agent-browser screenshot --full ./docs/design-references/tablet-full.png
agent-browser eval "window.innerWidth = 390; void(0)"
agent-browser screenshot --full ./docs/design-references/mobile-full.png
agent-browser eval "window.innerWidth = 1440; void(0)"
```

#### Step 8: Multi-State CSS Extraction

For any element that changes state (scroll-triggered, hover, click), capture before/after:

```bash
# Example: Header before/after scroll
# State A: at top
agent-browser eval "window.scrollTo(0, 0)"
cat <<'JSEOF' | agent-browser eval --stdin
var el = document.querySelector("header");
var cs = getComputedStyle(el);
JSON.stringify({
  state: "A-top", height: cs.height, padding: cs.padding,
  backgroundColor: cs.backgroundColor, boxShadow: cs.boxShadow,
  backdropFilter: cs.backdropFilter, transition: cs.transition
});
JSEOF

# State B: scrolled
agent-browser eval "window.scrollTo(0, 200)"
cat <<'JSEOF' | agent-browser eval --stdin
var el = document.querySelector("header");
var cs = getComputedStyle(el);
JSON.stringify({
  state: "B-scrolled", height: cs.height, padding: cs.padding,
  backgroundColor: cs.backgroundColor, boxShadow: cs.boxShadow,
  backdropFilter: cs.backdropFilter, transition: cs.transition
});
JSEOF
```

Then diff: "Property X: VALUE_A → VALUE_B, triggered by scroll > 200px, transition: all 0.3s ease"

#### Step 9: Page Topology

Document the page structure to `docs/research/PAGE_TOPOLOGY.md`:
- Section names and visual order
- Fixed vs. flow content
- Layout structure (single column, sidebar, etc.)
- Dependencies between sections
- Interaction model per section (static / click-driven / scroll-driven / hover-driven / time-driven)

#### Partial Cloning

If a specific section is requested, scope extraction:

```bash
agent-browser get html "#hero"
agent-browser get html "section.pricing"
agent-browser snapshot -s "#hero"
```

#### Step 10: Close Browser

```bash
agent-browser close
```

### Phase 2: Analysis (MANDATORY)

**STOP. Present analysis to user before ANY code generation.**

Read [references/analysis-template.md](references/analysis-template.md) and fill out the template with:
- Detected sections and component breakdown
- Extracted design tokens (colors, typography, spacing)
- Font inventory: Google Fonts vs commercial (with license question) vs system
- Image inventory with download/fallback status
- Behaviors detected (scroll-triggered, hover states, animations)
- Interaction model per section
- Proposed file structure

Ask user: "Ready to proceed? (y/n or request modifications)"

**Do not generate code until user confirms.**

### Phase 3: Foundation Build (Sequential — Not Delegated)

These must be done sequentially before any parallel builder work:

1. `src/styles/global.css` — Design tokens as CSS variables + Tailwind import
2. Font setup — Google Fonts via `@fontsource` or commercial fonts via `@font-face` in `global.css`
3. `src/layouts/Layout.astro` — Base layout with SEO metadata and font references
4. Download all assets to `public/images/`, `public/videos/`, `public/fonts/`
5. Extract inline SVGs as components if reused across sections
6. `astro.config.mjs` + `package.json` — Astro config with integrations
7. Verify: `npm run build` passes before proceeding

Reference [references/tech-stack.md](references/tech-stack.md) for Astro 6 conventions.

### Phase 4: Component Specification & Parallel Build

For each section of the page, run this loop:

#### Step 1: Extract (Per-Section)

- Screenshot the section in isolation
- Run the deep CSS extraction script (Step 5 from Phase 1) on the section's container
- For multi-state elements: capture styles at State A, trigger change, capture State B, diff
- Extract all text content verbatim using `agent-browser get text`
- For tabbed content: click each tab, extract content per state
- Identify all assets (including layered/overlapping images)

#### Step 2: Write Component Spec File

Write a spec to `docs/research/components/<component-name>.spec.md` using the template in [references/component-spec-template.md](references/component-spec-template.md).

**Pre-dispatch checklist:**
- [ ] Spec file has ALL sections filled out
- [ ] Every CSS value is from `getComputedStyle()`, not estimated
- [ ] Interaction model identified and documented
- [ ] For stateful components: every state's content and styles captured
- [ ] For scroll-driven: trigger threshold, before/after styles, transition recorded
- [ ] For hover: before/after values and transition timing recorded
- [ ] All images identified (including overlays, layered compositions)
- [ ] Responsive behavior documented for desktop, tablet, and mobile
- [ ] Text content verbatim, not paraphrased

#### Step 3: Dispatch Builder Agent (Worktree)

Use the Agent tool with `isolation: "worktree"` to dispatch a builder for each component:

- **Simple section** (1–2 sub-components): one builder agent
- **Complex section** (3+ sub-components): one agent per sub-component + one for the wrapper

Each builder agent receives:
- The full component spec inline (from the spec file)
- Screenshot path for visual reference
- Shared imports: design tokens from `global.css`, any shared SVG components
- Target file path (e.g., `src/components/landing/Hero.astro`)
- Instruction to verify build: `npm run build` before finishing

**Do NOT wait for builders to complete before extracting the next section.** Dispatch and move on.

Reference [references/component-patterns.md](references/component-patterns.md) for Astro component structure.

#### Step 4: Merge & Verify

As builder agents complete:
- Their worktree branches will be available for merging
- After each merge, verify `npm run build` passes
- Fix type errors or conflicts immediately

#### Step 5: Page Assembly

After all builders complete:
1. Import all section components into `src/pages/index.astro`
2. Implement page-level layout from topology doc (scroll containers, sticky positioning, z-index)
3. Implement page-level behaviors: scroll-snap, scroll-driven animations, smooth scroll (Lenis if detected)
4. Verify: `npm run build` passes clean

### Phase 5: Visual QA

**Do not skip this phase.**

1. Take side-by-side screenshots: original vs. clone at 1440px and 390px
2. Compare section by section, top to bottom
3. For each discrepancy:
   - Check if the spec was accurate
   - Re-extract from the original if needed
   - Update the component
4. Test all interactions: scroll behaviors, click states, hover effects, animations
5. Verify responsive behavior at 1440px, 768px, and 390px

Report to user:
- Total sections built
- Total components created
- Total spec files written
- Total assets downloaded
- Build result (`npm run build`)
- Any remaining visual discrepancies or known gaps

## Tech Stack (Fixed)

| Layer | Technology |
|-------|------------|
| Framework | Astro 6 (static + islands) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 |
| Interactive Islands | React (via `@astrojs/react`, only when needed) |
| Icons | Lucide (astro-icon or inline SVG) |
| Fonts | Google Fonts via `@fontsource`, or commercial fonts via local `@font-face` (with user license confirmation), or system fonts |

## When to Use Islands

Most cloned landing pages are **static** and need zero client-side JS. Use Astro's default: render everything as static HTML.

Only create interactive React islands (`client:*` directives) when the cloned site has:
- Mobile hamburger menu (toggle open/close) → `client:idle`
- Tabs, accordions, carousels → `client:visible`
- Form validation with live feedback → `client:load`
- Animated counters or scroll-triggered animations → `client:visible`

Static alternatives preferred when possible:
- CSS-only hamburger via `<details>`/`<summary>` or `:target`
- CSS-only accordions via `<details>` elements
- CSS scroll-snap carousels

## Image Handling

1. Extract all image URLs using the asset discovery script (Phase 1, Step 3)
2. Check for layered/composite images — a section may have background + foreground + overlay
3. Attempt download via `curl` or `agent-browser`
4. On failure, use Unsplash fallback:
   - Hero: `https://images.unsplash.com/photo-[id]?w=1920&h=1080`
   - Avatars: `https://images.unsplash.com/photo-[id]?w=100&h=100`
   - Features: Prefer Lucide icons or inline SVGs over images
5. Save to `public/images/` with descriptive kebab-case names
6. For optimized images, store in `src/images/` and use `<Image />` from `astro:assets`

## Partial Cloning

Parse user request for section filters:

| Request | Action |
|---------|--------|
| "clone the hero from X" | Generate only Hero.astro |
| "clone pricing and footer" | Generate Pricing.astro + Footer.astro |
| "clone X" (no filter) | Full page clone |

## Code Standards

- Mobile-first responsive design
- Use Tailwind arbitrary values for pixel-perfection: `w-[347px]`
- Extract repeated colors to CSS variables in `global.css`
- Use `class:list` for conditional classes in `.astro` files
- Add brief comments only for non-obvious patterns
- Prefer `gap-*` over margins for flex/grid spacing
- Prefer static `.astro` components; only use `.tsx` islands when interactivity is required
- Use `<Image />` from `astro:assets` for optimized images in `src/`
- Use standard `<img>` for images in `public/`

## What NOT to Do

- **Don't build click-based when original is scroll-driven (or vice versa).** Determine interaction model FIRST by scrolling before clicking. This is the #1 most expensive mistake — requires a complete rewrite, not a CSS fix.
- Don't extract only the default state — click each tab, scroll past triggers, capture every state's content and CSS
- Don't miss overlay/layered images — check every container's DOM for multiple `<img>` elements and positioned overlays
- Don't build mockup components for sections that are actually videos/animations — check for `<video>`, Lottie, canvas first
- Don't approximate CSS values — "looks like `text-lg`" is wrong if computed is 18px with different line-height; use exact `getComputedStyle()` values
- Don't dispatch builders without spec files — the spec forces exhaustive extraction and creates an auditable artifact
- Don't scope builder agents too broadly — if the prompt exceeds ~150 lines of spec, split the section
- Don't bundle unrelated sections (CTA + footer) — treat as separate components
- Don't skip responsive extraction — test at 1440, 768, 390 during reconnaissance
- Don't forget smooth scroll libraries (Lenis, Locomotive Scroll) — default scroll feels noticeably different
- Don't reference external docs in builder prompts — inline the spec's CSS values directly
