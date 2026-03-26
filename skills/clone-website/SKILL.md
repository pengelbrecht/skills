---
name: clone-website
description: |
  Clone/replicate websites into production-ready Astro 6 code using agent-browser for scraping.
  Use when user asks to: clone website, vibe clone, replicate landing page, copy website design,
  rebuild this site, recreate this page, clone specific sections (hero, pricing, footer, etc).
  Triggers: "clone this website", "vibe clone [url]", "replicate this landing page",
  "rebuild this site in Astro", "clone the hero section from [url]", "copy this design".
---

# Clone Website Skill

Transform any website into production-ready Astro 6 code using agent-browser for headless scraping.

## Prerequisites

Before starting, verify that the required tools are installed. Run these checks and report any missing tools to the user:

```bash
# Required: agent-browser for scraping
agent-browser --version

# Required: Node.js for Astro project
node --version

# Required: npm or pnpm for package management
npm --version

# Optional: curl for downloading images
curl --version
```

If `agent-browser` is not installed:
```bash
npm install -g agent-browser && agent-browser install
```

If any tool is missing, **stop and inform the user** with install instructions before proceeding.

## Workflow

Execute these 3 phases in order. **Never skip Phase 2.**

### Phase 1: Scrape

1. Extract URL from user request
2. Identify section filter if specified (e.g., "hero only", "just the pricing")
3. Scrape using agent-browser in headless mode (default, no flags needed):

```bash
# Navigate and wait for full render
agent-browser open [TARGET_URL]
agent-browser wait --load networkidle

# Extract full page HTML
agent-browser eval "document.documentElement.outerHTML"

# Extract page text for content analysis
agent-browser get text "body"

# Get page title and meta
agent-browser eval "JSON.stringify({ title: document.title, meta: Array.from(document.querySelectorAll('meta')).map(m => ({ name: m.name || m.getAttribute('property'), content: m.content })) })"

# Get computed styles for design tokens
agent-browser eval "JSON.stringify({ fonts: getComputedStyle(document.body).fontFamily, bgColor: getComputedStyle(document.body).backgroundColor })"

# Take a reference screenshot
agent-browser screenshot ./reference.png

# Get accessibility snapshot for structure understanding
agent-browser snapshot

# Close browser when done
agent-browser close
```

4. If a specific section is requested, scope extraction:

```bash
agent-browser get html "#hero"
agent-browser get html "section.pricing"
agent-browser snapshot -s "#hero"
```

5. For extracting design tokens (colors, fonts, spacing), use eval with computed styles:

```bash
# Extract all CSS custom properties
agent-browser eval "JSON.stringify(Array.from(document.styleSheets).flatMap(s => { try { return Array.from(s.cssRules) } catch { return [] } }).filter(r => r.selectorText === ':root').flatMap(r => r.cssText.match(/--[^:]+:[^;]+/g) || []))"

# Extract key colors from elements
agent-browser eval "JSON.stringify(['h1','h2','p','a','button','nav','footer','header'].map(sel => { const el = document.querySelector(sel); if (!el) return null; const s = getComputedStyle(el); return { el: sel, color: s.color, bg: s.backgroundColor, font: s.fontFamily, size: s.fontSize } }).filter(Boolean))"
```

### Phase 2: Analysis (MANDATORY)

**STOP. Present analysis to user before ANY code generation.**

Read [references/analysis-template.md](references/analysis-template.md) and fill out the template with:
- Detected sections and component breakdown
- Extracted design tokens (colors, typography, spacing)
- Image inventory with download/fallback status
- Proposed file structure

Ask user: "Ready to proceed? (y/n or request modifications)"

**Do not generate code until user confirms.**

### Phase 3: Code Generation

After user confirmation, generate files in this order:

1. `src/styles/global.css` - Design tokens as CSS variables + Tailwind import
2. `src/layouts/Layout.astro` - Base layout with SEO metadata
3. `src/components/landing/[Section].astro` - Each static component
4. `src/components/landing/[Interactive].tsx` - Interactive islands (React) if needed
5. `src/pages/index.astro` - Main page composing components
6. Download images to `public/images/`
7. `astro.config.mjs` - Astro config with integrations
8. `package.json` - Dependencies

Reference [references/tech-stack.md](references/tech-stack.md) for Astro 6 conventions.
Reference [references/component-patterns.md](references/component-patterns.md) for component structure.

## Tech Stack (Fixed)

| Layer | Technology |
|-------|------------|
| Framework | Astro 6 (static + islands) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 |
| Interactive Islands | React (via `@astrojs/react`, only when needed) |
| Icons | Lucide (astro-icon or inline SVG) |
| Font | System fonts (default) or extracted from source |

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

1. Extract all image URLs from scraped content
2. Attempt download via `curl` or `agent-browser`
3. On failure, use Unsplash fallback:
   - Hero: `https://images.unsplash.com/photo-[id]?w=1920&h=1080`
   - Avatars: `https://images.unsplash.com/photo-[id]?w=100&h=100`
   - Features: Prefer Lucide icons or inline SVGs over images
4. Save to `public/images/` with descriptive kebab-case names
5. For optimized images, store in `src/images/` and use `<Image />` from `astro:assets`

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
