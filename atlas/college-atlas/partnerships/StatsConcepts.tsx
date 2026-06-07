"use client";

/* ── SVAMP Dashboard — demand-stats panel concepts ──────────────────────────
   DESIGN EXPLORATION, not a product surface (sibling of /svamp/concepts).
   The "Demand & Gap" panel sheds its modeled rows (consortium supply 28.33,
   gap 522/yr — derived numbers with fake-precision smell) and keeps the four
   OBSERVED COE figures: annual openings, median wage, growth, employment.
   These options explore how four numbers earn a panel: as a quartet, as a
   hierarchy, or in context. All mocks use the real 49-9041 figures and real
   cross-SOC context from the landscape payload (which the lens already
   fetches — no new data machinery for any option). Delete with
   /svamp/concepts once the panel is settled. */

import React from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";
const GOLD = "#c9a84c";
const DEMAND = "#ff5a5a";
const INK = "#e8ecf4";
const SLATE = "#5e6a83";
const BODY = "#9aa6bd";

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

/* ── Page scaffolding (the concepts-family idiom) ─────────────────────────── */
function OptionHeading({ n, title, question }: { n: number; title: string; question: string }) {
  return (
    <div style={{ margin: "54px 0 6px" }}>
      <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: "0.16em", color: GOLD, marginBottom: 6 }}>OPTION S{n}</div>
      <div style={{ fontFamily: FONT, fontSize: 19, fontWeight: 650, color: INK }}>{title}</div>
      <div style={{ fontFamily: FONT, fontSize: 13, color: BODY, marginTop: 3 }}>{question}</div>
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
  return <p style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.65, color: BODY, maxWidth: 880, margin: "12px 0 0" }}>{children}</p>;
}

/* ── The real slot: DashPanel chrome at the baked 345px row height ────────── */
function PanelMock({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ width: 873, maxWidth: "100%", height: 345, display: "flex", flexDirection: "column", border: `1px solid ${HAIR}`, borderRadius: 10, background: "rgba(255,255,255,0.022)", overflow: "hidden", marginTop: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)", flex: "none" }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: DEMAND, flex: "none" }} />
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, letterSpacing: "0.04em", color: "rgba(255,255,255,0.88)" }}>Occupation Summary</span>
        <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 9.5, color: "rgba(255,255,255,0.4)" }}>· COE</span>
      </div>
      <div style={{ flex: 1, minHeight: 0, padding: 10, display: "flex", flexDirection: "column" }}>{children}</div>
    </div>
  );
}

// The real 49-9041 figures, and real cross-SOC context (12 SVAMP occupations).
const STAT = { openings: 550, wage: 80760, growth: 0.102, employment: 5450 };
const CTX = { wageMin: 70750, wageMax: 95880, regionalOpenings: 2710 };

/* ── Stat glyphs — four new members of the platonic-form family ────────────
   Same geometric language as the lens/surface forms (32×32, stroke 1.8,
   round caps, reduced archetypes): the doorway (an opening), the banknote
   (the wage), the rising line (growth), the crew (the employed base). */
type Glyph = React.FC;
const FormDoorway: Glyph = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M9 27V6h14v21" /><path d="M5 27h22" /><path d="M13 27V9.5l7 2.2V27" /><path d="M17.4 18.6v.01" />
  </svg>
);
const FormBanknote: Glyph = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <rect x="4" y="9" width="24" height="14" rx="2" /><circle cx="16" cy="16" r="3.6" /><path d="M8 13v6M24 13v6" />
  </svg>
);
const FormRise: Glyph = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M5 24l8-8 4 4 9-9" /><path d="M20.5 11H26v5.5" /><path d="M5 27.5h22" />
  </svg>
);
const FormCrew: Glyph = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <circle cx="12" cy="11.5" r="3.8" /><path d="M5 25.5c0-4.2 3.1-6.8 7-6.8s7 2.6 7 6.8" />
    <circle cx="21.5" cy="13" r="3" /><path d="M21.5 19.4c3.2 0 5.4 2.1 5.7 5.4" />
  </svg>
);

const QUARTET = [
  { k: "Annual Openings", v: "550", sub: "/yr · projected", Icon: FormDoorway, accent: true },
  { k: "Median Wage", v: "$80,760", sub: "annual", Icon: FormBanknote, accent: false },
  { k: "Growth", v: "10.2%", sub: "projection period", Icon: FormRise, accent: false },
  { k: "Employment", v: "5,450", sub: "regional jobs", Icon: FormCrew, accent: false },
];

/* ════════════════════════════════════════════════════════════════════════ */
export default function StatsConcepts() {
  /* S1 — stat quartet: 2×2 big numerals on a hairline cross. */
  const s1 = (
    <PanelMock>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr" }}>
        {[
          { k: "Annual Openings", v: "550", sub: "/yr · projected", accent: true },
          { k: "Median Wage", v: "$80,760", sub: "annual" },
          { k: "Growth", v: "10.2%", sub: "projection period" },
          { k: "Employment", v: "5,450", sub: "regional jobs" },
        ].map((s, i) => (
          <div key={s.k} style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 4, borderRight: i % 2 === 0 ? `1px solid rgba(255,255,255,0.05)` : "none", borderBottom: i < 2 ? `1px solid rgba(255,255,255,0.05)` : "none" }}>
            <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: SLATE }}>{s.k}</div>
            <div style={{ fontFamily: MONO, fontSize: 34, fontWeight: 600, color: s.accent ? DEMAND : INK, lineHeight: 1 }}>{s.v}</div>
            <div style={{ fontFamily: FONT, fontSize: 11, color: SLATE }}>{s.sub}</div>
          </div>
        ))}
      </div>
    </PanelMock>
  );

  /* S1a — totem: glyph above label above numeral, centered columns. */
  const s1a = (
    <PanelMock>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr" }}>
        {QUARTET.map((s, i) => (
          <div key={s.k} style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 5, borderRight: i % 2 === 0 ? `1px solid rgba(255,255,255,0.05)` : "none", borderBottom: i < 2 ? `1px solid rgba(255,255,255,0.05)` : "none" }}>
            <span style={{ width: 22, height: 22, color: s.accent ? DEMAND : SLATE, display: "flex" }}><s.Icon /></span>
            <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: SLATE }}>{s.k}</div>
            <div style={{ fontFamily: MONO, fontSize: 31, fontWeight: 600, color: s.accent ? DEMAND : INK, lineHeight: 1 }}>{s.v}</div>
            <div style={{ fontFamily: FONT, fontSize: 11, color: SLATE }}>{s.sub}</div>
          </div>
        ))}
      </div>
    </PanelMock>
  );

  /* S1b — badge: tinted glyph square leading a left-aligned stat block. */
  const s1b = (
    <PanelMock>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr" }}>
        {QUARTET.map((s, i) => {
          const tone = s.accent ? DEMAND : "#94a8c9";
          return (
            <div key={s.k} style={{ display: "flex", alignItems: "center", gap: 16, padding: "0 26px", borderRight: i % 2 === 0 ? `1px solid rgba(255,255,255,0.05)` : "none", borderBottom: i < 2 ? `1px solid rgba(255,255,255,0.05)` : "none" }}>
              <span style={{ width: 42, height: 42, borderRadius: 10, background: hexA(tone, 0.1), border: `1px solid ${hexA(tone, 0.22)}`, display: "flex", alignItems: "center", justifyContent: "center", flex: "none" }}>
                <span style={{ width: 22, height: 22, color: tone, display: "flex" }}><s.Icon /></span>
              </span>
              <div>
                <div style={{ fontFamily: MONO, fontSize: 27, fontWeight: 600, color: s.accent ? DEMAND : INK, lineHeight: 1.1 }}>{s.v}</div>
                <div style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.12em", textTransform: "uppercase", color: SLATE, marginTop: 3 }}>{s.k}</div>
              </div>
            </div>
          );
        })}
      </div>
    </PanelMock>
  );

  /* S1c — watermark: the glyph as a large, faint field behind each numeral. */
  const s1c = (
    <PanelMock>
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr" }}>
        {QUARTET.map((s, i) => (
          <div key={s.k} style={{ position: "relative", overflow: "hidden", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 4, borderRight: i % 2 === 0 ? `1px solid rgba(255,255,255,0.05)` : "none", borderBottom: i < 2 ? `1px solid rgba(255,255,255,0.05)` : "none" }}>
            <span style={{ position: "absolute", right: -14, bottom: -18, width: 104, height: 104, color: s.accent ? DEMAND : "#94a8c9", opacity: 0.07, display: "flex", pointerEvents: "none" }}>
              <s.Icon />
            </span>
            <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: SLATE }}>{s.k}</div>
            <div style={{ fontFamily: MONO, fontSize: 34, fontWeight: 600, color: s.accent ? DEMAND : INK, lineHeight: 1 }}>{s.v}</div>
            <div style={{ fontFamily: FONT, fontSize: 11, color: SLATE }}>{s.sub}</div>
          </div>
        ))}
      </div>
    </PanelMock>
  );

  /* S2 — demand-led hierarchy: openings as the hero, the trio beneath. */
  const s2 = (
    <PanelMock>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "0 18px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontFamily: MONO, fontSize: 58, fontWeight: 650, color: DEMAND, lineHeight: 1 }}>550</span>
          <span style={{ fontFamily: FONT, fontSize: 15, color: BODY }}>openings <span style={{ color: SLATE }}>/ yr</span></span>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: SLATE, marginTop: 7 }}>
          Regional Annual Demand · COE Projection
        </div>
        <div style={{ height: 1, background: "rgba(255,255,255,0.07)", margin: "20px 0 18px" }} />
        <div style={{ display: "flex", gap: 0 }}>
          {[
            { k: "Median Wage", v: "$80,760" },
            { k: "Growth", v: "10.2%" },
            { k: "Employment", v: "5,450" },
          ].map((s, i) => (
            <div key={s.k} style={{ flex: 1, paddingLeft: i ? 22 : 0, borderLeft: i ? `1px solid rgba(255,255,255,0.05)` : "none" }}>
              <div style={{ fontFamily: MONO, fontSize: 21, fontWeight: 600, color: INK, lineHeight: 1.1 }}>{s.v}</div>
              <div style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.12em", textTransform: "uppercase", color: SLATE, marginTop: 4 }}>{s.k}</div>
            </div>
          ))}
        </div>
      </div>
    </PanelMock>
  );

  /* S3 — stats in context: each number qualified by a micro-visual derived
     from the landscape payload (share of regional demand, wage position
     across the 12 SOCs, growth delta, turnover ratio). */
  const sharePct = Math.round((STAT.openings / CTX.regionalOpenings) * 100);
  const wagePos = (STAT.wage - CTX.wageMin) / (CTX.wageMax - CTX.wageMin);
  const turnover = Math.round((STAT.openings / STAT.employment) * 1000) / 10;
  const Row = ({ k, v, children }: { k: string; v: React.ReactNode; children: React.ReactNode }) => (
    <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 18, borderBottom: `1px solid rgba(255,255,255,0.04)`, padding: "0 8px" }}>
      <div style={{ width: 150, fontFamily: MONO, fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: SLATE, flex: "none" }}>{k}</div>
      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
      <div style={{ fontFamily: MONO, fontSize: 20, fontWeight: 600, color: INK, flex: "none", minWidth: 110, textAlign: "right" }}>{v}</div>
    </div>
  );
  const s3 = (
    <PanelMock>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Row k="Annual Openings" v={<span style={{ color: DEMAND }}>550<span style={{ fontSize: 12, color: hexA(DEMAND, 0.7) }}>/yr</span></span>}>
          <div style={{ position: "relative", height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)" }}>
            <div style={{ position: "absolute", inset: 0, width: `${sharePct}%`, borderRadius: 3, background: hexA(DEMAND, 0.75) }} />
          </div>
          <div style={{ fontFamily: FONT, fontSize: 10.5, color: SLATE, marginTop: 4 }}>{sharePct}% of regional advanced-manufacturing demand</div>
        </Row>
        <Row k="Median Wage" v="$80,760">
          <div style={{ position: "relative", height: 6, borderRadius: 3, background: "rgba(255,255,255,0.06)" }}>
            <div style={{ position: "absolute", top: -3, left: `${wagePos * 100}%`, width: 12, height: 12, borderRadius: "50%", background: INK, border: `2.5px solid ${BG}`, transform: "translateX(-50%)" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 9.5, color: SLATE, marginTop: 4 }}>
            <span>$70,750</span><span style={{ fontFamily: FONT, fontSize: 10.5 }}>across the 12 SVAMP occupations</span><span>$95,880</span>
          </div>
        </Row>
        <Row k="Growth" v="10.2%">
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontFamily: MONO, fontSize: 11, color: "#7dd087", background: "rgba(125,208,135,0.1)", borderRadius: 5, padding: "3px 9px" }}>
            ▲ growing
          </span>
          <span style={{ fontFamily: FONT, fontSize: 10.5, color: SLATE, marginLeft: 10 }}>projected over the COE period</span>
        </Row>
        <Row k="Employment" v="5,450">
          <span style={{ fontFamily: FONT, fontSize: 10.5, color: SLATE }}>
            openings replace <span style={{ fontFamily: MONO, color: BODY }}>{turnover}%</span> of the employed base each year
          </span>
        </Row>
      </div>
    </PanelMock>
  );

  return (
    // Fixed scroll container — globals.css locks body overflow for the atlas
    // scenes, so every page owns its scrolling.
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, color: INK, fontFamily: FONT, overflowY: "auto", overscrollBehavior: "none" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 28px 110px" }}>
        <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: "0.18em", color: SLATE, marginBottom: 10 }}>SVAMP · DASHBOARD · DESIGN RECORD</div>
        <h1 style={{ fontFamily: FONT, fontSize: 26, fontWeight: 650, margin: "0 0 10px" }}>Demand stats panel</h1>
        <p style={{ fontFamily: FONT, fontSize: 14, lineHeight: 1.7, color: BODY, maxWidth: 880, margin: 0 }}>
          The panel keeps the four observed COE figures — openings, wage, growth, employment — and drops the modeled
          rows (consortium supply, gap; the supply-vs-demand read already lives in the Awards chart&apos;s demand line).
          Every mock sits in the real slot: half-row width at the baked 345px height, titled
          <em> Occupation Summary</em> (decided 2026-06-06 — &ldquo;Demand &amp; Gap&rdquo; dies with the gap row).
          All context data shown is derivable from the landscape payload the lens already fetches.
        </p>

        <OptionHeading n={1} title="Stat quartet" question="Four equals on a hairline cross — the classic instrument read." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={DEMAND}>openings carries the lens accent</Chip>
          <Chip>34px numerals · projection-legible</Chip>
          <Chip>zero new data</Chip>
        </div>
        {s1}
        <Caption>
          The four figures as peers in a 2×2, centered on a faint cross. Numerals at 34px read across a room;
          each carries a quiet unit line so nothing needs a legend. Openings takes the lens red as the one accent —
          demand is still the panel&apos;s subject. Strongest at a glance; says nothing about how the numbers relate.
        </Caption>

        <div style={{ margin: "54px 0 6px" }}>
          <div style={{ fontFamily: MONO, fontSize: 10.5, letterSpacing: "0.16em", color: GOLD, marginBottom: 6 }}>S1 VARIATIONS · SYMBOLS</div>
          <div style={{ fontFamily: FONT, fontSize: 19, fontWeight: 650, color: INK }}>The quartet with glyphs</div>
          <div style={{ fontFamily: FONT, fontSize: 13, color: BODY, marginTop: 3 }}>
            Four new members of the platonic-form family — doorway (an opening), banknote (the wage), rising line
            (growth), crew (the employed base) — same geometric language as the lens and surface icons (32×32,
            stroke 1.8, reduced archetypes). The variations differ on where the symbol sits.
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "16px 0 2px" }}>
          <Chip color={GOLD}>✓ decided 2026-06-06 — shipped as Occupation Summary</Chip>
          <Chip color={DEMAND}>S1a · totem</Chip>
          <Chip>glyph crowns the column — quiet hieroglyph</Chip>
        </div>
        {s1a}
        <Caption>
          The glyph sits above the label like a column capital, in the same slate as the label (openings in the lens
          red). The icons read as hieroglyphs of the product&apos;s form language, not decoration — the panel stays
          typographic, the symbols index it. Most in-voice with the lens tabs and surface nav.
          REVISED in build (2026-06-06): the openings accent was dropped — all four numerals render as peers.
          Pre-ranking one figure is editorial; which number matters most (a negative growth projection can outrank
          openings) is the reader&apos;s call.
        </Caption>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "26px 0 2px" }}>
          <Chip color={DEMAND}>S1b · badge</Chip>
          <Chip>tinted glyph square leads each stat</Chip>
        </div>
        {s1b}
        <Caption>
          The conventional dashboard treatment: a tinted rounded square carries the glyph, the stat block sits
          beside it, left-aligned. Warmest and most &ldquo;designed&rdquo; at first glance — and the most generic;
          this is the one pattern every SaaS dashboard ships, and the filled chips sit slightly outside the
          product&apos;s hairline-and-stroke voice.
        </Caption>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "26px 0 2px" }}>
          <Chip color={DEMAND}>S1c · watermark</Chip>
          <Chip>the glyph as a faint field behind the numeral</Chip>
        </div>
        {s1c}
        <Caption>
          The glyph blown up to 104px and faded to 7% in each cell&apos;s corner — texture rather than icon, like a
          watermark on an instrument dial. Keeps S1&apos;s typographic purity at reading distance while giving the
          panel visual depth up close. The risk: at projection brightness the watermarks can vanish entirely (which
          is graceful) or smear (which is not) — worth one look on the actual conference screen.
        </Caption>

        <OptionHeading n={2} title="Demand-led hierarchy" question="Openings is the headline; wage, growth, employment qualify it." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={DEMAND}>58px hero numeral</Chip>
          <Chip>supporting trio at 21px</Chip>
          <Chip>zero new data</Chip>
        </div>
        {s2}
        <Caption>
          One argument per panel: <em>this occupation demands 550 hires a year</em> — everything else is supporting
          evidence below the rule. Mirrors how the report reasons (demand leads, qualities follow) and gives the
          panel a clear reading order. The trade: wage/growth/employment become second-class, though wage is often
          what a college dean actually asks first.
        </Caption>

        <OptionHeading n={3} title="Stats in context" question="Each number wears its comparison — share, range, direction, ratio." />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", margin: "10px 0 2px" }}>
          <Chip color={DEMAND}>share-of-demand bar</Chip>
          <Chip>wage dot on the 12-SOC range</Chip>
          <Chip>turnover ratio from the numbers themselves</Chip>
          <Chip>context derived from the landscape payload</Chip>
        </div>
        {s3}
        <Caption>
          A number alone asks the viewer to know the baseline; these carry it. Openings shows its share of the
          region&apos;s whole demand ({sharePct}%), wage places itself on the actual range across the 12 SVAMP
          occupations, growth reads as direction, and employment is restated as the turnover the openings imply.
          The most intuitive per stat — and the busiest; the micro-visuals must stay this quiet or the panel
          becomes four tiny charts.
        </Caption>

        <div style={{ marginTop: 60, borderTop: `1px solid ${HAIR}`, paddingTop: 18, fontFamily: FONT, fontSize: 12.5, color: SLATE, lineHeight: 1.7, maxWidth: 880 }}>
          DIRECTION (2026-06-06): the user chose the S1 quartet, retitled <span style={{ color: BODY }}>Occupation
          Summary</span>, with symbolic components — see the S1 variations above. Among them I&apos;d recommend
          <span style={{ color: BODY }}> S1a (totem)</span>: it extends the platonic-form vocabulary the lens tabs and
          surface nav already speak, where S1b imports a generic SaaS pattern and S1c risks washing out under
          projection. Earlier recommendation (S3) and S2/S3 below stand as the record of the road not taken.
        </div>
      </div>
    </div>
  );
}
