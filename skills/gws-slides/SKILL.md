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
  version: 0.1.0
  requires:
    bins:
      - gws
---

# GWS Slides

Create polished, professional Google Slides presentations using the `gws` CLI. This skill wraps the Google Slides API with strong design opinions — typography, color, spacing, and layout — so every deck looks intentional, not auto-generated.

> **PREREQUISITE:** The `gws` CLI must be on `$PATH` and authenticated.

## Prerequisites

```bash
which gws || echo "MISSING: install gws CLI — see https://github.com/googleworkspace/cli"
gws auth login -s slides   # OAuth login with Slides scope (first time: run gws auth setup)
gws slides --help           # verify Slides API is accessible
```

If `gws auth setup` has never been run, it creates a Cloud project and enables APIs — run it once before `gws auth login`.

## Quick Reference: gws CLI

```bash
gws slides <resource> <method> [flags]

# Key commands
gws slides presentations create --json '{"title": "My Deck"}'
gws slides presentations get --params '{"presentationId": "PRESENTATION_ID"}'
gws slides presentations batchUpdate --params '{"presentationId": "PRESENTATION_ID"}' --json '{"requests": [...]}'

# Discover available methods and params
gws slides --help
gws schema slides.presentations.batchUpdate
```

Use `gws schema slides.<resource>.<method>` before calling any method to inspect required params, types, and defaults.

## Design System

Every slide produced by this skill must follow these rules. They are non-negotiable defaults — only deviate when the user explicitly requests a different style.

### Typography

**Font stack (in order of preference):**

| Role | Font | Fallback | Weight |
|------|------|----------|--------|
| Headings | Google Sans | Arial | Bold (700) |
| Subheadings | Google Sans | Arial | Medium (500) |
| Body | Google Sans Text | Arial | Regular (400) |
| Monospace/code | Google Sans Mono | Courier New | Regular (400) |
| Accent/quotes | Google Sans Text | Arial | Italic (400i) |

If Google Sans is not available (it may not render for non-Google accounts), use **Inter** as the primary font and **Roboto Mono** for code.

**Font sizes (points):**

| Element | Size | Line spacing | Letter spacing |
|---------|------|--------------|----------------|
| Slide title | 36–44 pt | 1.15 | -0.02 em |
| Section divider title | 48–56 pt | 1.1 | -0.03 em |
| Subtitle / tagline | 20–24 pt | 1.3 | 0 |
| Body text | 16–18 pt | 1.5 | 0.01 em |
| Bullet points | 16–18 pt | 1.5 | 0.01 em |
| Captions / labels | 12–14 pt | 1.4 | 0.02 em |
| Footnotes / sources | 10–11 pt | 1.3 | 0.02 em |

**Rules:**
- Never use more than 2 font sizes per slide (title + body, or title + subtitle)
- Title case for slide titles, sentence case for everything else
- Maximum 6–7 words per slide title — if longer, it's a subtitle
- Never center body text — left-align always (titles may be centered on divider slides)
- No underlines except for hyperlinks
- No ALL CAPS except for short labels (2–3 words max, e.g., "KEY METRICS")
- Minimum contrast ratio of 4.5:1 for body text, 3:1 for large text (titles)

### Color Palettes

Provide a default palette and let users override. When the user provides brand colors, build the full palette around them.

**Default palette (neutral professional):**

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#FFFFFF` | Slide background |
| Surface | `#F8F9FA` | Content cards, callout boxes |
| Text primary | `#1A1A2E` | Headings, body text |
| Text secondary | `#5F6368` | Subtitles, captions, labels |
| Accent primary | `#1A73E8` | Key data, links, primary shapes |
| Accent secondary | `#34A853` | Positive indicators, success |
| Accent warm | `#EA4335` | Alerts, negative indicators |
| Accent neutral | `#FBBC04` | Warnings, highlights |
| Divider/border | `#DADCE0` | Lines, shape outlines |

**Dark variant (for section dividers or emphasis slides):**

| Role | Hex |
|------|-----|
| Background | `#1A1A2E` |
| Text primary | `#FFFFFF` |
| Text secondary | `#B0B3B8` |
| Accent primary | `#8AB4F8` |

**Rules:**
- Maximum 3 colors per slide (background + text + one accent)
- Never use saturated colors for large areas — reserve them for small accents
- Use the surface color (`#F8F9FA`) for content cards, not white-on-white
- Dark backgrounds only for divider slides or full-bleed image slides
- Ensure text is always readable: test against the background color
- For charts/graphs: use the accent palette in order, never repeat colors

### Spacing & Layout

**Slide dimensions:** 10" x 5.625" (widescreen 16:9, the default)

**Margins and safe zone:**

| Zone | Inset from edge |
|------|----------------|
| Safe zone (all content) | 0.5" from all edges |
| Comfortable zone (body text) | 0.75" from left/right, 1.0" from top, 0.6" from bottom |
| Title position | Top-left of comfortable zone |
| Body content start | 0.3" below title baseline |

**Spacing units (in inches):**

| Space | Size | Usage |
|-------|------|-------|
| XS | 0.1" | Between label and value, icon and text |
| S | 0.2" | Between bullet items, between related elements |
| M | 0.35" | Between title and body, between content blocks |
| L | 0.5" | Between major sections on a slide |
| XL | 0.75" | Margin from edges for body content |

**Rules:**
- Never place text or shapes within 0.5" of any slide edge
- Consistent spacing between same-type elements (e.g., all bullets use S spacing)
- Use invisible alignment — elements should share left edges, baselines, or center axes
- Maximum 60% of the slide area should contain content (40% whitespace minimum)
- If content fills more than 70% of the slide, split into two slides
- Prefer left-heavy or grid layouts — avoid centered-everything layouts (except dividers)
- Number columns: 2, 3, or 4 — never 5+ (too cramped at slide scale)

### Layouts

Use these standard layouts. Each slide must use exactly one layout.

#### 1. Title Slide
- Large title centered vertically and horizontally
- Subtitle below, smaller, in text-secondary color
- Optional: small logo bottom-right or bottom-center
- Background: white or branded dark

#### 2. Section Divider
- Large title (48–56 pt) centered or left-aligned
- Background: dark or accent color, full bleed
- Optional: section number in accent color
- No body text — this slide is a pause/transition

#### 3. Title + Body (the workhorse)
- Title top-left in comfortable zone
- Body text or bullets below, left-aligned
- Right 40% may contain a supporting visual (image, chart, icon)
- If no visual, body text can span full width but add generous right margin

#### 4. Two-Column
- Title spanning full width at top
- Two equal columns below (each ~4.1" wide with 0.3" gutter)
- Use for comparisons, before/after, pros/cons
- Each column can contain text, images, or a mix

#### 5. Grid (2x2 or 3x1)
- Title at top
- 2x2: four equal cards arranged in a grid
- 3x1: three cards in a row (for features, pillars, team members)
- Cards should have consistent internal structure (icon/number, title, description)

#### 6. Big Number / Statistic
- One large number or metric (60–80 pt, accent color, bold)
- Label above or below in text-secondary (14 pt)
- Brief context sentence in body text
- Used for KPIs, milestones, impact statements

#### 7. Image + Text (split)
- Slide split roughly 50/50 or 60/40
- Image on one side (full height, edge-to-edge on that side)
- Text on the other side with comfortable margins
- Image should bleed to the slide edge (no margin on image side)

#### 8. Full-Bleed Image
- Image covers entire slide
- Text overlay with semi-transparent dark scrim if needed
- Use sparingly — maximum 1–2 per deck

#### 9. Quote
- Large quote text (24–28 pt, italic or accent font)
- Attribution below in smaller text-secondary
- Left-aligned with a vertical accent bar or large quotation mark
- Generous whitespace

#### 10. Closing / CTA
- Similar to title slide
- Clear call-to-action or next steps
- Contact information or links in caption size

## Workflow

### Phase 1: Plan the Deck

Before touching the API, plan the full deck structure.

1. **Clarify the goal:** Ask the user (or infer) — what is this deck for? (pitch, internal update, teaching, proposal)
2. **Draft an outline:** List every slide with:
   - Slide number
   - Layout (from the layouts above)
   - Title text
   - Key content (bullets, data points, image descriptions)
3. **Apply the 1-idea-per-slide rule:** If any slide has 2+ distinct ideas, split it
4. **Check flow:** Title → Agenda/Overview → Content sections (with dividers) → Summary/CTA → Closing
5. **Present the outline to the user** for approval before building

**Slide count guidelines:**
- 5-minute talk: 8–12 slides
- 10-minute talk: 15–20 slides
- Read-ahead / memo deck: as many as needed, but each slide must stand alone

### Phase 2: Create the Presentation

```bash
# Create a blank presentation
gws slides presentations create --json '{"title": "TITLE_HERE"}'
```

Save the returned `presentationId` — all subsequent calls need it.

### Phase 3: Build Slides via batchUpdate

Build the deck using `presentations.batchUpdate`. Each call sends an array of requests that are applied atomically.

**Strategy:** Build in batches of 3–5 slides at a time. This keeps requests manageable and allows checkpoint validation.

#### Creating a slide

```json
{
  "createSlide": {
    "objectId": "slide_001",
    "insertionIndex": 0,
    "slideLayoutReference": {
      "predefinedLayout": "BLANK"
    }
  }
}
```

**Always use `BLANK` layout** and build content manually. The predefined layouts (TITLE, TITLE_AND_BODY, etc.) have poor default styling that fights our design system.

#### Adding text

```json
{
  "createShape": {
    "objectId": "slide_001_title",
    "shapeType": "TEXT_BOX",
    "elementProperties": {
      "pageObjectId": "slide_001",
      "size": {
        "width": {"magnitude": 540, "unit": "PT"},
        "height": {"magnitude": 50, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 54, "translateY": 72,
        "unit": "PT"
      }
    }
  }
}
```

Then insert text and style it:

```json
{
  "insertText": {
    "objectId": "slide_001_title",
    "text": "Your Slide Title"
  }
},
{
  "updateTextStyle": {
    "objectId": "slide_001_title",
    "style": {
      "fontFamily": "Google Sans",
      "fontSize": {"magnitude": 40, "unit": "PT"},
      "foregroundColor": {
        "opaqueColor": {"rgbColor": {"red": 0.102, "green": 0.102, "blue": 0.180}}
      },
      "bold": true
    },
    "textRange": {"type": "ALL"},
    "fields": "fontFamily,fontSize,foregroundColor,bold"
  }
}
```

#### Adding shapes and rectangles

For content cards, accent bars, divider lines:

```json
{
  "createShape": {
    "objectId": "slide_003_card_bg",
    "shapeType": "RECTANGLE",
    "elementProperties": {
      "pageObjectId": "slide_003",
      "size": {
        "width": {"magnitude": 260, "unit": "PT"},
        "height": {"magnitude": 200, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 54, "translateY": 120,
        "unit": "PT"
      }
    }
  }
},
{
  "updateShapeProperties": {
    "objectId": "slide_003_card_bg",
    "shapeProperties": {
      "shapeBackgroundFill": {
        "solidFill": {
          "color": {"rgbColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}
        }
      },
      "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": {"red": 0.855, "green": 0.859, "blue": 0.878}}}}, "weight": {"magnitude": 1, "unit": "PT"}},
      "shadow": {
        "type": "OUTER",
        "blurRadius": {"magnitude": 8, "unit": "PT"},
        "color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}},
        "alpha": 0.08,
        "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 2, "unit": "PT"}
      }
    },
    "fields": "shapeBackgroundFill,outline,shadow"
  }
}
```

#### Setting slide background

```json
{
  "updatePageProperties": {
    "objectId": "slide_002",
    "pageProperties": {
      "pageBackgroundFill": {
        "solidFill": {
          "color": {"rgbColor": {"red": 0.102, "green": 0.102, "blue": 0.180}}
        }
      }
    },
    "fields": "pageBackgroundFill"
  }
}
```

#### Adding images

```json
{
  "createImage": {
    "objectId": "slide_007_img",
    "url": "https://example.com/image.png",
    "elementProperties": {
      "pageObjectId": "slide_007",
      "size": {
        "width": {"magnitude": 360, "unit": "PT"},
        "height": {"magnitude": 405, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 360, "translateY": 0,
        "unit": "PT"
      }
    }
  }
}
```

Images must be publicly accessible URLs. If the user provides local files, ask them to upload to Google Drive first, then use the Drive file URL.

### Phase 4: Quality Check Loop

**This phase is mandatory. Never skip it.**

After building each batch of 3–5 slides, and again after the full deck is complete, run this quality check:

#### Step 1: Retrieve the presentation

```bash
gws slides presentations get --params '{"presentationId": "PRESENTATION_ID"}'
```

#### Step 2: Inspect every slide against the checklist

For each slide, verify:

**Typography:**
- [ ] No more than 2 font sizes used
- [ ] Title is 36–56 pt depending on layout
- [ ] Body text is 16–18 pt
- [ ] Font is from the approved stack
- [ ] No ALL CAPS blocks longer than 3 words
- [ ] Title case for titles, sentence case for body

**Color:**
- [ ] Maximum 3 colors on the slide (background + text + accent)
- [ ] Text has sufficient contrast against background
- [ ] Accent colors used sparingly (small shapes, highlights, not large areas)

**Spacing:**
- [ ] All content within the safe zone (0.5" from edges)
- [ ] Body content within comfortable zone (0.75" from sides)
- [ ] Consistent spacing between same-type elements
- [ ] At least 40% whitespace on the slide

**Content:**
- [ ] One idea per slide
- [ ] Maximum 6 bullet points per slide
- [ ] Maximum 8 words per bullet point
- [ ] No paragraphs — if it reads like a paragraph, split it
- [ ] Slide title is 7 words or fewer

**Layout:**
- [ ] Slide uses a recognizable layout from the layout system
- [ ] Elements are visually aligned (shared edges or center axes)
- [ ] Visual hierarchy is clear (eye moves title → subtitle → body → detail)

#### Step 3: Fix violations

For any violations found, issue corrective `batchUpdate` requests. Common fixes:

| Problem | Fix |
|---------|-----|
| Text overflows shape | Reduce font size or split slide |
| Too many bullets | Split into two slides |
| Content outside safe zone | Adjust transform translateX/Y |
| Low contrast text | Change text color or background |
| Inconsistent spacing | Recalculate transforms for even distribution |
| Too many colors | Remove the least important accent color |

#### Step 4: Final pass

After all slides pass the per-slide check, do a deck-level review:

- [ ] Consistent title positioning across all content slides
- [ ] Section dividers appear before each new topic
- [ ] Color usage is consistent throughout (same accent for same meaning)
- [ ] Font sizes are consistent across same-role elements on different slides
- [ ] Slide count matches the expected range for the presentation length
- [ ] First slide is a title slide, last slide is a closing/CTA slide
- [ ] No two adjacent slides use the same layout (vary the rhythm)

Report the results to the user with a summary of what was checked and any remaining issues.

## Coordinate System Reference

The Slides API uses **EMU (English Metric Units)** internally, but accepts **PT (points)** which is more intuitive.

| Measurement | Points | Inches |
|-------------|--------|--------|
| Slide width | 720 pt | 10" |
| Slide height | 405 pt | 5.625" |
| Safe zone inset | 36 pt | 0.5" |
| Comfortable zone left/right | 54 pt | 0.75" |
| Comfortable zone top | 72 pt | 1.0" |
| Comfortable zone bottom | 43.2 pt | 0.6" |
| Usable width (comfortable) | 612 pt | 8.5" |
| Usable height (comfortable) | 289.8 pt | 4.025" |

**Transform origin is top-left of the slide.** `translateX` moves right, `translateY` moves down.

## Object ID Convention

Use predictable, descriptive IDs:

```
slide_001                    # Slide itself
slide_001_title              # Title text box
slide_001_subtitle           # Subtitle text box
slide_001_body               # Body text box
slide_001_card_1_bg          # First card background shape
slide_001_card_1_title       # First card title
slide_001_card_1_body        # First card body text
slide_001_accent_bar         # Decorative accent element
slide_001_img                # Image element
```

## Common Patterns

### Bullet list with proper spacing

Build bullets as a single text box with newlines. Use `updateParagraphStyle` to control bullet spacing:

```json
{
  "insertText": {
    "objectId": "slide_003_body",
    "text": "First point\nSecond point\nThird point"
  }
},
{
  "createParagraphBullets": {
    "objectId": "slide_003_body",
    "textRange": {"type": "ALL"},
    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
  }
},
{
  "updateParagraphStyle": {
    "objectId": "slide_003_body",
    "textRange": {"type": "ALL"},
    "style": {
      "spaceAbove": {"magnitude": 6, "unit": "PT"},
      "spaceBelow": {"magnitude": 6, "unit": "PT"},
      "lineSpacing": 150
    },
    "fields": "spaceAbove,spaceBelow,lineSpacing"
  }
}
```

### Accent bar (vertical, left of content)

```json
{
  "createShape": {
    "objectId": "slide_005_accent_bar",
    "shapeType": "RECTANGLE",
    "elementProperties": {
      "pageObjectId": "slide_005",
      "size": {
        "width": {"magnitude": 4, "unit": "PT"},
        "height": {"magnitude": 200, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 54, "translateY": 100,
        "unit": "PT"
      }
    }
  }
},
{
  "updateShapeProperties": {
    "objectId": "slide_005_accent_bar",
    "shapeProperties": {
      "shapeBackgroundFill": {
        "solidFill": {
          "color": {"rgbColor": {"red": 0.102, "green": 0.451, "blue": 0.910}}
        }
      },
      "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": {"red": 0.102, "green": 0.451, "blue": 0.910}}}}}
    },
    "fields": "shapeBackgroundFill,outline"
  }
}
```

### Content card with subtle shadow

See the shapes example in Phase 3. Use surface color (`#F8F9FA`) background, 1pt border in divider color, subtle outer shadow with 0.08 alpha.

## What NOT to Do

- **Don't use predefined layouts** — they have ugly defaults; always use BLANK and build manually
- **Don't dump paragraphs onto slides** — if it reads like a document, it's not a slide
- **Don't use more than 3 colors per slide** — restraint is what separates good from bad
- **Don't center everything** — centered body text looks amateurish; left-align body content
- **Don't skip the quality check loop** — every deck must pass the checklist
- **Don't use clip art, WordArt, or decorative fonts** — keep it clean and modern
- **Don't make slides without whitespace** — 40% whitespace minimum is a hard rule
- **Don't use tiny text to cram more in** — split the slide instead
- **Don't use gradients unless the user's brand requires them** — solid colors are cleaner
- **Don't forget to validate object IDs are unique** — duplicate IDs cause silent failures
- **Don't send more than ~20 requests per batchUpdate** — batch in groups of 3–5 slides
