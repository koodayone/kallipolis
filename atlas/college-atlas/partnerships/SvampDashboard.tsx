"use client";

/* ── SVAMP Dashboard — the report transposed ────────────────────────────────
   Same visual vocabulary as the report (treemaps, coverage matrices, trend
   charts, the gold demand line), spatial simultaneity instead of narrative
   sequence. Report = argument (citeable, prose, scrolling); dashboard =
   instrument (at-a-glance, projectable). Prose dies here; its integrity
   obligations live in chrome — every DashPanel names its institutional
   authority.

   V1 requirements (decided 2026-06-06; design record at /svamp/concepts):
   1. One lens at a time via tabs. Programs and Occupations share the
      dashboard grammar (aggregates on top, single-scope band below);
      Employers is its own state — no selection crosses the lens boundary.
   2. Detail band = tiled single-scope grid. Treemap rect / matrix row ⇒
      consortium scope; matrix cell ⇒ that college's scope (decompositions
      live there).
   3. Strict 100vh fit, no scroll. ≥1440px target; smaller screens get a
      gate card routing to the report, which remains the scrolling surface.
   4. Employers = standalone full-bleed map at State-Atlas parity.

   URL anchoring reuses svampUrl verbatim (route-agnostic; same lens/top/
   soc/college vocabulary as the report), so dashboard views are shareable
   and the analytics record is the URL — and a view can hop between
   /svamp and /svamp/dashboard with its selection intact. */

import React, { useEffect, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";

type DashLens = "programs" | "occupations" | "employers";
const LENSES: DashLens[] = ["programs", "occupations", "employers"];
// Mirrors the report's lens accents (module-internal to SvampView).
const LENS_ACCENT: Record<DashLens, string> = {
  programs: "#50c878",
  occupations: "#ff5a5a",
  employers: "#5a9bd4",
};
const LENS_LABEL: Record<DashLens, string> = {
  programs: "Programs",
  occupations: "Occupations",
  employers: "Employers",
};

/* ── Panel chrome — the dashboard's signature element ─────────────────────
   Every panel header carries its authority chip (· DataMart, · COE, · EDD):
   the report's prose attributions, transposed into chrome. */
export function DashPanel({ title, authority, accent, children, grow = 1 }: {
  title: string;
  authority: string;
  accent: string;
  children: React.ReactNode;
  grow?: number;
}) {
  return (
    <div style={{ flex: grow, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", border: `1px solid ${HAIR}`, borderRadius: 10, background: "rgba(255,255,255,0.022)", overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)", flex: "none" }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: accent, flex: "none" }} />
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, letterSpacing: "0.04em", color: "rgba(255,255,255,0.88)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</span>
        <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 9.5, color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap", flex: "none" }}>· {authority}</span>
      </div>
      <div style={{ flex: 1, minHeight: 0, padding: 10, display: "flex", flexDirection: "column" }}>{children}</div>
    </div>
  );
}

/* ── Small-screen gate ──────────────────────────────────────────────────────
   Strict fit targets ≥1440px (projection, large monitors). Below that, the
   report is the better surface — route there with the selection intact. */
function useWideViewport(): boolean | null {
  const [wide, setWide] = useState<boolean | null>(null);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1440px)");
    const update = () => setWide(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return wide;
}

function NarrowGate() {
  // Preserve the view params across the hop — the report speaks the same URL
  // vocabulary, so the selection survives. (Safe to read render-time here:
  // the gate only renders post-mount, after the matchMedia effect.)
  const qs = typeof window === "undefined" ? "" : window.location.search;
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ maxWidth: 420, border: `1px solid ${HAIR}`, borderRadius: 12, padding: "26px 28px", background: "rgba(255,255,255,0.02)" }}>
        <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", color: "rgba(255,255,255,0.4)", marginBottom: 10 }}>SVAMP · DASHBOARD</div>
        <div style={{ fontFamily: FONT, fontSize: 16, fontWeight: 650, color: "#e8ecf4", marginBottom: 8 }}>This dashboard needs a wider screen.</div>
        <p style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.6, color: "#9aa6bd", margin: "0 0 18px" }}>
          It holds a strict one-viewport fit for screens 1440px and up. On this screen, the report carries the same
          data — with the full narrative.
        </p>
        <a href={`/svamp${qs}`} style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "#e8ecf4", textDecoration: "none", border: `1px solid ${HAIR}`, borderRadius: 8, padding: "8px 14px", display: "inline-block" }}>
          Open the report →
        </a>
      </div>
    </div>
  );
}

/* ── Placeholder lens bodies — filled by Phases 3 (Programs), 4
   (Occupations), 5 (Employers). Each names its decided composition so the
   shell is reviewable on its own. ── */
function LensPlaceholder({ lens }: { lens: DashLens }) {
  const accent = LENS_ACCENT[lens];
  const detail: Record<DashLens, string> = {
    programs: "supply treemap + coverage matrix · single-scope band (awards vs demand · enrollments · wages · occupations served)",
    occupations: "demand treemap + coverage matrix · single-scope band (awards vs demand · enrollments · feeding programs)",
    employers: "full-bleed regional employer map · State-Atlas parity · shown/total",
  };
  const phase: Record<DashLens, string> = { programs: "PHASE 3", occupations: "PHASE 4", employers: "PHASE 5" };
  return (
    <div style={{ flex: 1, minHeight: 0, border: `1px dashed ${HAIR}`, borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
      <span style={{ fontFamily: MONO, fontSize: 11, letterSpacing: "0.16em", color: accent }}>{LENS_LABEL[lens].toUpperCase()} LENS · {phase[lens]}</span>
      <span style={{ fontFamily: FONT, fontSize: 12.5, color: "#9aa6bd", maxWidth: 560, textAlign: "center", lineHeight: 1.6 }}>{detail[lens]}</span>
    </div>
  );
}

/* ── Shell ────────────────────────────────────────────────────────────────── */
export default function SvampDashboard() {
  const [lens, setLens] = useState<DashLens>("programs");
  const wide = useWideViewport();

  // Adopt the URL's lens after mount (post-hydration, mirroring the report's
  // static-export-safe pattern — no reactive useSearchParams).
  useEffect(() => {
    const p = readSvampParams();
    if (p.lens === "occupations" || p.lens === "employers") setLens(p.lens);
  }, []);

  const switchLens = (l: DashLens) => {
    setLens(l);
    // Absent lens param ⇒ programs default (the report's convention); clear
    // every cross-lens selection key on any switch.
    writeSvampParams({ lens: l === "programs" ? null : l, soc: null, top: null, college: null, emp: null });
  };

  if (wide === false) return <NarrowGate />;

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, display: "grid", gridTemplateRows: "auto 1fr", gap: 10, padding: "12px 16px 16px", overflow: "hidden" }}>
      {/* Top bar: identity · lens tabs · the road back to the argument. */}
      <div style={{ display: "flex", alignItems: "center", gap: 22, borderBottom: `1px solid ${HAIR}`, paddingBottom: 10 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 700, letterSpacing: "0.14em", color: "#e8ecf4", whiteSpace: "nowrap" }}>SVAMP</span>
          <span style={{ fontFamily: MONO, fontSize: 8.5, letterSpacing: "0.18em", color: "rgba(255,255,255,0.4)" }}>DASHBOARD</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {LENSES.map((l) => {
            const on = lens === l;
            return (
              <button
                key={l}
                onClick={() => switchLens(l)}
                style={{ appearance: "none", border: `1px solid ${on ? "rgba(255,255,255,0.18)" : HAIR}`, cursor: "pointer", background: on ? "rgba(255,255,255,0.1)" : "transparent", color: on ? "#e8ecf4" : "#9aa6bd", fontFamily: FONT, fontSize: 12.5, fontWeight: 600, padding: "6px 16px", borderRadius: 8, transition: "background .12s, color .12s" }}
              >
                {LENS_LABEL[l]}
              </button>
            );
          })}
        </div>
        {/* Query resolved at click time — render-time window.location reads
            are hydration-unstable under static export (server HTML wins). */}
        <a
          href="/svamp"
          onClick={(e) => { e.preventDefault(); window.location.href = `/svamp${window.location.search}`; }}
          style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 10.5, color: "rgba(255,255,255,0.5)", textDecoration: "none", whiteSpace: "nowrap" }}
        >
          view report →
        </a>
      </div>

      {/* Lens body — Programs and Occupations share the dashboard grammar;
          Employers is its own state. */}
      <div style={{ minHeight: 0, display: "flex", flexDirection: "column" }}>
        <LensPlaceholder lens={lens} />
      </div>
    </div>
  );
}
