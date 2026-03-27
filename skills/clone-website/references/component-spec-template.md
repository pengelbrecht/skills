# Component Spec Template

Write one spec file per component to `docs/research/components/<component-name>.spec.md` before generating any code. This is the contract between extraction and building.

---

```markdown
# <ComponentName> Specification

## Overview
- **Target file:** `src/components/landing/<ComponentName>.astro` (or `.tsx` if island)
- **Screenshot:** `docs/design-references/<screenshot-name>.png`
- **Interaction model:** static | click-driven | scroll-driven | hover-driven | time-driven | mixed

## DOM Structure

Describe the element hierarchy — what contains what, in order.

## Computed Styles (exact values from getComputedStyle)

### Container
- display: <value>
- padding: <value>
- maxWidth: <value>
- backgroundColor: <value>
- (every relevant property with exact values)

### Heading
- fontSize: <value>
- fontWeight: <value>
- fontFamily: <value>
- lineHeight: <value>
- letterSpacing: <value>
- color: <value>
- (every relevant property)

### [Other child elements...]
(Repeat for each significant element)

## States & Behaviors

### <Behavior name>
- **Trigger:** scroll position <N>px | IntersectionObserver rootMargin | click on <selector> | hover on <selector> | timer <N>ms
- **State A (before):** property: value, property: value, ...
- **State B (after):** property: value, property: value, ...
- **Transition:** CSS transition string (e.g., `all 0.3s ease`)
- **Implementation approach:** CSS transition | CSS animation | IntersectionObserver | scroll-timeline | React state

### Hover States
- **<Element>:** property: <before> → <after>, transition: <value>

## Per-State Content (if applicable)

### State: "<Tab/Slide name>"
- Title: "..."
- Body: "..."
- Cards: [{ title, description, image, link }, ...]

### State: "<Another tab/slide>"
- ...

## Assets
- Background image: `public/images/<file>.webp` (downloaded / needs download / Unsplash fallback)
- Icons used: <list inline SVGs or Lucide icon names>
- Videos: `public/videos/<file>.mp4` or iframe embed URL
- Layered images: list each layer with z-index order

## Text Content (verbatim)

Copy-paste ALL text content from the live site. Do not paraphrase.

## Responsive Behavior
- **Desktop (1440px):** <description of layout, sizing>
- **Tablet (768px):** <what changes — columns, font sizes, spacing, visibility>
- **Mobile (390px):** <what changes — stacking, hidden elements, touch targets>
- **Breakpoint:** ~<N>px where the layout shifts
```
