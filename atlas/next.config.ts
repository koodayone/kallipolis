import type { NextConfig } from "next";
import path from "path";

// Static export only when building for Cloudflare Pages deployment.
// During `next dev` (and during local-dev production-parity testing
// without the flag), keep the standard server output — `output: "export"`
// changes how the dev server resolves dynamic routes in ways that can
// break client-only components like the Three.js canvas.
const useStaticExport = process.env.NEXT_STATIC_EXPORT === "true";

const nextConfig: NextConfig = {
  ...(useStaticExport
    ? {
        output: "export" as const,
        // Image optimization requires a server; disabled for static export.
        images: { unoptimized: true },
        // Cloudflare Pages serves directory-style URLs by default.
        trailingSlash: true,
      }
    : {}),

  // Three.js requires client-side only; use dynamic(() => import(...), { ssr: false })

  // Set workspace root to atlas/ so Next.js doesn't pick up the parent lockfile
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
