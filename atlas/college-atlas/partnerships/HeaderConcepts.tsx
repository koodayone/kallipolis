"use client";

/* ── SVAMP Dashboard — header concepts ──────────────────────────────────────
   DESIGN EXPLORATION, not a product surface (sibling of /svamp/concepts).
   Translates the report's header language to the dashboard. Constant across
   every option (the user's vision): the top nav carries the Kallipolis brand
   (left), SILICON VALLEY ADVANCED MANUFACTURING PARTNERSHIP with PREVIEW MODE
   beneath (center), and platonic-form icons for the two surfaces — dashboard
   (the 2×2 panel grid: its own grammar) and report (the document: the
   argument) — as navigation (top right). The fork is how the masthead
   (eyebrow · big title · stats subhead) and the lens tabs compose below.
   Delete with the rest of /svamp/concepts once the design is settled. */

import React from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import KallipolisBrand from "@/ui/KallipolisBrand";

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";
const GOLD = "#c9a84c";
const SUPPLY = "#50c878";
const DEMAND = "#ff5a5a";

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

/* ── New platonic forms: the two surfaces ─────────────────────────────────
   Same geometric family as the lens forms (32×32, stroke 1.8, reduced
   archetypes). Dashboard = the 2×2 panel grid (the surface IS its grammar);
   Report = the document (the argument: title rule + prose lines). */
const FormDashboard: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <rect x="5" y="5" width="9.5" height="9.5" rx="1.5" /><rect x="17.5" y="5" width="9.5" height="9.5" rx="1.5" />
    <rect x="5" y="17.5" width="9.5" height="9.5" rx="1.5" /><rect x="17.5" y="17.5" width="9.5" height="9.5" rx="1.5" />
  </svg>
);
const FormReport: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M8 4.5h16v23H8z" /><path d="M12 10.5h8" /><path d="M12 15h8M12 18.5h8M12 22h5" />
  </svg>
);

/* ── Mock pieces ──────────────────────────────────────────────────────────── */

// Surface switcher — the nav's top-right navigation in every option.
function SurfaceNav({ active }: { active: "dashboard" | "report" }) {
  const items = [
    { key: "dashboard" as const, label: "Dashboard", Icon: FormDashboard },
    { key: "report" as const, label: "Report", Icon: FormReport },
  ];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
      {items.map(({ key, label, Icon }) => {
        const on = active === key;
        return (
          <span key={key} title={label} style={{ display: "flex", alignItems: "center", gap: 7, color: on ? "#e8ecf4" : "#5e6a83", cursor: "pointer" }}>
            <span style={{ width: 17, height: 17, display: "flex", color: on ? GOLD : "#5e6a83" }}><Icon /></span>
            <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase" }}>{label}</span>
          </span>
        );
      })}
      <span style={{ width: 1, height: 18, background: HAIR }} />
      <KallipolisBrand />
    </div>
  );
}

// The report's AtlasHeader, mocked: cube+chevron left, centered title with
// PREVIEW MODE beneath, SurfaceNav right.
function TopNav() {
  return (
    <div style={{ display: "flex", alignItems: "center", height: 64, padding: "0 18px", borderBottom: `1px solid ${HAIR}`, background: "rgba(6,13,31,0.96)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
        <span style={{ width: 22, height: 22, background: hexA(DEMAND, 0.8), borderRadius: 4, transform: "rotate(8deg)" }} />
        <span style={{ color: "#9aa6bd", fontSize: 16 }}>‹</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
        <span style={{ fontFamily: FONT, fontSize: 13.5, fontWeight: 700, letterSpacing: "0.22em", color: "#e8ecf4", whiteSpace: "nowrap" }}>SILICON VALLEY ADVANCED MANUFACTURING PARTNERSHIP</span>
        <span style={{ fontFamily: MONO, fontSize: 8.5, letterSpacing: "0.3em", color: GOLD }}>PREVIEW MODE</span>
      </div>
      <div style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
        <SurfaceNav active="dashboard" />
      </div>
    </div>
  );
}

function Stats() {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 10, fontFamily: FONT, fontSize: 11.5, fontWeight: 600, letterSpacing: "0.1em" }}>
      <span style={{ color: SUPPLY }}>5 MEMBER COLLEGES</span>
      <span style={{ color: "rgba(255,255,255,0.25)" }}>·</span>
      <span style={{ color: "rgba(255,255,255,0.85)" }}>10 PROGRAMS</span>
      <span style={{ color: "rgba(255,255,255,0.25)" }}>·</span>
      <span style={{ color: "rgba(255,255,255,0.85)" }}>12 OCCUPATIONS</span>
      <span style={{ color: "rgba(255,255,255,0.25)" }}>·</span>
      <span style={{ color: SUPPLY }}>BAY AREA</span>
    </div>
  );
}

function MockTabs() {
  const defs = [
    { label: "PROGRAMS", accent: SUPPLY, on: true },
    { label: "OCCUPATIONS", accent: DEMAND, on: false },
    { label: "EMPLOYERS", accent: "#5a9bd4", on: false },
  ];
  return (
    <div style={{ display: "flex", gap: 38, borderBottom: `1px solid ${HAIR}` }}>
      {defs.map((d) => (
        <span key={d.label} style={{ position: "relative", display: "flex", alignItems: "center", gap: 8, padding: "6px 0 12px", fontFamily: MONO, fontSize: 11, letterSpacing: "0.12em", color: d.on ? "#e8ecf4" : "#9aa6bd" }}>
          <span style={{ width: 15, height: 15, color: d.on ? d.accent : "#5e6a83" }}><FormDashboard /></span>
          {d.label}
          {d.on && <span style={{ position: "absolute", left: 0, right: 0, bottom: -1, height: 2, background: d.accent, borderRadius: 2 }} />}
        </span>
      ))}
    </div>
  );
}

function GhostPanels() {
  return (
    <div style={{ display: "flex", gap: 8, padding: "10px 18px 14px" }}>
      {[2, 1].map((f, i) => (
        <div key={i} style={{ flex: f, height: 72, border: `1px dashed ${HAIR}`, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: MONO, fontSize: 9, color: "#5e6a83" }}>
          {i === 0 ? "treemap" : "coverage matrix"}
        </div>
      ))}
    </div>
  );
}

function Frame({ tag, title, badge, children, note }: { tag: string; title: string; badge?: string; children: React.ReactNode; note?: string }) {
  return (
    <div style={{ marginBottom: 36 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
        <span style={{ fontFamily: MONO, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", color: BG, background: badge ? GOLD : "#9aa6bd", borderRadius: 5, padding: "2px 8px" }}>{tag}</span>
        <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.88)" }}>{title}</span>
        {badge && <span style={{ fontFamily: MONO, fontSize: 9, color: GOLD }}>{badge}</span>}
        {note && <span style={{ fontFamily: MONO, fontSize: 9, color: "#5e6a83" }}>{note}</span>}
      </div>
      <div style={{ border: `1px solid ${HAIR}`, borderRadius: 10, background: BG, overflow: "hidden", boxShadow: "0 8px 28px rgba(0,0,0,0.35)" }}>
        {children}
      </div>
    </div>
  );
}

function Caption({ children }: { children: React.ReactNode }) {
  return <p style={{ fontFamily: FONT, fontSize: 12, lineHeight: 1.55, color: "#9aa6bd", margin: "-22px 2px 36px", maxWidth: 680 }}>{children}</p>;
}

/* ── Page ─────────────────────────────────────────────────────────────────── */
export default function HeaderConcepts() {
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, overflowY: "auto", overscrollBehavior: "none", padding: "44px 30px 90px" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.16em", color: "rgba(255,255,255,0.4)" }}>DESIGN EXPLORATION · NOT A PRODUCT SURFACE</div>
        <h1 style={{ fontFamily: FONT, fontSize: 26, fontWeight: 700, color: "#e8ecf4", margin: "8px 0 4px" }}>SVAMP Dashboard — Header Concepts</h1>
        <p style={{ fontFamily: FONT, fontSize: 13.5, lineHeight: 1.6, color: "#9aa6bd", maxWidth: 720, margin: "0 0 34px" }}>
          Constant in every option, per the vision: the top nav carries the Kallipolis brand (left), the consortium
          title with PREVIEW MODE (center), and platonic-form surface navigation (right) — dashboard as the 2×2 panel
          grid (the surface is its grammar), report as the document (the argument). The fork is how the masthead
          (eyebrow · title · stats) and the lens tabs compose beneath it.
        </p>

        <Frame tag="H1" title="Report-faithful masthead, tabs stick on scroll" badge="recommended" note="two frames: landing · scrolled">
          <TopNav />
          <div style={{ padding: "26px 18px 0" }}>
            <div style={{ fontFamily: FONT, fontSize: 12, fontWeight: 700, letterSpacing: "0.18em", color: SUPPLY, marginBottom: 10 }}>PARTNERSHIP LANDSCAPE DASHBOARD</div>
            <div style={{ borderTop: `1px solid ${HAIR}`, paddingTop: 14 }}>
              <div style={{ fontFamily: FONT, fontSize: 26, fontWeight: 700, color: "#e8ecf4", marginBottom: 8 }}>Silicon Valley Advanced Manufacturing Partnership</div>
              <Stats />
            </div>
            <div style={{ marginTop: 18 }}><MockTabs /></div>
          </div>
          <GhostPanels />
        </Frame>
        <Frame tag="H1·scrolled" title="… after scroll: masthead gone, nav + tab rail pinned">
          <TopNav />
          <div style={{ padding: "0 18px", background: "rgba(6,13,31,0.96)" }}><MockTabs /></div>
          <GhostPanels />
        </Frame>
        <Caption>
          The report’s masthead, verbatim — eyebrow recolored for the surface (“PARTNERSHIP LANDSCAPE DASHBOARD”),
          hairline, full-size title, stats subhead — then the lens tabs. On scroll the masthead departs and the tab
          rail pins under the nav, exactly the report’s sticky-banner behavior. Landing reads like the report’s
          cover (what a projector shows when the page opens); working state is dense.
        </Caption>

        <Frame tag="H2" title="Compressed masthead — title and stats share a line, all sticky">
          <TopNav />
          <div style={{ padding: "14px 18px 0", background: "rgba(6,13,31,0.96)" }}>
            <div style={{ fontFamily: FONT, fontSize: 10.5, fontWeight: 700, letterSpacing: "0.18em", color: SUPPLY, marginBottom: 5 }}>PARTNERSHIP LANDSCAPE DASHBOARD</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 18, marginBottom: 12 }}>
              <span style={{ fontFamily: FONT, fontSize: 18, fontWeight: 700, color: "#e8ecf4", whiteSpace: "nowrap" }}>Silicon Valley Advanced Manufacturing Partnership</span>
              <span style={{ marginLeft: "auto" }}><Stats /></span>
            </div>
            <MockTabs />
          </div>
          <GhostPanels />
        </Frame>
        <Caption>
          Everything survives but compressed: smaller title with the stats right-aligned on its baseline, tabs
          beneath, and the whole band sticks — identity never leaves the screen. Costs ~90px of permanent chrome and
          the title competes with the nav’s uppercase title directly above it.
        </Caption>

        <Frame tag="H3" title="Unified rail — masthead block left, tabs right, one sticky band">
          <TopNav />
          <div style={{ display: "flex", alignItems: "flex-end", gap: 28, padding: "12px 18px 0", background: "rgba(6,13,31,0.96)", borderBottom: `1px solid ${HAIR}` }}>
            <div style={{ paddingBottom: 10 }}>
              <div style={{ fontFamily: FONT, fontSize: 10, fontWeight: 700, letterSpacing: "0.16em", color: SUPPLY, marginBottom: 3 }}>PARTNERSHIP LANDSCAPE DASHBOARD</div>
              <div style={{ fontFamily: FONT, fontSize: 15, fontWeight: 700, color: "#e8ecf4", marginBottom: 4 }}>Silicon Valley Advanced Manufacturing Partnership</div>
              <Stats />
            </div>
            <div style={{ marginLeft: "auto" }}><MockTabs /></div>
          </div>
          <GhostPanels />
        </Frame>
        <Caption>
          Maximum density: one band holds the whole masthead (left, small) and the tabs (right, on the shared rail).
          Most screen for panels at all times — but the title shrinks to chrome, the stats crowd, and on narrower
          desktop widths the band wraps awkwardly. The instrument wins; the identity loses.
        </Caption>

        <div style={{ border: `1px solid ${hexA(GOLD, 0.35)}`, borderRadius: 10, background: hexA(GOLD, 0.04), padding: "14px 18px", maxWidth: 720 }}>
          <div style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.14em", color: GOLD, marginBottom: 8 }}>RECOMMENDED PATH</div>
          <p style={{ fontFamily: FONT, fontSize: 12.5, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
            H1. The masthead is the dashboard’s cover — at a consortium convening, the landing view is the title
            slide, and the report-faithful masthead carries that identity at full size. After scroll it gets out of
            the way and H1 becomes as dense as H3 (nav + tab rail only) — the report’s own sticky-banner pattern,
            already familiar to anyone who has read it. The surface icons (2×2 grid · document) ride the nav in every
            option and make dashboard ⇄ report one click each way, selection preserved through the shared URL params.
          </p>
        </div>
      </div>
    </div>
  );
}
