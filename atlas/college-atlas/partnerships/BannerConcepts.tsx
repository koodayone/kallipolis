"use client";

/* ── SVAMP Dashboard — scope banner concepts ────────────────────────────────
   DESIGN EXPLORATION, not a product surface (sibling of /svamp/concepts).
   The scope banner is the dashboard's "you are here": it names the entity the
   scope bands are about and pins under the lens rail on scroll. The current
   build (chip + "← consortium" button) reads as UI furniture; these options
   transpose the REPORT's context banner — scope smallcaps · name · code on a
   46px translucent row — and differ on two axes:
     1. the exit affordance for college scope (the button's replacement), and
     2. vertical presence (how much bigger "a bit bigger" should be).
   Every option is shown in BOTH states — consortium and college scope —
   because the exit affordance is the fork. Delete with /svamp/concepts once
   the banner is settled. */

import React, { useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";
const GOLD = "#c9a84c";
const SUPPLY = "#50c878";

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

// The real derived De Anza accent, so color judgment is made on the actual hue.
const DEANZA = getCollegeAtlasConfig("deanza")?.brandColorLight ?? "#e25c87";

/* ── Page scaffolding (matches the sibling concept pages' idiom) ─────────── */
function OptionHeading({ n, title, question }: { n: number; title: string; question: string }) {
  return (
    <div style={{ margin: "54px 0 6px" }}>
      <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: "0.16em", color: GOLD, marginBottom: 6 }}>OPTION B{n}</div>
      <div style={{ fontFamily: FONT, fontSize: 19, fontWeight: 650, color: "#e8ecf4" }}>{title}</div>
      <div style={{ fontFamily: FONT, fontSize: 13, color: "#9aa6bd", marginTop: 3 }}>{question}</div>
    </div>
  );
}
function Chip({ children, color = "#9aa6bd" }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.06em", color, border: `1px solid ${hexA(color.startsWith("#") ? color : "#9aa6bd", 0.35)}`, borderRadius: 6, padding: "3px 9px", whiteSpace: "nowrap" }}>
      {children}
    </span>
  );
}
function Caption({ children }: { children: React.ReactNode }) {
  return <p style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.65, color: "#9aa6bd", maxWidth: 880, margin: "12px 0 0" }}>{children}</p>;
}
function StateTag({ children }: { children: React.ReactNode }) {
  return <div style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.14em", color: "#5e6a83", margin: "16px 0 6px" }}>{children}</div>;
}

/* ── In-situ frame: a sliver of panel bottoms above, a panel header below,
   so each banner reads at dashboard proportions, pinned mid-scroll. ──────── */
function MockFrame({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ border: `1px solid ${HAIR}`, borderRadius: 10, overflow: "hidden", background: BG }}>
      {/* content scrolling away beneath the pinned banner */}
      <div style={{ display: "flex", gap: 8, padding: "0 14px", opacity: 0.5 }}>
        <div style={{ flex: 2, height: 26, borderLeft: `1px solid ${HAIR}`, borderRight: `1px solid ${HAIR}`, borderBottom: `1px solid ${HAIR}`, borderRadius: "0 0 10px 10px" }} />
        <div style={{ flex: 1, height: 26, borderLeft: `1px solid ${HAIR}`, borderRight: `1px solid ${HAIR}`, borderBottom: `1px solid ${HAIR}`, borderRadius: "0 0 10px 10px" }} />
      </div>
      {children}
      {/* first scope panel under the banner */}
      <div style={{ display: "flex", gap: 8, padding: "8px 14px 14px", opacity: 0.85 }}>
        {["Awards", "Enrollments"].map((t) => (
          <div key={t} style={{ flex: 1, border: `1px solid ${HAIR}`, borderRadius: 10, background: "rgba(255,255,255,0.022)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
              <span style={{ width: 3, height: 12, borderRadius: 2, background: SUPPLY }} />
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.88)" }}>{t}</span>
              <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 9.5, color: "rgba(255,255,255,0.4)" }}>· DataMart</span>
            </div>
            <div style={{ height: 34 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Shared banner row chrome — the report's surface, full-bleed ─────────── */
function BannerRow({ height, children }: { height: number; children: React.ReactNode }) {
  return (
    <div style={{ height, background: "rgba(9,17,38,0.96)", borderTop: `1px solid ${HAIR}`, borderBottom: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", padding: "0 16px" }}>
      {children}
    </div>
  );
}

/* ── Breadcrumb scope — the path is the exit. CONSORTIUM dims to ancestry in
   college scope and brightens on hover (live here, to judge the feel). ───── */
function Crumb({ label, color, dim = false, onHoverable = true }: { label: string; color: string; dim?: boolean; onHoverable?: boolean }) {
  const [hot, setHot] = useState(false);
  return (
    <span
      onMouseEnter={() => onHoverable && setHot(true)}
      onMouseLeave={() => setHot(false)}
      style={{
        fontFamily: FONT, fontSize: 11.5, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase",
        color: dim ? (hot ? "rgba(255,255,255,0.85)" : "rgba(255,255,255,0.42)") : color,
        cursor: dim ? "pointer" : "default", whiteSpace: "nowrap", transition: "color .15s",
        borderBottom: dim && hot ? "1px solid rgba(255,255,255,0.4)" : "1px solid transparent",
      }}
    >
      {label}
    </span>
  );
}
const CrumbSep = () => <span style={{ color: "rgba(255,255,255,0.22)", fontFamily: MONO, fontSize: 11, padding: "0 2px" }}>›</span>;
const DotSep = () => <span style={{ color: "rgba(255,255,255,0.2)" }}>·</span>;

/* ════════════════════════════════════════════════════════════════════════ */
export default function BannerConcepts() {
  // The two evaluation states, with the user's own examples.
  const consortium = { name: "Manufacturing and Industrial Technology", code: "TOP 095600" };
  const college = { name: "Digital Fabrication Technician", code: "TOP 095690" };

  /* B1 — the report's banner verbatim, display-only. */
  const b1 = (scoped: boolean) => (
    <BannerRow height={46}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, minWidth: 0, width: "100%" }}>
        <Crumb label={scoped ? "De Anza" : "Consortium"} color={scoped ? DEANZA : SUPPLY} onHoverable={false} />
        <DotSep />
        <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.9)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {scoped ? college.name : consortium.name}
        </span>
        <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.05em", color: hexA(scoped ? DEANZA : SUPPLY, 0.65), whiteSpace: "nowrap" }}>
          {scoped ? college.code : consortium.code}
        </span>
      </div>
    </BannerRow>
  );

  /* B2 — breadcrumb scope: the path is the exit. */
  const b2 = (scoped: boolean) => (
    <BannerRow height={52}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, minWidth: 0, width: "100%" }}>
        {scoped ? (
          <span style={{ display: "inline-flex", alignItems: "baseline", gap: 7, flex: "none" }}>
            <Crumb label="Consortium" color={SUPPLY} dim />
            <CrumbSep />
            <Crumb label="De Anza" color={DEANZA} onHoverable={false} />
          </span>
        ) : (
          <Crumb label="Consortium" color={SUPPLY} onHoverable={false} />
        )}
        <DotSep />
        <span style={{ fontFamily: FONT, fontSize: 14.5, fontWeight: 600, color: "rgba(255,255,255,0.92)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {scoped ? college.name : consortium.name}
        </span>
        <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.05em", color: hexA(scoped ? DEANZA : SUPPLY, 0.65), whiteSpace: "nowrap" }}>
          {scoped ? college.code : consortium.code}
        </span>
      </div>
    </BannerRow>
  );

  /* B3 — masthead two-liner: eyebrow path above, title row below. */
  const b3 = (scoped: boolean) => (
    <div style={{ background: "rgba(9,17,38,0.96)", borderTop: `1px solid ${HAIR}`, borderBottom: "1px solid rgba(255,255,255,0.07)", padding: "9px 16px 11px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 7, marginBottom: 3 }}>
        {scoped ? (
          <>
            <Crumb label="Consortium" color={SUPPLY} dim />
            <CrumbSep />
            <Crumb label="De Anza" color={DEANZA} onHoverable={false} />
          </>
        ) : (
          <Crumb label="Consortium" color={SUPPLY} onHoverable={false} />
        )}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, minWidth: 0 }}>
        <span style={{ fontFamily: FONT, fontSize: 17, fontWeight: 650, color: "#e8ecf4", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {scoped ? college.name : consortium.name}
        </span>
        <span style={{ fontFamily: MONO, fontSize: 11.5, fontWeight: 500, letterSpacing: "0.05em", color: hexA(scoped ? DEANZA : SUPPLY, 0.65), whiteSpace: "nowrap" }}>
          {scoped ? college.code : consortium.code}
        </span>
      </div>
    </div>
  );

  const option = (mock: (s: boolean) => React.ReactNode) => (
    <>
      <StateTag>STATE · CONSORTIUM SCOPE</StateTag>
      <MockFrame>{mock(false)}</MockFrame>
      <StateTag>STATE · COLLEGE SCOPE (DE ANZA)</StateTag>
      <MockFrame>{mock(true)}</MockFrame>
    </>
  );

  return (
    // Fixed scroll container — globals.css locks body overflow for the atlas
    // scenes, so every page owns its scrolling (the HeaderConcepts idiom).
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, color: "#e8ecf4", fontFamily: FONT, overflowY: "auto", overscrollBehavior: "none" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 28px 110px" }}>
        <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: "0.18em", color: "#5e6a83", marginBottom: 10 }}>SVAMP · DASHBOARD · DESIGN RECORD</div>
        <h1 style={{ fontFamily: FONT, fontSize: 26, fontWeight: 650, margin: "0 0 10px" }}>Scope banner</h1>
        <p style={{ fontFamily: FONT, fontSize: 14, lineHeight: 1.7, color: "#9aa6bd", maxWidth: 880, margin: 0 }}>
          The banner names the scope every panel below it is about, and pins under the lens rail on scroll.
          All options inherit the report&apos;s context-banner surface — scope smallcaps in the scope&apos;s brand color,
          a dot, the entity, its code — full-bleed at dashboard width. They fork on the <em>exit affordance</em> for
          college scope (replacing the &ldquo;← consortium&rdquo; button) and on vertical presence. Hover the dimmed
          CONSORTIUM crumb in B2/B3 — it&apos;s live, to judge the feel.
        </p>

        <OptionHeading n={1} title="The report's banner, verbatim" question="Display-only — maximal consistency; the data is the control." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={GOLD}>✓ decided 2026-06-06 — shipped to ScopeBanner</Chip>
          <Chip color={SUPPLY}>46px · report-identical type</Chip>
          <Chip>exit: click a matrix row / treemap cell</Chip>
          <Chip>zero interactive chrome</Chip>
        </div>
        {option(b1)}
        <Caption>
          Byte-level consistency with the report: same heights, same type, same dot grammar. The banner asserts,
          never acts — leaving scope changes entirely to the coverage matrix and treemap, which already do this.
          The trade: deep in the scope bands the matrix is off-screen, so leaving college scope means scrolling up
          first. Cleanest, least discoverable.
        </Caption>

        <OptionHeading n={2} title="Breadcrumb scope" question="The path is the exit — ancestry is clickable, no button." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={SUPPLY}>52px · name up to 14.5/600</Chip>
          <Chip>exit: click CONSORTIUM in the path</Chip>
          <Chip>consortium state = B1 purity</Chip>
        </div>
        {option(b2)}
        <Caption>
          In college scope the scope label becomes a path — CONSORTIUM dimmed to ancestry, the college in its brand —
          and clicking the ancestor returns to it. No furniture: navigation is the structure itself, which is also the
          URL&apos;s grammar (scope is a param; the crumb just edits it). At consortium scope it collapses to B1&apos;s
          single label, so the common state stays pure. Slightly taller and the entity steps up to 14.5px/600 —
          prominent without becoming a second masthead.
        </Caption>

        <OptionHeading n={3} title="Masthead two-liner" question="Eyebrow path over a 17px title — the report's masthead hierarchy, condensed." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={SUPPLY}>~64px · title 17/650</Chip>
          <Chip>exit: click CONSORTIUM in the eyebrow</Chip>
          <Chip>largest standing presence</Chip>
        </div>
        {option(b3)}
        <Caption>
          The report&apos;s eyebrow→title hierarchy transposed: scope path as the eyebrow, the entity as a true title.
          Unmissable at a glance and projectable across a room. The trade: ~64 sticky pixels on every scroll position —
          the nav + rail + banner stack reaches ~190px before content begins, taxing the very panels the lab is tuning.
        </Caption>

        <div style={{ marginTop: 60, borderTop: `1px solid ${HAIR}`, paddingTop: 18, fontFamily: FONT, fontSize: 12.5, color: "#5e6a83", lineHeight: 1.7, maxWidth: 880 }}>
          Recommendation was B2; <span style={{ color: GOLD }}>DECIDED: B1</span> (2026-06-06) — display-only purity,
          the data is the control. The exit affordance question stays answered by the coverage matrix and treemap.
        </div>
      </div>
    </div>
  );
}
