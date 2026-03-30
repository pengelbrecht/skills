# Standard Layouts

Every slide uses exactly one of these 10 layouts. Consistent structure helps the audience focus on content rather than figuring out where to look next.

All positions use comfortable-zone coordinates (left margin at 54 pt). Title top position depends on mode: **standard** at 54 pt for light slides, **dense** at 36 pt for heavy slides (chart, terminal, grid, two-column, >4 bullets).

---

## 1. Title Slide

The opening slide. Sets the tone for the entire deck.

- **Title:** Large (40–44 pt, bold), centered vertically and horizontally on the slide
- **Subtitle:** Below title, 20–24 pt, in `text_secondary` color
- **Logo:** Bottom-right (or per theme `logo.placement`), using theme logo
- **Background:** White or theme `dark_bg` for a dramatic opener
- **Content density:** Minimal — title, subtitle, logo, nothing else

**Positioning guide:**
- Title center: ~translateY 150 pt (vertically centered)
- Subtitle: ~30 pt below title baseline
- Logo: see logo placement table in api-patterns.md

## 2. Section Divider

A visual pause that signals "new topic." These are the punctuation marks of your deck.

- **Title:** 48–56 pt, centered or left-aligned, bold
- **Background:** Theme `dark_bg` or `accent_primary`, full bleed
- **Text color:** `dark_text` (white) for contrast
- **Optional:** Section number in `dark_accent` color, top-left
- **No body text** — this slide is a breath, not a content carrier

**Positioning guide:**
- Title centered vertically (~translateY 160 pt) or at comfortable-zone top
- Section number (if used): 14 pt, top-left at (54, 36)

## 3. Title + Body

The workhorse layout — used for most content slides.

- **Title:** Top-left of comfortable zone (54, 72), 36–40 pt, bold
- **Body:** Left-aligned below title, starting ~25 pt (M spacing) below title baseline
- **Optional visual:** Right 40% of slide can hold a supporting image, chart, or icon
- **If no visual:** Body spans full comfortable width (612 pt) but add extra right margin (~80 pt) for breathing room

**Positioning guide:**
- Title: (54, 72), width 612 pt (or 350 pt if right visual present)
- Body: (54, ~130), width matches title
- Right visual: (400, 72), width ~280 pt, height ~290 pt

## 4. Two-Column

For comparisons, before/after, pros/cons, or parallel concepts.

- **Title:** Full width at top of comfortable zone
- **Two columns below:** Each ~290 pt wide with ~30 pt gutter between them
- **Each column** can contain text, bullets, images, or a mix
- **Column headers** (optional): 20 pt, bold, in `accent_primary`

**Positioning guide:**
- Title: (54, 72), width 612 pt
- Left column: (54, ~130), width 290 pt
- Right column: (374, ~130), width 290 pt
- Gutter: 30 pt between columns

## 5. Grid (2×2 or 3×1)

For features, pillars, team members, or any set of 3–4 parallel items.

**2×2 variant:**
- Title at top
- Four equal cards in a 2×2 grid
- Each card: ~290 pt wide, ~130 pt tall

**3×1 variant:**
- Title at top
- Three cards in a row
- Each card: ~190 pt wide, ~230 pt tall

Cards should have consistent internal structure: icon or number at top, card title (bold, 16 pt), description below (regular, 14 pt). Use the `surface` color for card backgrounds.

**Positioning guide (2×2):**
- Top-left card: (54, 130), size 290 × 130
- Top-right card: (374, 130), size 290 × 130
- Bottom-left card: (54, 275), size 290 × 130
- Bottom-right card: (374, 275), size 290 × 130

**Positioning guide (3×1):**
- Left card: (54, 130), size 190 × 230
- Center card: (264, 130), size 190 × 230
- Right card: (474, 130), size 190 × 230

## 6. Big Number / Statistic

For KPIs, milestones, impact statements. Makes one number impossible to ignore.

- **Number:** 60–80 pt, bold, in `accent_primary` — the visual anchor
- **Label:** Above or below the number, 14 pt, in `text_secondary`
- **Context:** One sentence of body text, 16 pt, below the number
- **Accent bar** (optional): Vertical bar left of the number for added emphasis

**Positioning guide:**
- Number: centered or left-aligned, translateY ~150 pt
- Label: 14 pt above or 10 pt below the number
- Context line: ~40 pt below number baseline

## 7. Image + Text (Split)

Slide divided roughly 50/50 or 60/40 between an image and text.

- **Image side:** Full height, bleeding to the slide edge (no margin on the image side)
- **Text side:** Title + body with comfortable margins
- **Image can be left or right** — vary across the deck for visual rhythm

**Positioning guide (image left, 50/50):**
- Image: (0, 0), width 360 pt, height 405 pt (full bleed left)
- Title: (390, 72), width 290 pt
- Body: (390, ~130), width 290 pt

**Positioning guide (image right, 60/40):**
- Title: (54, 72), width 350 pt
- Body: (54, ~130), width 350 pt
- Image: (430, 0), width 290 pt, height 405 pt (full bleed right)

## 8. Full-Bleed Image

Image covers the entire slide edge-to-edge. Use sparingly — 1–2 per deck maximum. Great for dramatic openers, transitions, or emotional impact.

- **Image:** Covers full 720 × 405 pt, no margins — bleeds to all 4 edges
- **Scrim:** Full-width semi-transparent dark rectangle behind the title text. Black fill at 55% opacity (`alpha: 0.55`). Sized to cover the title text with comfortable padding — typically 110pt tall, vertically centered on the slide.
- **Title:** White bold text, centered, sitting on top of the scrim. Use the theme font.
- **Important:** The scrim must be tall enough to cover wrapped text. Calculate scrim height based on the title's line count at the chosen font size (e.g., 36pt × 2 lines ≈ 80pt + 30pt padding = 110pt). The text box and scrim should be vertically aligned.

**Positioning guide:**
- Image: (0, 0), width 720 pt, height 405 pt
- Scrim: (0, 148), width 720 pt, height 110 pt, black `solidFill` with `alpha: 0.55`, outline `NOT_RENDERED`
- Title text box: (40, 155), width 640 pt, height 96 pt, white bold 36pt, center-aligned

**Construction order matters:** Create image first, then scrim on top, then text box on top of scrim. The Slides API renders elements in creation order (z-index).

## 9. Quote

For testimonials, key quotes, or emphasized statements.

- **Quote text:** 24–28 pt, italic weight or regular with accent styling
- **Attribution:** Below quote, 14 pt, `text_secondary`
- **Visual treatment:** Vertical accent bar left of the quote, or a large decorative quotation mark (60+ pt, `accent_primary` at low opacity)
- **Generous whitespace** — quotes need room to breathe

**Positioning guide:**
- Accent bar: (54, 100), width 4 pt, height 200 pt
- Quote text: (76, 120), width 560 pt (indented past accent bar)
- Attribution: (76, ~30 pt below quote baseline), width 560 pt

## 10. Closing / CTA

The last slide. Similar structure to the title slide but forward-looking.

- **Headline:** Call-to-action or key takeaway, 36–40 pt, bold
- **Supporting text:** Next steps, contact info, or links, 16 pt
- **Logo:** Same placement as title slide
- **Background:** Match the title slide (white or dark) for visual bookending

**Positioning guide:**
- Same as Title Slide, with headline replacing the title and supporting text replacing the subtitle

## 11. Terminal / CLI

For technical presentations showing CLI commands, API calls, or code. Uses dense title positioning.

- **Background:** White (standard slide background — not dark)
- **Title:** Normal theme styling (dark text on white), dense position (translateY: 36)
- **Terminal card:** A dark rectangle with window chrome bar and syntax-colored monospace text
- **Window chrome:** Thin dark bar (22pt tall) across the top of the card with three small dots (●●●) in muted gray — gives the "terminal window" feel
- **Code area:** Dark rectangle below chrome, filled with monospace text (theme `font.mono`)

**Syntax color scheme for code:**
| Element | Color | Example |
|---------|-------|---------|
| `$` prompt | Green (#34C759) | `$` |
| Command name | White, bold | `lore query` |
| Flags | Accent primary (#0891B2) | `--org` |
| Flag values | Light accent (#A5F3FC) | `acme` |
| Strings | Amber (#F59E0B) | `"SELECT ..."` |
| Output text | Muted gray (#959AA6) | table data |
| Table dividers | Dim gray (#4D5360) | `──────` |
| Success markers | Green (#34C759) | `✓` |

**Positioning guide (dense mode):**
- Title: (54, 36), width 612 pt
- Chrome bar: (54, 130), width 612 pt, height 22 pt, dark fill (#262833)
- Dots: (62, 132), small text `● ● ●` at 7pt in muted gray
- Code area: (54, 152), width 612 pt, height 235 pt, dark fill (#191D28)
- Code text: (74, 162), width 572 pt, monospace 11pt, lineSpacing 150

**Construction order:** chrome bar → dots text box → code area background → code text box (z-index follows creation order).

**Content guidelines:**
- Keep commands short enough to not wrap at 11pt monospace on 572pt width (~65 characters)
- Two commands with output is a good density — more than three gets cramped
- Use blank lines (`\n\n`) to separate command/output blocks
- Color each element with `FIXED_RANGE` targeting — this requires tracking character indices
