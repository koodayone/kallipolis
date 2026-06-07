"use client";

import React from "react";
import { MONO } from "@/college-atlas/partnerships/reportChrome";

// Lens accents (mirror SvampView's module constants — programs green,
// occupations red, employers blue).
const PROGRAM_ACCENT = "#50c878";
const EMPLOYER_ACCENT = "#5a9bd4";

// ── Lens navigation ────────────────────────────────────────────────────────
// Three Platonic forms of the partnership landscape: the worker (occupations ·
// hard hat), the curriculum (programs · book), the firm (employers · skyscraper).
// One geometric family of reduced archetypes; the per-lens accent doubles as
// wayfinding once the Programs/Employers views ship. Eyebrow-tab treatment —
// active underline echoes the coverage grid's selected-column underline.
type Lens = "occupations" | "programs" | "employers";
const FormHardHat: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M6 18a10 10 0 0 1 20 0" /><path d="M11.4 18C11.4 12.4 13 9.4 16 8" /><path d="M20.6 18C20.6 12.4 19 9.4 16 8" /><path d="M3 18h26" /><path d="M5.4 18c2.4 3.1 18.8 3.1 21.2 0" />
  </svg>
);
const FormBook: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M16 9.6C12.4 7.8 7.6 8.1 4.6 9.6V22.6C7.6 21.1 12.4 20.8 16 22.6" /><path d="M16 9.6C19.6 7.8 24.4 8.1 27.4 9.6V22.6C24.4 21.1 19.6 20.8 16 22.6" /><path d="M16 9.6V22.6" />
  </svg>
);
const FormTower: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M10.5 28V11h11v17" /><path d="M13.6 11V6h4.8v5" /><path d="M16 6V3" /><path d="M13.2 15.5h5.6M13.2 19.5h5.6M13.2 23.5h5.6" /><path d="M7.5 28h17" />
  </svg>
);
// Programs first — workforce practitioners own and act on programs (supply is
// their lever; SWP funds programs), and it matches the institution-primary atlas.
// Occupations (regional demand) follows as the justification; employers, the map.
const LENS_DEFS: { key: Lens; label: string; accent: string; Icon: React.FC }[] = [
  { key: "programs", label: "Programs", accent: PROGRAM_ACCENT, Icon: FormBook },
  { key: "occupations", label: "Occupations", accent: "#ff5a5a", Icon: FormHardHat },
  { key: "employers", label: "Employers", accent: EMPLOYER_ACCENT, Icon: FormTower },
];
function LensTabs({ lens, setLens, activeAccent }: {
  lens: Lens;
  setLens: (l: Lens) => void;
  // Overrides the ACTIVE tab's accent (icon + underline) — the dashboard
  // passes the selected college's brand in college scope, so the whole
  // instrument wears the scope color. Inactive tabs keep lens identity.
  activeAccent?: string;
}) {
  return (
    <div style={{ display: "flex", gap: 38, borderBottom: "1px solid rgba(255,255,255,.08)", marginBottom: 4 }}>
      {LENS_DEFS.map(({ key, label, accent: lensAccent, Icon }) => {
        const on = lens === key;
        const accent = on && activeAccent ? activeAccent : lensAccent;
        return (
          <button
            key={key}
            onClick={() => setLens(key)}
            onMouseEnter={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#e8ecf4"; }}
            onMouseLeave={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#9aa6bd"; }}
            style={{ display: "flex", alignItems: "center", gap: 9, border: 0, background: "transparent", cursor: "pointer", padding: "6px 0 13px", color: on ? "#e8ecf4" : "#9aa6bd", fontFamily: MONO, fontSize: 11.5, fontWeight: 500, letterSpacing: ".12em", textTransform: "uppercase", position: "relative", transition: "color .16s" }}
          >
            <span style={{ width: 17, height: 17, display: "flex", color: on ? accent : "#5e6a83", transition: "color .16s" }}><Icon /></span>
            {label}
            {on && <span style={{ position: "absolute", left: 0, right: 0, bottom: -1, height: 2, background: accent, borderRadius: 2 }} />}
          </button>
        );
      })}
    </div>
  );
}
export default LensTabs;
export type { Lens };
// Lens → accent, for surfaces whose chrome follows the active lens (the
// report's and dashboard's masthead eyebrows).
export const LENS_ACCENTS: Record<Lens, string> = Object.fromEntries(
  LENS_DEFS.map((d) => [d.key, d.accent]),
) as Record<Lens, string>;
