# Component Patterns

Reference patterns for common landing page components in Astro. Use as starting points, adapt to match scraped design.

## Header/Navigation

```astro
---
// src/components/landing/Header.astro
// Static header — mobile menu uses CSS-only <details> pattern
---

<header class="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
  <div class="container mx-auto flex h-16 items-center justify-between px-4">
    <a href="/" class="flex items-center gap-2">
      <img src="/images/logo.svg" alt="Brand" width="32" height="32" />
      <span class="font-semibold">Brand</span>
    </a>

    <!-- Desktop nav -->
    <nav class="hidden md:flex items-center gap-6">
      <a href="#features" class="text-sm text-muted-foreground hover:text-foreground">Features</a>
      <a href="#pricing" class="text-sm text-muted-foreground hover:text-foreground">Pricing</a>
      <a href="#" class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
        Get Started
      </a>
    </nav>

    <!-- Mobile hamburger (CSS-only via <details>) -->
    <details class="md:hidden relative">
      <summary class="list-none p-2 cursor-pointer" aria-label="Toggle menu">
        <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </summary>
      <nav class="absolute right-0 top-full mt-2 w-48 rounded-md border border-border bg-background p-4 shadow-lg">
        <ul class="flex flex-col gap-3">
          <li><a href="#features" class="text-sm">Features</a></li>
          <li><a href="#pricing" class="text-sm">Pricing</a></li>
          <li><a href="#" class="text-sm font-medium text-primary">Get Started</a></li>
        </ul>
      </nav>
    </details>
  </div>
</header>

<style>
  /* Hide default marker */
  details summary::-webkit-details-marker { display: none; }
  /* Close on click outside (optional enhancement) */
  details[open] summary::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
  }
</style>
```

### Interactive Mobile Menu (Island — Use Only If Complex Animation Needed)

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
      <button onClick={() => setIsOpen(!isOpen)} className="p-2" aria-label="Toggle menu">
        {isOpen ? (
          <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>
      {isOpen && (
        <nav className="absolute right-0 top-full mt-2 w-48 rounded-md border bg-white p-4 shadow-lg">
          <ul className="flex flex-col gap-3">
            {links.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="text-sm hover:text-primary">{link.label}</a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}
```

Usage in .astro:
```astro
<MobileMenu client:idle links={[{ label: "Features", href: "#features" }]} />
```

## Hero Variants

### Centered Hero

```astro
---
// src/components/landing/Hero.astro
---

<section class="py-20 md:py-32">
  <div class="container mx-auto flex flex-col items-center text-center gap-6 px-4">
    <span class="inline-flex items-center rounded-full border border-border px-3 py-1 text-xs font-medium">
      New Feature
    </span>
    <h1 class="text-4xl md:text-6xl font-bold tracking-tight max-w-3xl">
      Headline goes here
    </h1>
    <p class="text-lg text-muted-foreground max-w-2xl">
      Subheadline description text
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

### Split Hero (Image + Content)

```astro
---
import { Image } from "astro:assets";
import heroImage from "../../images/hero.jpg";
---

<section class="py-20">
  <div class="container mx-auto grid lg:grid-cols-2 gap-12 items-center px-4">
    <div class="flex flex-col gap-6">
      <h1 class="text-4xl md:text-5xl font-bold tracking-tight">
        Headline
      </h1>
      <p class="text-lg text-muted-foreground">Description</p>
      <div class="flex gap-4">
        <a href="#" class="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          CTA
        </a>
      </div>
    </div>
    <div class="relative aspect-video lg:aspect-square overflow-hidden rounded-lg">
      <Image src={heroImage} alt="Hero" class="object-cover w-full h-full" />
    </div>
  </div>
</section>
```

## Features

### 3-Column Grid

```astro
---
const features = [
  { icon: "zap", title: "Fast", description: "Lightning quick performance." },
  { icon: "shield", title: "Secure", description: "Enterprise-grade security." },
  { icon: "sparkles", title: "Modern", description: "Built with latest tech." },
];

const icons: Record<string, string> = {
  zap: "M13 2L3 14h9l-1 10 10-12h-9l1-10z",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  sparkles: "M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8L12 2z",
};
---

<section class="py-20 bg-muted/50">
  <div class="container mx-auto px-4">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-bold">Features</h2>
      <p class="text-muted-foreground mt-2">Why choose us</p>
    </div>
    <div class="grid md:grid-cols-3 gap-8">
      {features.map((feature) => (
        <div class="rounded-lg border border-border bg-background p-6">
          <svg class="size-10 text-primary mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d={icons[feature.icon]} />
          </svg>
          <h3 class="font-semibold text-lg mb-2">{feature.title}</h3>
          <p class="text-muted-foreground">{feature.description}</p>
        </div>
      ))}
    </div>
  </div>
</section>
```

### Bento Grid

```astro
<section class="py-20">
  <div class="container mx-auto px-4">
    <div class="grid md:grid-cols-3 gap-4">
      <div class="md:col-span-2 md:row-span-2 rounded-lg border border-border bg-background p-8">
        <!-- Large feature -->
      </div>
      <div class="rounded-lg border border-border bg-background p-6">
        <!-- Small feature 1 -->
      </div>
      <div class="rounded-lg border border-border bg-background p-6">
        <!-- Small feature 2 -->
      </div>
    </div>
  </div>
</section>
```

## Testimonials

```astro
---
const testimonials = [
  { name: "John Doe", role: "CEO at Acme", content: "This product transformed our workflow.", avatar: "/images/avatar-1.jpg" },
  { name: "Jane Smith", role: "CTO at Corp", content: "Incredible performance gains.", avatar: "/images/avatar-2.jpg" },
  { name: "Bob Wilson", role: "Lead Dev", content: "Best tool we've ever used.", avatar: "/images/avatar-3.jpg" },
];
---

<section class="py-20">
  <div class="container mx-auto px-4">
    <h2 class="text-3xl font-bold text-center mb-12">What people say</h2>
    <div class="grid md:grid-cols-3 gap-6">
      {testimonials.map((t) => (
        <div class="rounded-lg border border-border bg-background p-6">
          <p class="text-muted-foreground mb-4">"{t.content}"</p>
          <div class="flex items-center gap-3">
            <img src={t.avatar} alt={t.name} width="40" height="40" class="rounded-full object-cover" />
            <div>
              <p class="font-medium text-sm">{t.name}</p>
              <p class="text-xs text-muted-foreground">{t.role}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
</section>
```

## Pricing

```astro
---
const plans = [
  { name: "Free", price: "$0", features: ["Feature 1", "Feature 2"], popular: false },
  { name: "Pro", price: "$29", features: ["Everything in Free", "Feature 3", "Feature 4"], popular: true },
  { name: "Enterprise", price: "Custom", features: ["Everything in Pro", "Feature 5", "Feature 6"], popular: false },
];
---

<section class="py-20">
  <div class="container mx-auto px-4">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-bold">Pricing</h2>
    </div>
    <div class="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
      {plans.map((plan) => (
        <div class:list={[
          "rounded-lg border bg-background p-6 flex flex-col",
          plan.popular ? "border-primary shadow-lg" : "border-border"
        ]}>
          {plan.popular && (
            <span class="inline-flex self-start items-center rounded-full bg-primary/10 text-primary px-3 py-1 text-xs font-medium mb-4">
              Popular
            </span>
          )}
          <h3 class="text-xl font-semibold">{plan.name}</h3>
          <div class="text-3xl font-bold mt-2">
            {plan.price}<span class="text-sm font-normal text-muted-foreground">/mo</span>
          </div>
          <ul class="mt-6 space-y-3 flex-1">
            {plan.features.map((f) => (
              <li class="flex items-center gap-2 text-sm">
                <svg class="size-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {f}
              </li>
            ))}
          </ul>
          <a
            href="#"
            class:list={[
              "mt-6 inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium",
              plan.popular
                ? "bg-primary text-primary-foreground hover:bg-primary/90"
                : "border border-border hover:bg-accent"
            ]}
          >
            {plan.popular ? "Get Started" : "Choose Plan"}
          </a>
        </div>
      ))}
    </div>
  </div>
</section>
```

## FAQ (CSS-Only Accordion)

```astro
---
const faqs = [
  { question: "What is this product?", answer: "A brief explanation of the product." },
  { question: "How does pricing work?", answer: "Details about pricing structure." },
  { question: "Is there a free trial?", answer: "Yes, we offer a 14-day free trial." },
];
---

<section class="py-20">
  <div class="container mx-auto px-4 max-w-3xl">
    <h2 class="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
    <div class="space-y-4">
      {faqs.map((faq) => (
        <details class="group rounded-lg border border-border p-4">
          <summary class="flex cursor-pointer items-center justify-between font-medium list-none">
            {faq.question}
            <svg class="size-5 text-muted-foreground transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <p class="mt-3 text-muted-foreground">{faq.answer}</p>
        </details>
      ))}
    </div>
  </div>
</section>
```

## CTA Section

```astro
<section class="py-20 bg-primary text-primary-foreground">
  <div class="container mx-auto px-4 text-center">
    <h2 class="text-3xl font-bold mb-4">Ready to get started?</h2>
    <p class="text-primary-foreground/80 mb-8 max-w-xl mx-auto">
      Join thousands of users already using our platform.
    </p>
    <div class="flex flex-col sm:flex-row gap-4 justify-center">
      <a href="#" class="inline-flex items-center justify-center rounded-md bg-background text-foreground px-6 py-3 text-sm font-medium hover:bg-background/90">
        Get Started Free
      </a>
      <a href="#" class="inline-flex items-center justify-center rounded-md border border-primary-foreground/20 px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary-foreground/10">
        Contact Sales
      </a>
    </div>
  </div>
</section>
```

## Footer

```astro
---
const footerLinks = {
  Product: ["Features", "Pricing", "Changelog"],
  Company: ["About", "Blog", "Careers"],
  Legal: ["Privacy", "Terms"],
};
---

<footer class="border-t border-border py-12">
  <div class="container mx-auto px-4">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
      <div>
        <img src="/images/logo.svg" alt="Brand" width="32" height="32" class="mb-4" />
        <p class="text-sm text-muted-foreground">
          Brief company description.
        </p>
      </div>
      {Object.entries(footerLinks).map(([category, links]) => (
        <div>
          <h4 class="font-medium mb-4">{category}</h4>
          <ul class="space-y-2">
            {links.map((link) => (
              <li>
                <a href="#" class="text-sm text-muted-foreground hover:text-foreground">{link}</a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
    <div class="border-t border-border mt-12 pt-8 text-center text-sm text-muted-foreground">
      &copy; {new Date().getFullYear()} Company. All rights reserved.
    </div>
  </div>
</footer>
```
