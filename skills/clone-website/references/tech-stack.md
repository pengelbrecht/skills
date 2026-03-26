# Tech Stack Reference — Astro 6

## Project Setup

```bash
npm create astro@latest -- --template minimal
npx astro add react      # Only if islands are needed
npx astro add tailwind   # Tailwind v4 integration
```

## Astro Config

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';       // Only if islands needed
import tailwindcss from '@astrojs/tailwind';

export default defineConfig({
  integrations: [
    tailwindcss(),
    react(),  // Only if islands needed
  ],
});
```

## File Structure

```
src/
├── layouts/
│   └── Layout.astro      # Base layout (required)
├── pages/
│   └── index.astro        # Home page (file-based routing)
├── components/
│   └── landing/            # Page-specific components
│       ├── Header.astro    # Static components
│       └── MobileMenu.tsx  # Interactive islands (React)
├── styles/
│   └── global.css          # Global styles + Tailwind
└── images/                 # Optimized images

public/
└── images/                 # Static assets (no processing)
```

## Base Layout Template

```astro
---
// src/layouts/Layout.astro
interface Props {
  title: string;
  description?: string;
  ogImage?: string;
}

const { title, description = "Site description", ogImage = "/images/og-image.jpg" } = Astro.props;

import "../styles/global.css";
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={description} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    <meta property="og:image" content={ogImage} />
    <meta property="og:type" content="website" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>{title}</title>
  </head>
  <body class="min-h-screen bg-background text-foreground antialiased">
    <slot />
  </body>
</html>
```

## Page Template

```astro
---
// src/pages/index.astro
import Layout from "../layouts/Layout.astro";
import Header from "../components/landing/Header.astro";
import Hero from "../components/landing/Hero.astro";
import Features from "../components/landing/Features.astro";
import Footer from "../components/landing/Footer.astro";
---

<Layout title="Page Title | Brand" description="Meta description from scrape">
  <Header />
  <main>
    <Hero />
    <Features />
    <!-- Other sections -->
  </main>
  <Footer />
</Layout>
```

## Tailwind CSS v4

### global.css Structure

```css
/* src/styles/global.css */
@import "tailwindcss";

/* Design tokens as CSS custom properties */
:root {
  --color-background: #ffffff;
  --color-foreground: #0a0a0a;
  --color-primary: #2563eb;
  --color-primary-foreground: #ffffff;
  --color-secondary: #f1f5f9;
  --color-secondary-foreground: #0f172a;
  --color-muted: #f1f5f9;
  --color-muted-foreground: #64748b;
  --color-accent: #f1f5f9;
  --color-accent-foreground: #0f172a;
  --color-border: #e2e8f0;
  --color-ring: #2563eb;
  --radius: 0.5rem;
}

/* Tailwind v4: use @theme to register custom values */
@theme {
  --color-background: var(--color-background);
  --color-foreground: var(--color-foreground);
  --color-primary: var(--color-primary);
  --color-primary-foreground: var(--color-primary-foreground);
  --color-secondary: var(--color-secondary);
  --color-secondary-foreground: var(--color-secondary-foreground);
  --color-muted: var(--color-muted);
  --color-muted-foreground: var(--color-muted-foreground);
  --color-accent: var(--color-accent);
  --color-accent-foreground: var(--color-accent-foreground);
  --color-border: var(--color-border);
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### Responsive Breakpoints (Mobile First)

```
sm: 640px   — Small tablets
md: 768px   — Tablets
lg: 1024px  — Small laptops
xl: 1280px  — Desktops
2xl: 1536px — Large screens
```

### Common Patterns

```html
<!-- Container with max-width -->
<div class="container mx-auto px-4">

<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Responsive text -->
<h1 class="text-3xl md:text-4xl lg:text-5xl">

<!-- Responsive spacing -->
<section class="py-12 md:py-20 lg:py-32">

<!-- Responsive visibility -->
<div class="hidden md:block">  <!-- Hide on mobile -->
<div class="md:hidden">        <!-- Show only on mobile -->
```

## Astro Components (.astro)

### Static Component (Default)

```astro
---
// src/components/landing/Hero.astro
interface Props {
  headline?: string;
  subheadline?: string;
}

const { headline = "Default Headline", subheadline = "Default subheadline" } = Astro.props;
---

<section class="py-20 md:py-32">
  <div class="container mx-auto px-4 flex flex-col items-center text-center gap-6">
    <h1 class="text-4xl md:text-6xl font-bold tracking-tight max-w-3xl">
      {headline}
    </h1>
    <p class="text-lg text-muted-foreground max-w-2xl">
      {subheadline}
    </p>
    <div class="flex flex-col sm:flex-row gap-4">
      <a href="#" class="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
        Primary CTA
      </a>
      <a href="#" class="inline-flex items-center justify-center rounded-md border border-border px-6 py-3 text-sm font-medium hover:bg-accent">
        Secondary CTA
      </a>
    </div>
  </div>
</section>
```

### Conditional Classes

```astro
---
const { isActive = false } = Astro.props;
---

<div class:list={["box", { "bg-primary": isActive }]}>
  Content
</div>
```

## Interactive Islands (React — Only When Needed)

### When to Create an Island

| Pattern | Static (.astro) | Island (.tsx) |
|---------|-----------------|---------------|
| Navigation links | Yes | No |
| Mobile hamburger toggle | Prefer CSS `<details>` | If complex animation needed |
| Accordion/FAQ | Use `<details>` element | If custom animation needed |
| Tabs | Possible with `:target` | Yes, for complex state |
| Carousel | CSS scroll-snap | Yes, for autoplay/controls |
| Form with validation | Basic HTML validation | Yes, for live validation |
| Scroll animations | CSS `@keyframes` + `animation-timeline` | Yes, for complex triggers |

### Island Component Pattern

```tsx
// src/components/landing/MobileMenu.tsx
import { useState } from "react";

interface Props {
  links: { label: string; href: string }[];
}

export default function MobileMenu({ links }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="md:hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
        aria-label="Toggle menu"
      >
        {isOpen ? (
          <svg className="size-6" /* X icon */ />
        ) : (
          <svg className="size-6" /* Menu icon */ />
        )}
      </button>
      {isOpen && (
        <nav className="absolute top-16 left-0 right-0 bg-background border-b p-4">
          <ul className="flex flex-col gap-4">
            {links.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="text-foreground hover:text-primary">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}
```

### Using Islands in Astro Pages

```astro
---
import MobileMenu from "../components/landing/MobileMenu.tsx";
const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
];
---

<!-- client:idle = load JS when browser is idle (good for non-critical interactivity) -->
<MobileMenu client:idle links={navLinks} />

<!-- client:visible = load JS when element enters viewport -->
<Carousel client:visible items={items} />

<!-- client:load = load JS immediately (use sparingly) -->
<SearchForm client:load />
```

## Image Handling

### Optimized Images (from src/)

```astro
---
import { Image } from "astro:assets";
import heroImage from "../images/hero.jpg";
---

<!-- Astro optimizes: format conversion, resizing, srcset -->
<Image src={heroImage} alt="Hero image" class="rounded-lg" />

<!-- With explicit dimensions -->
<Image src={heroImage} alt="Hero" width={800} height={600} />
```

### Static Images (from public/)

```html
<!-- No processing, served as-is -->
<img src="/images/logo.png" alt="Logo" width="120" height="40" />
```

### Remote Images

```astro
---
import { Image } from "astro:assets";
---

<!-- Remote images need explicit width/height -->
<Image src="https://images.unsplash.com/photo-xxx?w=800" alt="Photo" width={800} height={600} />
```

### Unsplash Fallback URLs

```
Hero backgrounds (1920x1080):
https://images.unsplash.com/photo-1557683316-973673baf926?w=1920&h=1080&fit=crop

Feature images (800x600):
https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=600&fit=crop

Avatars (100x100):
https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face
```

## SEO Metadata

Pass metadata via Layout props:

```astro
---
// In page files
import Layout from "../layouts/Layout.astro";
---

<Layout
  title="Page Title | Brand"
  description="Meta description extracted from scrape"
  ogImage="/images/og-image.jpg"
>
  <!-- page content -->
</Layout>
```

For structured data (JSON-LD):

```astro
<!-- In Layout.astro <head> -->
<script type="application/ld+json" set:html={JSON.stringify({
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: title,
  description: description,
})} />
```
