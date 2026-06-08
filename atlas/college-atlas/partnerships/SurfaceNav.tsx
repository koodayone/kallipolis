"use client";

/* ── Surface navigation — dashboard ⇄ report ───────────────────────────────
   Two platonic forms join the family (32×32, stroke 1.8): the dashboard as
   the 2×2 panel grid (the surface IS its grammar), the report as the document
   (the argument). Rendered in the AtlasHeader's right slot on both surfaces;
   the inactive surface is one click away, with the view's selection preserved
   through the shared URL params (resolved at click time — render-time
   window.location reads are hydration-unstable under static export). */

import React from "react";
import { MONO } from "@/college-atlas/partnerships/reportChrome";
import KallipolisBrand from "@/ui/KallipolisBrand";
import { useMeasuredWidth } from "@/college-atlas/partnerships/chartKit";


export const FormDashboard: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <rect x="5" y="5" width="9.5" height="9.5" rx="1.5" /><rect x="17.5" y="5" width="9.5" height="9.5" rx="1.5" />
    <rect x="5" y="17.5" width="9.5" height="9.5" rx="1.5" /><rect x="17.5" y="17.5" width="9.5" height="9.5" rx="1.5" />
  </svg>
);
export const FormReport: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M8 4.5h16v23H8z" /><path d="M12 10.5h8" /><path d="M12 15h8M12 18.5h8M12 22h5" />
  </svg>
);

// The dashboard owns the root AND the far-right anchor (decided 2026-06-07,
// after the responsive re-architecture removed its viewport gate — it now
// renders at every width, so the old "universal surface owns the root"
// asymmetry dissolved). The header bookends: brand on the hard left edge,
// the primary surface on the hard right; the report is the narrated,
// citeable descent at /svamp/report, one click away with selection intact.
const SURFACES = [
  { key: "report" as const, label: "Report", path: "/svamp/report", Icon: FormReport },
  { key: "dashboard" as const, label: "Dashboard", path: "/svamp", Icon: FormDashboard },
];

export default function SurfaceNav({ active, withBrand = false }: { active: "dashboard" | "report"; withBrand?: boolean }) {
  // Container-driven shedding: below ~210px of available width the labels
  // drop and the surface forms carry the nav alone (title/aria keep them
  // named). Stretches into its cell (flex 1 1 auto, content right-aligned)
  // so the measurement reads AVAILABLE width — content-sized measurement
  // would lock the compact form in (it never re-measures wider).
  const { ref, width } = useMeasuredWidth(true);
  const iconOnly = width != null && width < 210;
  return (
    <div ref={ref} style={{ flex: "1 1 auto", minWidth: 0, display: "flex", alignItems: "center", justifyContent: "flex-end", gap: iconOnly ? 18 : 26 }}>
      {SURFACES.map(({ key, label, path, Icon }) => {
        const on = active === key;
        return (
          <a
            key={key}
            href={path}
            title={iconOnly ? label : undefined}
            aria-label={label}
            aria-current={on ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              if (on) return;
              window.location.href = `${path}${window.location.search}`;
            }}
            onMouseEnter={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#e8ecf4"; }}
            onMouseLeave={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#5e6a83"; }}
            style={{ display: "flex", alignItems: "center", gap: 8, color: on ? "#ffffff" : "#5e6a83", textDecoration: "none", cursor: on ? "default" : "pointer", transition: "color .16s", textShadow: on ? "0 0 14px rgba(255,255,255,0.55)" : "none" }}
          >
            <span style={{ width: 19, height: 19, display: "flex", color: "currentColor", filter: on ? "drop-shadow(0 0 6px rgba(255,255,255,0.6))" : "none" }}><Icon /></span>
            {!iconOnly && <span style={{ fontFamily: MONO, fontSize: 10.5, fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase" }}>{label}</span>}
          </a>
        );
      })}
      {withBrand && <span style={{ width: 1, height: 18, background: "rgba(255,255,255,0.09)" }} />}
      {withBrand && <KallipolisBrand />}
    </div>
  );
}
