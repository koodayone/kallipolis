import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Three.js requires client-side only; use dynamic(() => import(...), { ssr: false })
  // Set workspace root to atlas/ so Next.js doesn't pick up the parent lockfile
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
