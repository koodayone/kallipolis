import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "atlas-bg": "#060d1f",
        "atlas-gold": "#c9a84c",
        "atlas-gold-dim": "#8a6e2e",
        surface: "#f8f7f4",
        "surface-border": "#e4e2dc",
        "text-primary": "#111827",
        "text-secondary": "#6b7280",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
