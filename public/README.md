# public/

Static assets for the landing page (`app/page.tsx`), served by Next.js at the site root.

| File | Consumer | Purpose |
|---|---|---|
| `icon.png` | `app/layout.tsx` | Favicon |
| `kallipolis-logo.png` | Nav, Footer | Brand logo |
| `hero-illustration.jpg` | Vision | Hero section background |
| `desert_modernism.png` | Promise | "The Promise" section background |
| `california.geojson` | CaliforniaMap | State outline for SVG map |

This directory must remain at the project root — Next.js resolves `/filename` to `public/filename` by convention.
