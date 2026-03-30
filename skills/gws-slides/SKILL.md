---
name: gws-slides
description: >
  Create polished, professional Google Slides presentations using the gws CLI.
  Use this skill whenever the user wants to create, update, or improve a Google Slides
  presentation — whether from scratch, from an outline, or by fixing an ugly existing deck.
  Triggers on phrases like "make a presentation", "create slides", "build a deck",
  "fix my slides", "make these slides look better", "presentation about X",
  "slide deck for X", "pitch deck", "keynote-style slides", "investor deck",
  "update my Google Slides", or any request involving Google Slides authoring.
  Also triggers when users mention gws slides, batchUpdate, or Slides API in the
  context of creating visual content.
metadata:
  version: 0.4.0
  requires:
    bins:
      - gws
---

# GWS Slides

Create polished, professional Google Slides presentations using the `gws` CLI. This skill wraps the Google Slides API with strong design opinions so every deck looks intentional, not auto-generated.

> **PREREQUISITE:** The `gws` CLI must be on `$PATH` and authenticated.

## Prerequisites

```bash
which gws || echo "MISSING: install gws CLI"
gws auth login -s slides,drive   # OAuth login with Slides + Drive scope
gws slides --help                 # verify Slides API is accessible
```

If `gws auth setup` has never been run, run it once to create a Cloud project and enable APIs.

> **CLI quirk:** `gws` prints `Using keyring backend: keyring` to stdout before JSON output. When parsing responses programmatically, skip the first line (e.g., `tail -n +2`).

## Quick Reference

```bash
gws slides presentations create --json '{"title": "My Deck"}'
gws slides presentations get --params '{"presentationId": "ID"}'
gws slides presentations batchUpdate --params '{"presentationId": "ID"}' --json '{"requests": [...]}'
gws schema slides.<resource>.<method>   # inspect params/types before calling
```

---

## Theme System

Every presentation uses a theme — a YAML file that pins fonts, colors, and an optional logo/wordmark. Themes keep decks consistent across presentations and let users express their brand without re-specifying preferences each time.

### Finding a theme

Check these locations in order:
1. `.gws-slides-theme.yaml` in the current working directory (project-specific)
2. `~/.gws-slides-theme.yaml` (user default)

If a theme file exists, use it silently. If no theme is found, run the theme interview before building the deck.

### Theme file format

```yaml
name: "Company Name"

font:
  family: "Inter"            # One family for everything — hierarchy through size/weight, not competing typefaces
  fallback: "Arial"          # Web-safe fallback
  mono: "JetBrains Mono"    # Code blocks only (functional, not decorative)

logo:
  path: "./logo.png"         # Local file path — will be uploaded to Drive automatically
  placement: "bottom-right"  # bottom-right | bottom-left | bottom-center | title-only
  height: 24                 # Points (width scales proportionally)

colors:
  background: "#FFFFFF"       # Slide background
  surface: "#F5F5F7"          # Content cards, callout boxes — prevents flat white-on-white
  text_primary: "#1D1D1F"     # Headings, body text
  text_secondary: "#6E6E73"   # Subtitles, captions, metadata
  accent_primary: "#0066CC"   # Key data, links, primary shapes
  accent_secondary: "#34C759" # Positive indicators, success states
  accent_warm: "#FF3B30"      # Alerts, negative indicators
  accent_neutral: "#FF9500"   # Warnings, highlights
  divider: "#D2D2D7"          # Lines, shape outlines, borders
  dark_bg: "#1D1D1F"          # Section divider backgrounds
  dark_text: "#FFFFFF"        # Text on dark backgrounds
  dark_accent: "#64D2FF"      # Accent on dark backgrounds
```

### Theme interview

When no theme file exists, ask these questions before building. Keep it conversational — most fields have sensible defaults.

1. **"Do you have brand colors?"** If yes, get the primary color at minimum. Derive the full palette from one strong brand color:
   - Background stays white/near-white (the brand color is an accent, not a flood fill)
   - Text primary: very dark neutral with high contrast
   - Surface: 2-3% gray tint of background
   - Brand color → `accent_primary`
   - Darken brand color → `dark_bg`; lighten it → `dark_accent`
2. **"Any font preference?"** Default to Inter if none. One family is the standard — weight and size create hierarchy without visual noise from mixed typefaces.
3. **"Do you have a company logo or wordmark?"** Optional. Can be a local file path — the skill handles uploading to Drive. Ask about preferred placement (bottom-right is the default). SVGs must be converted to PNG first (the Slides API only accepts raster images).
4. **"Save as your default theme?"** Write to `~/.gws-slides-theme.yaml` for reuse, or `.gws-slides-theme.yaml` for project-only.

### Default theme

When the user declines theming or wants to jump straight in:

```yaml
name: "Default"
font:
  family: "Inter"
  fallback: "Arial"
  mono: "Roboto Mono"
colors:
  background: "#FFFFFF"
  surface: "#F8F9FA"
  text_primary: "#1A1A2E"
  text_secondary: "#5F6368"
  accent_primary: "#1A73E8"
  accent_secondary: "#34A853"
  accent_warm: "#EA4335"
  accent_neutral: "#FBBC04"
  divider: "#DADCE0"
  dark_bg: "#1A1A2E"
  dark_text: "#FFFFFF"
  dark_accent: "#8AB4F8"
```

---

## Design Principles

These principles shape every slide. They're grounded in how people process projected content — understanding the reasoning helps you make good calls in edge cases rather than blindly following rules.

### Typography

**One font family, multiple weights.** Use the theme's `font.family` for all text. Hierarchy comes from size and weight (regular 400, medium 500, bold 700). Mixing typefaces adds visual noise and makes decks look cobbled together rather than designed.

| Element | Size | Line height | Rationale |
|---------|------|-------------|-----------|
| Section divider title | 48–56 pt | 1.1 | Needs to read from the back of the room |
| Slide title | 36–44 pt | 1.15 | Primary anchor for the eye |
| Subtitle / tagline | 20–24 pt | 1.3 | Clearly subordinate to title |
| Body / L1 bullets | 16–18 pt | 1.15 | Readable at projection distance |
| L2 sub-bullets | 14–16 pt | 1.15 | Clearly subordinate to L1 |
| Captions / labels | 12–14 pt | 1.4 | Secondary info, closer viewing |
| Footnotes | 10–11 pt | 1.3 | Reference only |

**Keep titles to 6–7 words.** Short titles let the audience grasp the point instantly. If it's longer, it belongs as a subtitle or the idea needs splitting.

**Left-align body text.** Centered body text forces the eye to find a new starting position on every line, slowing reading. Center-align only single-line titles on divider slides.

**Limit to 2 font sizes per slide** (e.g., title + body). More sizes create competing visual levels that confuse the hierarchy.

**Formatting restraint:** Title case for titles, sentence case for everything else. No underlines except hyperlinks. No ALL CAPS beyond short labels (2–3 words like "KEY METRICS"). These choices project professionalism; decorative formatting undermines it.

### Color

**Three colors per slide maximum** (background + text + one accent). Every additional color competes for attention. When everything is highlighted, nothing is.

**Saturated colors stay small** — a key metric, a badge, faux bullet glyphs. Large saturated areas overwhelm the eye and reduce text legibility. Use the theme's `surface` color for content cards and callout backgrounds.

**Dark backgrounds for section dividers only.** They create visual rhythm, signaling "new topic." Using them for content slides makes the deck feel heavy and reduces contrast options.

**Contrast is legibility.** Minimum 4.5:1 for body text, 3:1 for titles. This isn't just accessibility compliance — it's about readability in rooms with ambient light hitting the projector screen.

### Spacing & Layout

**Slide dimensions:** 720 × 405 pt (10" × 5.625", 16:9 widescreen)

Projectors and screens crop edges unpredictably, so content needs safe zones:

| Zone | Inset | What goes here |
|------|-------|----------------|
| Safe zone | 36 pt (0.5") all edges | Absolute boundary — nothing outside |
| Comfortable zone | 54 pt sides, 72 pt top, 43 pt bottom | Body content lives here |

**At least 40% whitespace.** Projected slides are viewed at distance in low-attention environments. Density kills comprehension. If content exceeds 70% of the slide area, split into two slides. The audience absorbs two clean slides faster than one cramped one.

**Alignment creates the "designed" feeling.** Elements sharing left edges, baselines, or center axes is what separates professional from amateur. Use consistent spacing:

| Token | Size | Use for |
|-------|------|---------|
| XS | 7 pt (0.1") | Icon-to-text, label-to-value |
| S | 14 pt (0.2") | Between bullets, related elements |
| M | 25 pt (0.35") | Title-to-body gap |
| L | 36 pt (0.5") | Between major sections |
| XL | 54 pt (0.75") | Body margin from edges |

### Layouts

Every slide uses one of 10 standard layouts: Title Slide, Section Divider, Title + Body, Two-Column, Grid (2×2 / 3×1), Big Number, Image + Text, Full-Bleed Image, Quote, Closing/CTA.

See `references/layouts.md` for detailed descriptions and positioning guidance for each layout.

**Vary the rhythm** — avoid two adjacent slides with the same layout. Alternating layouts sustains audience engagement.

---

## Workflow

### Phase 1: Plan the Deck

Before touching the API:

1. **Load the theme** — find theme file or run the interview
2. **Clarify the goal** — what is this deck for? (pitch, internal update, teaching, proposal)
3. **Draft an outline** — each slide gets: number, layout name, title, key content
4. **One idea per slide** — if a slide has 2+ distinct points, split it
5. **Check the arc:** Title → Agenda → Content (with section dividers) → Summary → Closing
6. **Present the outline** to the user for approval before building

Slide count targets: 5-min talk → 8–12 slides, 10-min → 15–20, read-ahead → as many as needed.

### Phase 2: Create the Presentation

```bash
gws slides presentations create --json '{"title": "TITLE"}'
```

Save the returned `presentationId` — every subsequent call needs it.

### Phase 3: Build Slides

Build via `presentations.batchUpdate` in batches of 3–5 slides. Always use the `BLANK` predefined layout and build content manually — the built-in Google layouts have poor default styling that fights your theme.

Read `references/api-patterns.md` for all JSON patterns: creating slides, text boxes, shapes, images, backgrounds, bullets, charts, and content cards.

**Key rules during construction:**
- Every color and font value comes from the loaded theme — never hardcode hex values or font names
- Place the logo on title and closing slides (or per `logo.placement` in the theme)
- **Use faux bullets, not `createParagraphBullets`.** The Slides API cannot color native bullet glyphs independently from text (this is a known API limitation). Instead, insert Unicode glyph characters (`●`, `■`, `→`, etc.) as text, color them `accent_primary`, and use `indentStart`/`indentFirstLine` with a tab character for hanging indent. See `references/api-patterns.md` for the full pattern.
- Use accent bars only on non-bullet slides (quotes, plain body text) — they collide visually with bullet markers
- **For charts:** generate as a high-DPI PNG (matplotlib, plotly, etc.) using theme colors, then upload via the Drive image pipeline and insert with `createImage`
- Use predictable object IDs: `slide_001`, `slide_001_title`, `slide_001_body`, etc.
- Keep batchUpdate payloads to 3–5 slides — large payloads are harder to debug when something goes wrong

### Bullet Styles

Three built-in styles. The default is `disc`. Max 2 nesting levels.

| Style | L1 glyph | L2 glyph | Feel |
|-------|----------|----------|------|
| **disc** (default) | `●` | `○` | Clean, universal |
| **square** | `■` | `–` | Bold, editorial |
| **arrow** | `→` | `▸` | Modern, techy |

**Sizing:** Glyphs render at the same font size as their line's text (L1: 17pt, L2: 15pt). Unicode glyphs like `●`, `■`, `→` are naturally proportioned within the em box, so they appear smaller than letters and align vertically on the baseline without manual adjustment.

**Spacing rules for bullet groups:**
- L1 → L1 (between top-level groups): `spaceAbove: 14pt` — clear visual separation
- L1 → L2 or L2 → L2 (within a group): `spaceAbove: 4pt` — tight, reads as one unit
- `lineSpacing: 115` (within a multiline bullet)
- First bullet on the slide: `spaceAbove: 0`

**Indentation (hanging indent via tab):**
- L1: `indentFirstLine: 0pt`, `indentStart: 28pt`
- L2: `indentFirstLine: 28pt`, `indentStart: 48pt`

**L2 text styling:** 15pt, `text_secondary` color — clearly subordinate to L1.

### Phase 4: Quality Check

Run this after each batch and again after the full deck is complete. Do not skip it — catching issues early is far cheaper than fixing a finished deck.

1. **Retrieve** the presentation: `gws slides presentations get`
2. **Per-slide checks:**
   - Typography: ≤2 font sizes on simple slides (grid/multi-column/closing may use 3), correct scale for element type, theme font used
   - Color: ≤3 colors, sufficient contrast, only theme colors
   - Faux bullets: glyph characters (`●`, `■`, `→`, etc.) are `accent_primary` colored, text is `text_primary` (L1) or `text_secondary` (L2), no accent bars on bullet slides
   - Bullet spacing: 14pt `spaceAbove` between L1 groups, 4pt within groups, correct indentation (L1: 0/28pt, L2: 28/48pt)
   - Spacing: content in safe zone, body in comfortable zone, ≥40% whitespace
   - **Overlap detection:** for each pair of elements on a slide, verify they don't collide — compare each element's bounding box (`translateY + height` of one vs `translateY` of another). Charts, images, and captions are especially prone to overlap
   - Content: one idea, ≤6 bullets, ≤8 words per bullet, title ≤7 words
   - Layout: matches a standard layout, elements aligned, clear hierarchy
   - Theme: logo present where expected, no stray hardcoded values
3. **Fix violations** via corrective batchUpdate calls
4. **Visual verification:** use `gws slides presentations pages getThumbnail` to download slide thumbnails as PNG and inspect them visually. This catches issues that the JSON check misses (element overlap, text truncation, visual alignment). Spot-check at minimum the title slide, one bullet slide, any chart slide, and the closing slide.
5. **Deck-level pass:** consistent title positioning, section dividers before each topic, font/color consistency across slides, proper first/last slides, layout rhythm variety

Report results to the user with a summary of checks passed and any issues found.

---

## What to Avoid

- **Predefined Google layouts** — they fight your theme; build on BLANK
- **Native `createParagraphBullets`** — the Slides API cannot color native bullet glyphs independently from text. Always use faux bullets (Unicode glyph + tab + hanging indent)
- **Paragraphs on slides** — if it reads like a document, split it
- **Centering body text** — hard to scan; left-align body, center only divider titles
- **Shrinking text to fit** — split the slide instead; cramped text is never read
- **Accent bars on bullet slides** — the bar and faux bullet glyphs collide; use accent-colored glyphs instead
- **Gradients** — solid colors are cleaner (unless the brand specifically requires them)
- **Duplicate object IDs** — cause silent API failures; follow the naming convention
- **Skipping quality check** — every deck passes the checklist; use `getThumbnail` to visually verify

## Reference Files

Read these during slide construction as needed:
- `references/api-patterns.md` — JSON examples for all batchUpdate operations, image upload pipeline, coordinate system
- `references/layouts.md` — All 10 standard layouts with positioning details
