# API Patterns Reference

JSON examples for all common `batchUpdate` operations. Every example uses placeholder values — substitute theme colors, fonts, and computed positions from the loaded theme.

## Table of Contents

- [Creating a Slide](#creating-a-slide)
- [Adding Text](#adding-text)
- [Styling Text](#styling-text)
- [Faux Bullet Lists](#faux-bullet-lists)
- [Shapes and Rectangles](#shapes-and-rectangles)
- [Accent Bars](#accent-bars)
- [Content Cards](#content-cards)
- [Setting Slide Background](#setting-slide-background)
- [Generating Charts](#generating-charts)
- [Uploading Images](#uploading-images)
- [Adding Images to Slides](#adding-images-to-slides)
- [Adding a Logo](#adding-a-logo)
- [Visual Verification](#visual-verification)
- [Coordinate System](#coordinate-system)
- [Object ID Convention](#object-id-convention)

---

## Creating a Slide

Always use `BLANK` layout. The predefined layouts (TITLE, TITLE_AND_BODY, etc.) impose default styling that conflicts with theme-driven design.

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

## Adding Text

Create a text box, then insert text into it:

```json
{
  "createShape": {
    "objectId": "slide_001_title",
    "shapeType": "TEXT_BOX",
    "elementProperties": {
      "pageObjectId": "slide_001",
      "size": {
        "width": {"magnitude": 612, "unit": "PT"},
        "height": {"magnitude": 50, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 54, "translateY": 72,
        "unit": "PT"
      }
    }
  }
},
{
  "insertText": {
    "objectId": "slide_001_title",
    "text": "Your Slide Title"
  }
}
```

**Positioning notes:**
- `translateX: 54` = comfortable zone left margin (0.75")
- `translateY: 72` = comfortable zone top margin (1.0")
- `width: 612` = usable width within comfortable zone (720 - 54 - 54)
- Transform origin is top-left of the slide; X increases right, Y increases down

## Styling Text

Apply font, size, color, and weight. Always use the theme's font family and color values.

```json
{
  "updateTextStyle": {
    "objectId": "slide_001_title",
    "style": {
      "fontFamily": "THEME_FONT_FAMILY",
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

**Converting hex to RGB floats:** Divide each component by 255. For example, `#1A1A2E` → red: 0.102, green: 0.102, blue: 0.180.

**Letter spacing** via `updateParagraphStyle`:

```json
{
  "updateParagraphStyle": {
    "objectId": "slide_001_title",
    "textRange": {"type": "ALL"},
    "style": {
      "lineSpacing": 115,
      "spaceAbove": {"magnitude": 0, "unit": "PT"},
      "spaceBelow": {"magnitude": 0, "unit": "PT"}
    },
    "fields": "lineSpacing,spaceAbove,spaceBelow"
  }
}
```

Note: `lineSpacing` is a percentage (115 = 1.15×). The Slides API does not support letter-spacing directly — it's a visual guideline for font selection, not an API parameter.

## Faux Bullet Lists

**Do not use `createParagraphBullets`.** The Google Slides API cannot color native bullet glyphs independently from paragraph text — this is a known, confirmed API limitation. Instead, use "faux bullets": Unicode glyph characters inserted as text, colored with `accent_primary`, with tab characters and paragraph indentation to create a proper hanging indent.

### Bullet styles (max 2 levels)

| Style | L1 glyph | L2 glyph | Feel |
|-------|----------|----------|------|
| **disc** (default) | `●` | `○` | Clean, universal |
| **square** | `■` | `–` | Bold, editorial |
| **arrow** | `→` | `▸` | Modern, techy |

### How it works

Each bullet line is: `GLYPH\tText content\n`. The tab character snaps to the `indentStart` position, creating the gap between glyph and text. Wrapped lines align at `indentStart` too (hanging indent).

**Glyph sizing:** Keep glyphs at the same font size as their line's text. Unicode bullet characters are naturally proportioned within the em box — they appear smaller than letters and align on the baseline without needing size reduction.

### Step 1: Insert text with glyph prefixes

```json
{
  "insertText": {
    "objectId": "slide_003_body",
    "text": "●\tFirst top-level bullet\n○\tA sub-bullet with detail\n○\tAnother sub-bullet\n●\tSecond top-level bullet"
  }
}
```

### Step 2: Apply base text styling

```json
{
  "updateTextStyle": {
    "objectId": "slide_003_body",
    "style": {
      "fontFamily": "THEME_FONT_FAMILY",
      "fontSize": {"magnitude": 17, "unit": "PT"},
      "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.059, "green": 0.090, "blue": 0.165}}}
    },
    "textRange": {"type": "ALL"},
    "fields": "fontFamily,fontSize,foregroundColor"
  }
}
```

### Step 3: Apply paragraph indentation per level

**L1 paragraphs** — glyph at left edge, text indented 28pt:
```json
{
  "updateParagraphStyle": {
    "objectId": "slide_003_body",
    "textRange": {"type": "FIXED_RANGE", "startIndex": L1_START, "endIndex": L1_END},
    "style": {
      "indentFirstLine": {"magnitude": 0, "unit": "PT"},
      "indentStart": {"magnitude": 28, "unit": "PT"},
      "lineSpacing": 115,
      "spaceAbove": {"magnitude": 14, "unit": "PT"},
      "spaceBelow": {"magnitude": 0, "unit": "PT"}
    },
    "fields": "indentFirstLine,indentStart,lineSpacing,spaceAbove,spaceBelow"
  }
}
```

**L2 paragraphs** — glyph at 28pt, text indented 48pt:
```json
{
  "updateParagraphStyle": {
    "objectId": "slide_003_body",
    "textRange": {"type": "FIXED_RANGE", "startIndex": L2_START, "endIndex": L2_END},
    "style": {
      "indentFirstLine": {"magnitude": 28, "unit": "PT"},
      "indentStart": {"magnitude": 48, "unit": "PT"},
      "lineSpacing": 115,
      "spaceAbove": {"magnitude": 4, "unit": "PT"},
      "spaceBelow": {"magnitude": 0, "unit": "PT"}
    },
    "fields": "indentFirstLine,indentStart,lineSpacing,spaceAbove,spaceBelow"
  }
}
```

**Spacing logic:**
- First bullet on slide: `spaceAbove: 0`
- L1 after L1 or L2 (new group): `spaceAbove: 14pt`
- L2 after L1 or L2 (within group): `spaceAbove: 4pt`
- `lineSpacing: 115` everywhere (tight within multiline bullets)

### Step 4: Style L2 text (smaller, secondary color)

```json
{
  "updateTextStyle": {
    "objectId": "slide_003_body",
    "style": {
      "fontSize": {"magnitude": 15, "unit": "PT"},
      "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.392, "green": 0.455, "blue": 0.545}}}
    },
    "textRange": {"type": "FIXED_RANGE", "startIndex": L2_START, "endIndex": L2_END},
    "fields": "fontSize,foregroundColor"
  }
}
```

### Step 5: Color the glyph characters accent

Use `FIXED_RANGE` targeting just the single glyph character at the start of each paragraph:

```json
{
  "updateTextStyle": {
    "objectId": "slide_003_body",
    "style": {
      "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.031, "green": 0.569, "blue": 0.698}}}
    },
    "textRange": {"type": "FIXED_RANGE", "startIndex": GLYPH_INDEX, "endIndex": GLYPH_INDEX + 1},
    "fields": "foregroundColor"
  }
}
```

Repeat for every bullet glyph character in the text box. The glyph is always at the `startIndex` of each paragraph (the character before the `\t`).

## Shapes and Rectangles

For content cards, divider lines, background shapes:

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
      "outline": {
        "outlineFill": {
          "solidFill": {
            "color": {"rgbColor": {"red": 0.855, "green": 0.859, "blue": 0.878}}
          }
        },
        "weight": {"magnitude": 1, "unit": "PT"}
      }
    },
    "fields": "shapeBackgroundFill,outline"
  }
}
```

## Accent Bars

A thin vertical rectangle left of content, in the theme's accent_primary color. Use on **non-bullet slides only** (quotes, plain body text) — on bullet slides the bar collides visually with bullet markers, so use accent-colored bullets instead.

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
      "outline": {
        "outlineFill": {
          "solidFill": {
            "color": {"rgbColor": {"red": 0.102, "green": 0.451, "blue": 0.910}}
          }
        }
      }
    },
    "fields": "shapeBackgroundFill,outline"
  }
}
```

## Content Cards

Combine a surface-colored rectangle with subtle shadow for a polished card effect:

```json
{
  "updateShapeProperties": {
    "objectId": "slide_003_card_bg",
    "shapeProperties": {
      "shapeBackgroundFill": {
        "solidFill": {
          "color": {"rgbColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}
        }
      },
      "outline": {
        "outlineFill": {
          "solidFill": {
            "color": {"rgbColor": {"red": 0.855, "green": 0.859, "blue": 0.878}}
          }
        },
        "weight": {"magnitude": 1, "unit": "PT"}
      },
      "shadow": {
        "type": "OUTER",
        "blurRadius": {"magnitude": 8, "unit": "PT"},
        "color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}},
        "alpha": 0.08,
        "transform": {
          "scaleX": 1, "scaleY": 1,
          "translateX": 0, "translateY": 2,
          "unit": "PT"
        }
      }
    },
    "fields": "shapeBackgroundFill,outline,shadow"
  }
}
```

Use `surface` color for the background and `divider` color for the border. The shadow is subtle (0.08 alpha, 2pt Y offset) — enough to lift the card without looking dated.

## Full-Bleed Image with Scrim

For dramatic photo slides with overlay text. The scrim is a semi-transparent black rectangle that ensures text legibility over any image.

**Construction order matters:** image first → scrim → text (z-index follows creation order).

```json
{
  "createImage": {
    "objectId": "slide_008_bg",
    "url": "IMAGE_URL",
    "elementProperties": {
      "pageObjectId": "slide_008",
      "size": {"width": {"magnitude": 720, "unit": "PT"}, "height": {"magnitude": 405, "unit": "PT"}},
      "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "PT"}
    }
  }
},
{
  "createShape": {
    "objectId": "slide_008_scrim",
    "shapeType": "RECTANGLE",
    "elementProperties": {
      "pageObjectId": "slide_008",
      "size": {"width": {"magnitude": 720, "unit": "PT"}, "height": {"magnitude": 110, "unit": "PT"}},
      "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 148, "unit": "PT"}
    }
  }
},
{
  "updateShapeProperties": {
    "objectId": "slide_008_scrim",
    "shapeProperties": {
      "shapeBackgroundFill": {
        "solidFill": {
          "color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}},
          "alpha": 0.55
        }
      },
      "outline": {"propertyState": "NOT_RENDERED"}
    },
    "fields": "shapeBackgroundFill,outline"
  }
}
```

Then add a text box on top of the scrim with white bold text, center-aligned. Size the scrim height to cover the title including any line wraps — a 36pt title wrapping to 2 lines needs ~110pt scrim height. For single-line titles, 70pt is sufficient.

## Setting Slide Background

For dark section dividers or branded slides:

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

Use the theme's `dark_bg` color. Remember to switch text to `dark_text` and accents to `dark_accent` on dark backgrounds.

## Generating Charts

The Slides API has no native chart creation. Generate charts as high-DPI PNG images using matplotlib, plotly, or similar, then insert via the image upload pipeline.

**Key guidelines:**
- Use theme colors for bars, lines, and labels — not library defaults
- Set `dpi=144` for sharp rendering on projected slides
- Use `figsize=(10, 5.625)` for a full-slide chart, or smaller for partial
- Match the theme font if matplotlib supports it
- Set figure and axes background to white (or transparent)
- Remove chart chrome that competes with the slide design (minimize spines, grid lines)

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 5.625), dpi=144)
fig.patch.set_facecolor('white')
# ... build chart using theme colors ...
plt.savefig('chart.png', dpi=144, facecolor='white', bbox_inches='tight')
```

After saving, upload via the Drive pipeline (see below) and insert with `createImage`. Leave room for a title above and an optional caption below — don't let the chart fill the entire slide.

## Uploading Images

The Slides API requires images to be accessible via public URL. For local files, use this pipeline:

**Step 1: Convert SVGs to PNG** (Slides API only accepts raster images — PNG, JPEG, GIF):
```bash
rsvg-convert -w 680 -h 256 logo.svg -o logo.png
# or: convert logo.svg logo.png  (ImageMagick)
# or: sips -s format png logo.svg --out logo.png  (macOS built-in)
```

**Step 2: Upload to Google Drive:**
```bash
gws drive +upload ./logo.png --name "deck-logo.png"
# Returns JSON with "id" field — save this file ID
```

**Step 3: Share the file** (required — the Slides API fetches images server-side and cannot use the user's Drive session):
```bash
gws drive permissions create --params '{"fileId": "FILE_ID"}' --json '{"role": "reader", "type": "anyone"}'
```

**Step 4: Use the Drive URL in `createImage`:**
```
https://drive.google.com/uc?id=FILE_ID
```

> **Remember:** `gws` outputs `Using keyring backend: keyring` before JSON. When extracting the file ID programmatically, skip the first line.

## Adding Images to Slides

```json
{
  "createImage": {
    "objectId": "slide_007_img",
    "url": "https://drive.google.com/uc?id=FILE_ID",
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

Images can be publicly accessible URLs or Drive files shared via the upload pipeline above.

## Adding a Logo

Place the logo as a small image element. Position depends on the theme's `logo.placement`:

| Placement | translateX | translateY | Notes |
|-----------|-----------|-----------|-------|
| `bottom-right` | `720 - 36 - logo_width` | `405 - 36 - logo_height` | Inside safe zone, bottom-right corner |
| `bottom-left` | `36` | `405 - 36 - logo_height` | Inside safe zone, bottom-left corner |
| `bottom-center` | `(720 - logo_width) / 2` | `405 - 36 - logo_height` | Centered horizontally, bottom safe zone |
| `title-only` | Same as `bottom-right` | Same | Only on title + closing slides |

Calculate `logo_width` proportionally from `logo.height` (maintain aspect ratio). If the theme has a local `logo.path`, upload it using the image upload pipeline above first to get a Drive URL.

```json
{
  "createImage": {
    "objectId": "slide_001_logo",
    "url": "THEME_LOGO_URL",
    "elementProperties": {
      "pageObjectId": "slide_001",
      "size": {
        "width": {"magnitude": 72, "unit": "PT"},
        "height": {"magnitude": 24, "unit": "PT"}
      },
      "transform": {
        "scaleX": 1, "scaleY": 1,
        "translateX": 612, "translateY": 345,
        "unit": "PT"
      }
    }
  }
}
```

---

## Coordinate System

The Slides API accepts **PT (points)**, which maps cleanly to inches (72 pt = 1").

| Measurement | Points | Inches |
|-------------|--------|--------|
| Slide width | 720 pt | 10" |
| Slide height | 405 pt | 5.625" |
| Safe zone inset | 36 pt | 0.5" |
| Comfortable zone left/right | 54 pt | 0.75" |
| Comfortable zone top | 72 pt | 1.0" |
| Comfortable zone bottom | 43 pt | 0.6" |
| Usable width (comfortable) | 612 pt | 8.5" |
| Usable height (comfortable) | 290 pt | 4.0" |

**Transform origin is top-left.** `translateX` increases rightward, `translateY` increases downward.

## Object ID Convention

Use predictable, descriptive IDs so elements are easy to reference in later batchUpdate calls:

```
slide_001                    # Slide itself
slide_001_title              # Title text box
slide_001_subtitle           # Subtitle text box
slide_001_body               # Body text box
slide_001_card_1_bg          # First card background shape
slide_001_card_1_title       # First card title text
slide_001_card_1_body        # First card body text
slide_001_accent_bar         # Decorative accent element
slide_001_img                # Image element
slide_001_logo               # Logo image
```

All IDs must be unique across the entire presentation. Duplicate IDs cause silent failures in the API.

## Visual Verification

Use `getThumbnail` to download slide renders as PNG for visual inspection. This catches issues that JSON-level checks miss: element overlap, text truncation, alignment problems, and color rendering.

```bash
gws slides presentations pages getThumbnail \
  --params '{"presentationId": "PRES_ID", "pageObjectId": "slide_001"}'
# Returns JSON with "contentUrl" — download it with curl
```

The returned URL is a temporary Google-hosted PNG (1600×900). Download and inspect:

```bash
curl -sL "CONTENT_URL" -o slide_001_thumb.png
```

**When to use:** After each batch during Phase 4 quality check. At minimum, spot-check: the title slide, one bullet slide, any chart slide, and the closing slide.
