# Analysis Template

Use this template to present analysis in Phase 2. Fill all sections before asking user to confirm.

---

## Website Analysis Report

**Source URL**: [url]
**Scrape Status**: Success / Partial / Failed (with fallback)

---

### Page Structure

**Sections Detected**:
1. [ ] Header/Navigation
2. [ ] Hero
3. [ ] Features/Benefits
4. [ ] Social Proof/Testimonials
5. [ ] Pricing
6. [ ] FAQ
7. [ ] CTA
8. [ ] Footer

**Layout Pattern**: [single-column / two-column / grid / bento / asymmetric]
**Navigation Type**: [sticky / fixed / relative] + [hamburger mobile / full mobile nav]

---

### Design Tokens Extracted

**Colors**:
```css
--color-primary: #______;
--color-secondary: #______;
--color-accent: #______;
--color-background: #______;
--color-foreground: #______;
--color-muted: #______;
--color-border: #______;
```

**Typography**:
- Headings: [Font Family], weights: [400/500/600/700]
- Body: [Font Family], weights: [400/500]
- Scale: [h1: px, h2: px, h3: px, body: px, small: px]

**Spacing**:
- Base unit: [4px / 8px]
- Section gap: [px]
- Component gap: [px]
- Container max-width: [px]

**Border Radius**:
- Small: [px]
- Medium: [px]
- Large: [px]

---

### Component Breakdown

| # | Component | File | Type | Description | Complexity |
|---|-----------|------|------|-------------|------------|
| 1 | Header | `Header.astro` | Static | [description] | Low/Med/High |
| 2 | MobileMenu | `MobileMenu.tsx` | Island (`client:idle`) | [description] | Low/Med/High |
| 3 | Hero | `Hero.astro` | Static | [description] | Low/Med/High |
| 4 | Features | `Features.astro` | Static | [description] | Low/Med/High |
| ... | ... | ... | ... | ... | ... |

**Island justification**: List any components marked as islands and why they need client-side JS. If none need interactivity, state "No islands needed — fully static page."

---

### Images Inventory

| # | Source URL | Target Path | Status |
|---|------------|-------------|--------|
| 1 | [url] | `public/images/hero-bg.jpg` | Will download |
| 2 | [url] | `src/images/feature-1.png` | Will optimize via astro:assets |
| 3 | N/A | `public/images/avatar-1.jpg` | Using Unsplash fallback |

---

### Proposed File Structure

```
src/
├── layouts/
│   └── Layout.astro        # Base layout + metadata
├── pages/
│   └── index.astro          # Main page composition
├── components/
│   └── landing/
│       ├── Header.astro
│       ├── Hero.astro
│       ├── Features.astro
│       ├── [Other].astro
│       ├── Footer.astro
│       └── MobileMenu.tsx   # Only if interactive island needed
├── styles/
│   └── global.css           # Tailwind import + design tokens
└── images/                  # Optimized images (via astro:assets)

public/
└── images/
    ├── hero-bg.jpg          # Unprocessed static images
    └── [other images]

astro.config.mjs             # Astro config + integrations
package.json
```

---

### Notes & Considerations

- [Any special patterns observed]
- [Animations or interactions requiring islands]
- [Missing content that needs placeholders]
- [Accessibility considerations]
- [ ] Background video detected: [URL] — will embed as iframe / use poster image fallback (delete if none found)

---

**Ready to proceed with code generation? (y/n)**

If modifications needed, specify:
- Sections to skip
- Components to combine/split
- Design token adjustments
- Image handling preferences
- Which components should be islands vs static
