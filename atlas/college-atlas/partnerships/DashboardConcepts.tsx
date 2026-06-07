"use client";

/* ── SVAMP Dashboard — layout concepts ──────────────────────────────────────
   A DESIGN EXPLORATION, not a product surface: static mocks of the candidate
   dashboard layouts, rendered in the report's own design language (same fonts,
   accents, panel chrome, treemap/matrix/trend idioms) so the layout forks can
   be judged visually before any implementation. No data fetches — every
   visualization is a hand-shaped placeholder at faithful proportions.

   The four forks on display:
     1. Top-level layout grammar — supply|demand panes vs. one lens at a time
     2. Detail band semantics — consortium|college split vs. tiled visual grid
     3. Viewport discipline — strict no-scroll fit vs. scrolling detail band
     4. Employers integration — selection-linked map vs. standalone map
   Delete this file (and its route) once the dashboard design is settled. */

import React from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { squarify } from "@/college-atlas/partnerships/treemap";

// Mirrors SvampView's lens accents (local constants there, not exported).
const DEMAND = "#ff5a5a";
const SUPPLY = "#50c878";
const EMPLOYER = "#5a9bd4";
const GOLD = "#c9a84c";
const BG = "#060d1f";
const PANEL = "rgba(255,255,255,0.022)";
const HAIR = "rgba(255,255,255,0.09)";
// Member-college brand stand-ins (De Anza pink, Evergreen green, Foothill
// crimson, Mission teal-ish, Ohlone green) — close enough for layout reading.
const COLLEGES = ["#e85d8a", "#7bd88f", "#b1122b", "#5ab0c4", "#50c878"];

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

/* ── Mock primitives — the report's vocabulary at placeholder fidelity ───── */

// Panel chrome with the authority-chip signature: every panel names its
// institutional source, transposing the report's prose attributions.
function Panel({ title, authority, accent, children, grow = 1 }: {
  title: string; authority: string; accent: string; children: React.ReactNode; grow?: number;
}) {
  return (
    <div style={{ flex: grow, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", border: `1px solid ${HAIR}`, borderRadius: 8, background: PANEL, overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 9px", borderBottom: `1px solid rgba(255,255,255,0.05)` }}>
        <span style={{ width: 3, height: 10, borderRadius: 2, background: accent }} />
        <span style={{ fontFamily: FONT, fontSize: 9.5, fontWeight: 600, letterSpacing: "0.06em", color: "rgba(255,255,255,0.85)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</span>
        <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 8, color: "rgba(255,255,255,0.38)", whiteSpace: "nowrap" }}>· {authority}</span>
      </div>
      <div style={{ flex: 1, minHeight: 0, padding: 7 }}>{children}</div>
    </div>
  );
}

// Squarified treemap via the real algorithm — faithful shapes, fake values.
function MockTreemap({ accent, highlight }: { accent: string; highlight?: number[] }) {
  const values = [510, 300, 150, 110, 80, 60, 45, 30];
  const rects = squarify(values, 0, 0, 100, 60);
  return (
    <svg viewBox="0 0 100 60" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block" }}>
      {rects.map((r, i) => (
        <rect key={i} x={r.x + 0.4} y={r.y + 0.4} width={Math.max(0, r.w - 0.8)} height={Math.max(0, r.h - 0.8)} rx={0.8}
          fill={hexA(accent, 1 - (i / (values.length - 1)) * 0.62)} opacity={0.5}
          stroke={highlight?.includes(i) ? "#e8ecf4" : "none"} strokeWidth={highlight?.includes(i) ? 0.9 : 0} />
      ))}
    </svg>
  );
}

// Coverage grid: 5 college columns × n unit rows, three coverage levels.
// highlightRow outlines a unit's whole row; highlightCell rings one
// (row, college) cell — the targeted-college selection.
function MockMatrix({ rows = 8, highlightRow, highlightCell }: { rows?: number; highlightRow?: number; highlightCell?: [number, number] }) {
  const LEVELS = ["rgba(148,168,201,.92)", "rgba(148,168,201,.3)", "rgba(255,255,255,.035)"];
  const seed = (r: number, c: number) => LEVELS[((r * 7 + c * 5 + 3) % 11) % 3];
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(5, 1fr)`, gap: 2, height: "100%", alignContent: "stretch" }}>
      {Array.from({ length: rows * 5 }, (_, k) => {
        const r = Math.floor(k / 5), c = k % 5;
        const cell = highlightCell && highlightCell[0] === r && highlightCell[1] === c;
        return <div key={k} style={{ borderRadius: 2, background: seed(r, c), outline: cell ? `1.5px solid ${COLLEGES[0]}` : highlightRow === r ? "1px solid #e8ecf4" : "none", minHeight: 0 }} />;
      })}
    </div>
  );
}

// Trend chart: stacked area bands (college colors) + optional gold demand
// line with the axis rescaled — the vs.-demand squash at mock fidelity.
function MockTrend({ demand = false, lines = false }: { demand?: boolean; lines?: boolean }) {
  const top = demand ? [12, 11, 12.5, 11.5, 12] : [40, 36, 42, 38, 44];      // stack top edge (% of height from bottom)
  const mid = top.map((v) => v * 0.7);
  const X = (i: number) => 4 + (i / 4) * 92;
  const Y = (v: number) => 56 - (v / 100) * 52;
  const path = (vals: number[]) => vals.map((v, i) => `${i ? "L" : "M"}${X(i)} ${Y(v)}`).join(" ");
  const area = (vals: number[], base: number[]) =>
    `${path(vals)} ${base.map((v, i, a) => `L${X(a.length - 1 - i)} ${Y(base[a.length - 1 - i])}`).join(" ")} Z`;
  return (
    <svg viewBox="0 0 100 60" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block" }}>
      <line x1={4} x2={96} y1={Y(0)} y2={Y(0)} stroke="rgba(255,255,255,.12)" strokeWidth={0.4} />
      {[25, 50, 75].map((g) => <line key={g} x1={4} x2={96} y1={Y(g)} y2={Y(g)} stroke="rgba(255,255,255,.045)" strokeWidth={0.35} />)}
      {lines ? (
        <>
          <path d={path(top)} fill="none" stroke={COLLEGES[0]} strokeWidth={1.1} opacity={0.85} />
          <path d={path(mid)} fill="none" stroke={GOLD} strokeWidth={1.1} opacity={0.85} />
        </>
      ) : (
        <>
          <path d={area(top, mid)} fill={COLLEGES[1]} opacity={0.35} />
          <path d={area(mid, mid.map(() => 0))} fill={COLLEGES[0]} opacity={0.4} />
          <path d={path(top)} fill="none" stroke={COLLEGES[1]} strokeWidth={0.8} />
        </>
      )}
      {demand && (
        <>
          <line x1={4} x2={96} y1={Y(88)} y2={Y(88)} stroke={GOLD} strokeWidth={1} />
          <text x={96} y={Y(88) - 2.5} textAnchor="end" style={{ fontFamily: MONO, fontSize: 4.4, fontWeight: 600, fill: GOLD }}>1,020/yr</text>
        </>
      )}
    </svg>
  );
}

// Wage dumbbells: three cohort rows, before → after ramp in a brand hue.
function MockDumbbell({ accent = COLLEGES[0] }: { accent?: string }) {
  const rows = [[18, 62], [24, 78], [30, 88]];
  return (
    <svg viewBox="0 0 100 60" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block" }}>
      {rows.map(([a, b], i) => {
        const y = 12 + i * 17;
        return (
          <g key={i}>
            <line x1={a} x2={b} y1={y} y2={y} stroke={hexA(accent, 0.3)} strokeWidth={2.4} strokeLinecap="round" />
            <circle cx={a} cy={y} r={2.4} fill={hexA(accent, 0.5)} />
            <circle cx={b} cy={y} r={2.6} fill={accent} />
          </g>
        );
      })}
    </svg>
  );
}

// Regional employer map: scattered dots; `linked` highlights a selected subset.
function MockMap({ linked }: { linked: boolean }) {
  const pts = [[14, 18], [22, 34], [30, 12], [38, 42], [46, 24], [55, 50], [60, 16], [68, 36], [74, 52], [80, 22], [86, 44], [26, 52], [50, 8], [64, 58], [12, 46], [90, 12]];
  const hot = new Set([1, 4, 7, 10, 13]);
  return (
    <svg viewBox="0 0 100 64" preserveAspectRatio="none" style={{ width: "100%", height: "100%", display: "block" }}>
      <path d="M6 6 Q 40 -2 70 8 T 96 30 Q 92 54 60 60 T 8 50 Z" fill={hexA(EMPLOYER, 0.05)} stroke={hexA(EMPLOYER, 0.18)} strokeWidth={0.5} />
      {pts.map(([x, y], i) => {
        const on = linked && hot.has(i);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={on ? 1.9 : 1.4} fill={on ? EMPLOYER : hexA(EMPLOYER, linked ? 0.22 : 0.65)} />
            {on && <circle cx={x} cy={y} r={3.4} fill="none" stroke={hexA(EMPLOYER, 0.55)} strokeWidth={0.5} />}
          </g>
        );
      })}
    </svg>
  );
}

function Chip({ children, color = "rgba(255,255,255,0.5)" }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{ fontFamily: MONO, fontSize: 9, color, border: `1px solid ${hexA("#9aa6bd", 0.25)}`, borderRadius: 5, padding: "2px 7px", whiteSpace: "nowrap" }}>{children}</span>
  );
}

// Pane header: the scope chrome of a dashboard region (SUPPLY / DEMAND / etc.).
function PaneHead({ label, sub, accent }: { label: string; sub: string; accent: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 8, padding: "2px 2px 6px" }}>
      <span style={{ fontFamily: FONT, fontSize: 10.5, fontWeight: 700, letterSpacing: "0.16em", color: accent }}>{label}</span>
      <span style={{ fontFamily: MONO, fontSize: 8.5, color: "rgba(255,255,255,0.4)" }}>{sub}</span>
    </div>
  );
}

/* ── Concept frames — each fork's options as full mock compositions ──────── */

// A viewport-proportioned frame (16:10) holding one mock dashboard layout.
function Frame({ tag, title, children, badge }: {
  tag: string; title: string; children: React.ReactNode; badge?: string;
}) {
  return (
    <div style={{ flex: 1, minWidth: 380 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
        <span style={{ fontFamily: MONO, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em", color: BG, background: badge ? GOLD : "#9aa6bd", borderRadius: 5, padding: "2px 8px" }}>{tag}</span>
        <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.88)" }}>{title}</span>
        {badge && <span style={{ fontFamily: MONO, fontSize: 9, color: GOLD }}>{badge}</span>}
      </div>
      <div style={{ aspectRatio: "16 / 10", border: `1px solid ${HAIR}`, borderRadius: 10, background: BG, padding: 10, display: "flex", flexDirection: "column", gap: 8, overflow: "hidden", boxShadow: "0 8px 28px rgba(0,0,0,0.35)" }}>
        {children}
      </div>
    </div>
  );
}

function Caption({ children }: { children: React.ReactNode }) {
  return <p style={{ fontFamily: FONT, fontSize: 12, lineHeight: 1.55, color: "#9aa6bd", margin: "10px 2px 0", maxWidth: 620 }}>{children}</p>;
}

function ForkHeading({ n, title, question }: { n: number; title: string; question: string }) {
  return (
    <div style={{ margin: "54px 0 18px", borderTop: `1px solid ${HAIR}`, paddingTop: 26 }}>
      <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", color: "rgba(255,255,255,0.4)", marginBottom: 6 }}>FORK {n}</div>
      <h2 style={{ fontFamily: FONT, fontSize: 19, fontWeight: 650, color: "#e8ecf4", margin: 0 }}>{title}</h2>
      <p style={{ fontFamily: FONT, fontSize: 13, color: "#9aa6bd", margin: "6px 0 0" }}>{question}</p>
    </div>
  );
}

/* Fork 1, Option A — supply|demand simultaneous panes. */
function ConceptDualPane() {
  return (
    <>
      <div style={{ flex: 3, minHeight: 0, display: "flex", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          <PaneHead label="SUPPLY" sub="Programs · TOP6" accent={SUPPLY} />
          <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
            <Panel title="Program supply" authority="DataMart" accent={SUPPLY}><MockTreemap accent={SUPPLY} highlight={[2]} /></Panel>
            <Panel title="Coverage" authority="DataMart" accent={SUPPLY}><MockMatrix rows={8} highlightRow={2} /></Panel>
          </div>
        </div>
        <div style={{ width: 1, background: HAIR }} />
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          <PaneHead label="DEMAND" sub="Occupations · SOC" accent={DEMAND} />
          <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
            <Panel title="Regional demand" authority="COE" accent={DEMAND}><MockTreemap accent={DEMAND} highlight={[0, 3]} /></Panel>
            <Panel title="Coverage" authority="DataMart" accent={DEMAND}><MockMatrix rows={8} highlightRow={0} /></Panel>
          </div>
        </div>
      </div>
      <div style={{ flex: 2, minHeight: 0, display: "flex", flexDirection: "column", gap: 5 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontFamily: MONO, fontSize: 8.5, color: "rgba(255,255,255,0.45)" }}>DETAIL · selection: 095630 Machining</span>
          <Chip color={hexA("#e8ecf4", 0.7)}>fed SOCs lit on the demand side ⟷ feeding TOPs lit on the supply side</Chip>
        </div>
        <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
          <Panel title="Awards vs demand" authority="DataMart · COE" accent={SUPPLY}><MockTrend demand /></Panel>
          <Panel title="Enrollments" authority="DataMart" accent={SUPPLY}><MockTrend lines /></Panel>
          <Panel title="Wage outcomes" authority="DataMart" accent={SUPPLY}><MockDumbbell /></Panel>
        </div>
      </div>
    </>
  );
}

/* Fork 1, Option B — one lens at a time, denser internals. */
function ConceptSingleLens() {
  return (
    <>
      <div style={{ display: "flex", gap: 6 }}>
        {(["Programs", "Occupations", "Employers"] as const).map((t, i) => (
          <span key={t} style={{ fontFamily: FONT, fontSize: 9.5, fontWeight: 600, padding: "3px 10px", borderRadius: 6, color: i === 0 ? "#e8ecf4" : "#9aa6bd", background: i === 0 ? "rgba(255,255,255,0.1)" : "transparent", border: `1px solid ${HAIR}` }}>{t}</span>
        ))}
      </div>
      <div style={{ flex: 3, minHeight: 0, display: "flex", gap: 8 }}>
        <Panel title="Program supply treemap" authority="DataMart" accent={SUPPLY}><MockTreemap accent={SUPPLY} /></Panel>
        <Panel title="Coverage matrix — college × program" authority="DataMart" accent={SUPPLY}><MockMatrix rows={9} /></Panel>
      </div>
      <div style={{ flex: 2, minHeight: 0, display: "flex", gap: 6 }}>
        <Panel title="Awards vs demand" authority="DataMart · COE" accent={SUPPLY}><MockTrend demand /></Panel>
        <Panel title="Enrollments" authority="DataMart" accent={SUPPLY}><MockTrend lines /></Panel>
        <Panel title="Occupations served" authority="COE" accent={DEMAND}><MockTreemap accent={DEMAND} /></Panel>
      </div>
    </>
  );
}

/* Fork 2 — detail-band semantics, rendered INSIDE the decided Concept-B
   geometry (lens tabs + full-width treemap|matrix), so the band is judged in
   its real context. The selected program (treemap rect / matrix row) is
   highlighted; B1 additionally rings one (program, college) cell — the
   targeted-college selection its right pane follows. */
function BTop({ cellSelected = false }: { cellSelected?: boolean }) {
  return (
    <>
      <div style={{ display: "flex", gap: 6 }}>
        {(["Programs", "Occupations", "Employers"] as const).map((t, i) => (
          <span key={t} style={{ fontFamily: FONT, fontSize: 9.5, fontWeight: 600, padding: "3px 10px", borderRadius: 6, color: i === 0 ? "#e8ecf4" : "#9aa6bd", background: i === 0 ? "rgba(255,255,255,0.1)" : "transparent", border: `1px solid ${HAIR}` }}>{t}</span>
        ))}
        <span style={{ marginLeft: "auto", alignSelf: "center", fontFamily: MONO, fontSize: 8.5, color: "rgba(255,255,255,0.45)" }}>selection: 095630 Machining{cellSelected ? " × De Anza" : ""}</span>
      </div>
      <div style={{ flex: 3, minHeight: 0, display: "flex", gap: 8 }}>
        <Panel title="Program supply treemap" authority="DataMart" accent={SUPPLY}><MockTreemap accent={SUPPLY} highlight={[2]} /></Panel>
        <Panel title="Coverage matrix — college × program" authority="DataMart" accent={SUPPLY}><MockMatrix rows={9} highlightRow={2} highlightCell={cellSelected ? [2, 0] : undefined} /></Panel>
      </div>
    </>
  );
}

function ConceptB1Full() {
  return (
    <>
      <BTop cellSelected />
      <div style={{ flex: 2.6, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <BandConsortiumCollege />
      </div>
    </>
  );
}

function ConceptB2Full() {
  return (
    <>
      <BTop />
      <div style={{ flex: 2.6, minHeight: 0, display: "flex", flexDirection: "column", gap: 5 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontFamily: MONO, fontSize: 8.5, fontWeight: 600, letterSpacing: "0.1em", color: SUPPLY }}>CONSORTIUM · 095630 MACHINING</span>
          <Chip>click a matrix cell → scope becomes that college</Chip>
        </div>
        <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
          <Panel title="Awards vs demand" authority="DataMart · COE" accent={SUPPLY}><MockTrend demand /></Panel>
          <Panel title="Enrollments" authority="DataMart" accent={SUPPLY}><MockTrend lines /></Panel>
          <Panel title="Wage outcomes" authority="DataMart" accent={SUPPLY}><MockDumbbell /></Panel>
          <Panel title="Occupations served" authority="COE" accent={DEMAND}><MockTreemap accent={DEMAND} /></Panel>
        </div>
      </div>
    </>
  );
}

function BandConsortiumCollege() {
  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 8 }}>
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <PaneHead label="CONSORTIUM" sub="095630 Machining" accent={SUPPLY} />
        <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
          <Panel title="Awards vs demand" authority="DataMart · COE" accent={SUPPLY}><MockTrend demand /></Panel>
          <Panel title="Enrollments" authority="DataMart" accent={SUPPLY}><MockTrend /></Panel>
        </div>
      </div>
      <div style={{ width: 1, background: HAIR }} />
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <PaneHead label="DE ANZA" sub="095630 · targeted" accent={COLLEGES[0]} />
        <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 6 }}>
          <Panel title="Awards by credential" authority="DataMart" accent={COLLEGES[0]}><MockTrend /></Panel>
          <Panel title="Enrollment by credit family" authority="DataMart" accent={COLLEGES[0]}><MockTrend lines /></Panel>
        </div>
      </div>
    </div>
  );
}

/* Fork 4 — employers integration. */
function EmployersFrame({ linked }: { linked: boolean }) {
  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", gap: 8 }}>
      <div style={{ flex: 3, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <PaneHead label="EMPLOYERS" sub={linked ? "hiring for 51-4041 Machinists" : "Bay Area · advanced manufacturing"} accent={EMPLOYER} />
        <div style={{ flex: 1, minHeight: 0 }}>
          <Panel title="Regional employer map" authority="EDD" accent={EMPLOYER} grow={1}>
            <MockMap linked={linked} />
          </Panel>
        </div>
        <div style={{ display: "flex", gap: 6, paddingTop: 6 }}>
          <Chip>shown 41 / total 58</Chip>
          {linked && <Chip color={EMPLOYER}>filtered by selection · HIRES_FOR</Chip>}
        </div>
      </div>
      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontFamily: MONO, fontSize: 8.5, color: "rgba(255,255,255,0.45)", padding: "2px 2px 4px" }}>{linked ? "CANDIDATE PARTNERS" : "ALL EMPLOYERS"}</span>
        {Array.from({ length: 7 }, (_, i) => (
          <div key={i} style={{ height: 16, borderRadius: 4, background: linked && i < 4 ? hexA(EMPLOYER, 0.18) : "rgba(255,255,255,0.03)", border: `1px solid ${linked && i < 4 ? hexA(EMPLOYER, 0.4) : HAIR}` }} />
        ))}
      </div>
    </div>
  );
}

/* ── Page ─────────────────────────────────────────────────────────────────── */

export default function DashboardConcepts() {
  return (
    // The atlas root locks body scrolling (canvas-app shell), so routed
    // surfaces own their scroll — same fixed-inset pattern as /svamp.
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, overflowY: "auto", overscrollBehavior: "none", padding: "44px 30px 90px" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.16em", color: "rgba(255,255,255,0.4)" }}>DESIGN EXPLORATION · NOT A PRODUCT SURFACE</div>
        <h1 style={{ fontFamily: FONT, fontSize: 26, fontWeight: 700, color: "#e8ecf4", margin: "8px 0 4px" }}>SVAMP Dashboard — Layout Concepts</h1>
        <p style={{ fontFamily: FONT, fontSize: 13.5, lineHeight: 1.6, color: "#9aa6bd", maxWidth: 700, margin: 0 }}>
          The report transposed: same visual vocabulary (treemaps, coverage matrices, trend charts, the gold demand
          line, authority chips), spatial simultaneity instead of narrative sequence. Each fork below shows its
          options as static mocks at viewport proportions. Prose dies in the dashboard; its integrity obligations
          move into chrome — note the per-panel authority chips throughout.
        </p>

        <div style={{ marginTop: 22, border: `1px solid ${hexA(GOLD, 0.35)}`, borderRadius: 10, background: hexA(GOLD, 0.04), padding: "14px 18px", maxWidth: 700 }}>
          <div style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.14em", color: GOLD, marginBottom: 8 }}>ALL FORKS DECIDED · V1 REQUIREMENTS</div>
          {[
            ["1 · Grammar", "One lens at a time (tabs). Programs and Occupations share the dashboard grammar; Employers is its own state."],
            ["2 · Detail band", "Tiled grid, one scope. Selection via treemap/matrix: row = consortium scope, cell = that college's scope; decompositions appear in college scope."],
            ["3 · Viewport", "Strict 100vh fit, no scroll. ≥1440px target; small screens route to the report. Curriculum → count chips; prose → chrome."],
            ["4 · Employers", "Standalone full-bleed map at State-Atlas parity; no selection crosses the lens boundary; shown/total chip retained."],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", gap: 12, padding: "4px 0", alignItems: "baseline" }}>
              <span style={{ fontFamily: MONO, fontSize: 10, color: GOLD, flex: "none", width: 92 }}>{k}</span>
              <span style={{ fontFamily: FONT, fontSize: 12.5, lineHeight: 1.5, color: "rgba(255,255,255,0.82)" }}>{v}</span>
            </div>
          ))}
        </div>

        <ForkHeading n={1} title="Top-level layout grammar" question="Do the two lenses stay tabs, or become simultaneous supply | demand panes?" />
        <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>
          <Frame tag="A" title="Supply | Demand panes">
            <ConceptDualPane />
          </Frame>
          <Frame tag="B" title="One lens at a time, denser" badge="✓ decided">
            <ConceptSingleLens />
          </Frame>
        </div>
        <Caption>
          DECIDED: B. One lens owns the screen at a time — the report’s navigation, transposed; each lens gets the
          full width for its own aggregates and details. (A kept above for the record: it traded lens depth for the
          cross-lens brushing idea, which can still return later as targeted highlights within B.)
        </Caption>

        <ForkHeading n={2} title="Detail band semantics" question="Within the decided Concept B: when a unit is selected, what fills the band below the aggregates?" />
        <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>
          <Frame tag="B1" title="Consortium | College split">
            <ConceptB1Full />
          </Frame>
          <Frame tag="B2" title="Tiled visual grid, one scope" badge="✓ decided">
            <ConceptB2Full />
          </Frame>
        </div>
        <Caption>
          DECIDED: B2, for v1 simplicity. One selection model, one scope on screen: the user picks a view via the
          treemap or the matrix (a row = consortium scope, a cell = that college’s scope), and the band shows that
          scope’s data across four panels — the report’s toggle logic, transposed without new grammar. The
          decompositions (credential types, credit families) appear when a college scope is selected, as in the
          report’s targeted view. (B1’s permanent consortium-beside-college comparison kept for the record — it can
          return as a v2 “compare” mode without disturbing B2’s model.)
        </Caption>

        <ForkHeading n={3} title="Viewport discipline" question="Strict one-viewport fit, or may the detail band scroll?" />
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "center" }}>
          <Chip color={GOLD}>✓ revised: page scrolls · each visualization at its ideal proportion</Chip>
          <Chip>curriculum accordion → course-count chips</Chip>
          <Chip>pathway diagram → selection interaction</Chip>
          <Chip>prose → authority chips + legend sublabels</Chip>
          <Chip>≥1440px target · small screens route to the report</Chip>
        </div>
        <Caption>
          REVISED in build (2026-06-06): the strict 100vh fit shrank charts below readability — the wrong
          invariant. The decided priority is the inverse: every visualization renders whole at its ideal,
          report-like proportion (width-driven), and the dashboard page scrolls to hold them; the tab bar stays
          sticky. The other chips stand — curriculum stays count-level, prose stays chrome, and small screens
          still route to the report.
        </Caption>

        <ForkHeading n={4} title="Employers integration" question="Does the map join the selection model, or stand alone at full bleed?" />
        <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>
          <Frame tag="D1" title="Selection-linked map">
            <EmployersFrame linked />
          </Frame>
          <Frame tag="D2" title="Standalone map at full bleed" badge="✓ decided">
            <EmployersFrame linked={false} />
          </Frame>
        </div>
        <Caption>
          DECIDED: D2. Employers is its own state, entered via its tab — the dashboard grammar (treemap, matrix,
          scope band, selection model) belongs to Programs and Occupations only; no selection crosses the lens
          boundary. The map reaches State-Atlas parity in surface area, and the shown/total chip stays — an
          ungeocoded remainder never reads as complete. (D1’s HIRES_FOR linkage kept for the record as a possible
          later layer; it would not change D2’s structure, only light it up.)
        </Caption>
      </div>
    </div>
  );
}
