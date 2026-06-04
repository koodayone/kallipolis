"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { SchoolConfig } from "@/config/schoolConfig";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import { FONT, MONO, ReportHeader, Section, Prose } from "@/college-atlas/partnerships/reportChrome";
import { OpportunityReportBody } from "@/college-atlas/partnerships/OpportunityReport";
import { getSvampLandscape } from "@/college-atlas/partnerships/api";
import type {
  ApiSvampLandscape,
  ApiSvampCell,
  ApiSvampCollege,
  ApiSvampProgram,
} from "@/college-atlas/partnerships/api";

const GAP = "#e0654f";
// SVAMP consortium accent (red) — cube, eyebrow, hairline, section bars.
const ACCENT = "#ff5a5a";

type CollegeRef = { id: string; config: SchoolConfig };

type Props = {
  colleges: CollegeRef[]; // member colleges, in display order
  onBack: () => void;
};

// Plain-English role labels for the 12 SVAMP occupations. The role name leads;
// the SOC code rides beneath as provenance. No invented grouping — the twelve
// roles list in SOC order.
const ROLE_LABEL: Record<string, string> = {
  "17-3023": "Electrical & Electronic Eng. Techs",
  "17-3024": "Electro-Mech. & Mechatronics Techs",
  "17-3026": "Industrial Eng. Techs",
  "17-3027": "Mechanical Eng. Techs",
  "17-3028": "Calibration Techs",
  "17-3029": "Eng. Technologists, other",
  "49-9041": "Industrial Machinery Mechanics",
  "49-9043": "Machinery Maintenance Workers",
  "51-4041": "Machinists",
  "51-9141": "Semiconductor Processing",
  "51-9161": "CNC Tool Operators",
  "51-9162": "CNC Tool Programmers",
};

// Alignment level, grounded in the data: teaches it AND shows output evidence —
// a CoE supply projection OR actual conferred awards = strong; teaches it but no
// output signal of either kind = partial; no aligned curriculum = gap.
const hasOutput = (c: ApiSvampCell) => c.supply > 0 || c.awards_recent > 0;
function level(cell: ApiSvampCell | undefined): "none" | "partial" | "strong" {
  if (!cell || cell.course_count === 0) return "none";
  return hasOutput(cell) ? "strong" : "partial";
}
const rank = (c: ApiSvampCell) => (c.course_count === 0 ? 0 : hasOutput(c) ? 2 : 1);
function sortCells(cells: ApiSvampCell[]): ApiSvampCell[] {
  return [...cells].sort((a, b) => {
    if (rank(b) !== rank(a)) return rank(b) - rank(a);
    if ((b.supply || 0) !== (a.supply || 0)) return (b.supply || 0) - (a.supply || 0);
    return (b.gap || 0) - (a.gap || 0);
  });
}
function topTaughtSoc(c: ApiSvampCollege | undefined): string | null {
  if (!c) return null;
  const first = sortCells(c.cells).find((x) => x.course_count > 0);
  return first ? first.soc_code : null;
}
const shortName = (name: string) => name.replace(/ Valley College$/, "").replace(/ College$/, "");
function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}
// hue (0–360), saturation & lightness (0–100) — used to keep non-lead program
// colors hue-distinct from the school brand color.
function hexToHsl(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16) / 255, g = parseInt(h.slice(2, 4), 16) / 255, b = parseInt(h.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let hue = 0;
  if (d) {
    if (max === r) hue = ((g - b) / d) % 6;
    else if (max === g) hue = (b - r) / d + 2;
    else hue = (r - g) / d + 4;
    hue = (hue * 60 + 360) % 360;
  }
  const l = (max + min) / 2;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  return [hue, s * 100, l * 100];
}
function hueDist(a: number, b: number): number { const x = Math.abs(a - b) % 360; return x > 180 ? 360 - x : x; }
const Dot = () => <span style={{ color: "rgba(255,255,255,0.25)", margin: "0 8px" }}>·</span>;

// Distinct line/band colors for non-lead programs, in preference order (gold
// first — a strong hue distinct from most school brands). At render time this
// palette is filtered to drop any hue too close to the school's brand color, so
// a non-lead program never reads as the brand.
const OVERLAY_COLORS = ["#c9a84c", "#5ab0c4", "#7bd88f", "#b483f0", "#f0915a", "#67c2c9", "#e85d8a", "#e0654f", "#9aa6bd"];

// "Winter 2021" -> { season: "Wi", year: "2021" } for the two-tier enrollment
// axis: a compact season label under every term, the year grouped beneath.
const SEASON_ABBR: Record<string, string> = { Winter: "Wi", Spring: "Sp", Summer: "Su", Fall: "Fa" };
function parseTerm(t: string): { season: string; year: string } {
  const [season, year] = t.split(" ");
  return { season: SEASON_ABBR[season] ?? (season ?? "").slice(0, 2), year: year ?? "" };
}

// Edge-safe text anchor: the leftmost/rightmost slots anchor inward so their
// value/term labels never spill past the chart's plot area.
function edgeAnchor(i: number, n: number): "start" | "middle" | "end" {
  if (i === 0) return "start";
  if (i === n - 1) return "end";
  return "middle";
}

// Shared plot geometry for the two SVAMP trend charts (enrollment lines + award
// areas) so their sizing, axes, and hover chips stay identical.
const PLOT = { W: 760, H: 256, padL: 34, padR: 14, padT: 18, padB: 26 };

// A value chip floated above a point — its own dark pill (program-colored
// border, bold mono) so the number reads clearly and never sits on a trend
// line. Clamped to the plot so edge chips don't spill past the axes. Shared by
// both charts; draw it in a final pass so it lands on top of every series.
// A value chip centered at (cx, cy) — its own dark pill so the number reads
// clearly. The caller decides cy (it staggers chips across two rows to fit a
// number on every term without overlap); cx is clamped to the plot.
function valueChip(cx: number, cy: number, v: number, color: string, key: number) {
  const { W, padL, padR } = PLOT;
  const txt = v.toLocaleString("en-US");
  const w = 13 + txt.length * 6.8, h = 17;
  const x = Math.min(Math.max(cx, padL + w / 2), W - padR - w / 2);
  return (
    <g key={key} style={{ pointerEvents: "none" }}>
      <rect x={x - w / 2} y={cy - h / 2} width={w} height={h} rx={4} fill="#0b1530" stroke={color} strokeWidth={1} />
      <text x={x} y={cy + 4} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 11.5, fontWeight: 600, fill: "#ffffff" }}>{txt}</text>
    </g>
  );
}

function chipWidth(v: number): number { return 13 + v.toLocaleString("en-US").length * 6.8; }

// Collision-aware chip placement: a value on every point, each defaulting just
// above its point and bumped to the opposite side only if it would overlap the
// previous chip — robust to the line's slope (a fixed above/below stagger isn't,
// since a rising line can re-align the two rows). Returns a center-y per point,
// clamped to [minY, maxY].
function placeChipYs(pts: { x: number; y: number; v: number }[], minY: number, maxY: number): number[] {
  const ys: number[] = [];
  const gapV = 19;
  let prev: { x: number; y: number; w: number } | null = null;
  for (const p of pts) {
    const w = chipWidth(p.v);
    let cy = p.y - 16;
    if (prev && Math.abs(p.x - prev.x) < (w + prev.w) / 2 + 4 && Math.abs(cy - prev.y) < gapV) {
      cy = p.y + 16;
      if (Math.abs(cy - prev.y) < gapV) cy = prev.y + gapV;
    }
    cy = Math.min(Math.max(cy, minY), maxY);
    ys.push(cy);
    prev = { x: p.x, y: cy, w };
  }
  return ys;
}

function awardYearLabel(y: string): string {
  const m = y.match(/(\d{4})\D+(\d{4})/);
  return m ? `${m[1].slice(2)}–${m[2].slice(2)}` : y;
}

// Gridline step that reads cleanly across both magnitudes — enrollment volume
// (hundreds–thousands, esp. stacked) and award counts (tens–hundreds).
function niceStep(max: number): number {
  if (max > 2000) return 500;
  if (max > 800) return 200;
  if (max > 300) return 100;
  if (max > 150) return 50;
  if (max > 60) return 20;
  if (max > 30) return 10;
  return 5;
}

// ── Shared trend chart: per-program lines ↔ stacked area ───────────────────
// One chart for both Program Enrollments and Program Awards, with a mode the
// user toggles:
//   • "lines"   — each program a line on a shared axis: individual trajectory
//                 and relative size. Nulls are gaps, drawn through. (Default
//                 for enrollment.)
//   • "stacked" — programs stacked so total output reads at the top edge:
//                 throughput and mix. Nulls count as 0. (Default for awards.)
// Color is keyed to the program's position in the cell, so a program keeps one
// hue across both charts and both modes. Hover a program (legend, line, or
// band) to focus it; its per-slot values appear as chips above the points.
// Leading/trailing columns no program reports are trimmed (calendars differ).
type TrendSeries = { top6: string; name: string; vals: (number | null)[] };

// Sentinel hover value for the stacked "Total" trend (the summed top edge),
// distinct from any program's index.
const TOTAL_FOCUS = -1;

function TrendChart({ series, labels, defaultMode, colorOf, axisStyle = "thinned" }: { series: TrendSeries[]; labels: string[]; defaultMode: "lines" | "stacked"; colorOf: (top6: string) => string; axisStyle?: "thinned" | "twoTier" }) {
  const [mode, setMode] = useState<"lines" | "stacked">(defaultMode);
  const [hover, setHover] = useState<number | null>(null);
  const { W, padL, padR, padT } = PLOT;
  // The two-tier axis (season row + year row) needs extra room below the plot;
  // adding it to both H and padB keeps the plot height identical to single-tier.
  const twoTier = axisStyle === "twoTier";
  const H = PLOT.H + (twoTier ? 20 : 0);
  const padB = PLOT.padB + (twoTier ? 20 : 0);
  const base = H - padB, top = padT;

  const L = labels.length;
  // Programs with any data, carrying original index (→ stable color).
  const shownAll = series
    .map((s, idx) => ({ s, idx }))
    .filter((it) => it.s.vals.some((v) => v != null && v > 0));
  if (!shownAll.length) return null;
  // Keep only columns ≥1 shown program reports — drops not just the empty
  // boundary terms but every term the displayed college never runs (e.g. a
  // semester college's Winter terms), so the axis fits the calendar shown.
  const cols: number[] = [];
  for (let i = 0; i < L; i++) if (shownAll.some((it) => it.s.vals[i] != null)) cols.push(i);
  if (!cols.length) return null;
  const n = cols.length;
  const shown = shownAll.map((it) => ({ s: it.s, idx: it.idx, vals: cols.map((c) => it.s.vals[c]) }));

  const X = (k: number) => (n === 1 ? (padL + W - padR) / 2 : padL + (k / (n - 1)) * (W - padL - padR));

  const lineMax = Math.max(...shown.flatMap((it) => it.vals.filter((v): v is number => v != null)));
  const totals = cols.map((_, k) => shown.reduce((sum, it) => sum + (it.vals[k] ?? 0), 0));
  const stackMax = Math.max(...totals, 1);
  const dataMax = mode === "stacked" ? stackMax : lineMax;
  const step = niceStep(dataMax);
  const axisMax = Math.ceil(dataMax / step) * step;
  const Y = (v: number) => base - (v / axisMax) * (base - top);
  const ticks: number[] = [];
  for (let t = step; t <= axisMax; t += step) ticks.push(t);

  // Stacked geometry (largest-total at the base for a stable footing).
  const ordered = mode === "stacked"
    ? [...shown].sort((a, b) =>
        b.vals.reduce((s: number, v) => s + (v ?? 0), 0) - a.vals.reduce((s: number, v) => s + (v ?? 0), 0))
    : shown;
  const acc = cols.map(() => 0);
  const bands = ordered.map((it) => {
    const color = colorOf(it.s.top6);
    const loY = acc.slice();
    const hiY = cols.map((_, k) => loY[k] + (it.vals[k] ?? 0));
    for (let k = 0; k < n; k++) acc[k] = hiY[k];
    return { it, color, loY, hiY };
  });
  const single = n === 1;
  const barW = Math.min(72, (W - padL - padR) * 0.5);
  const focused = hover != null ? shown.find((it) => it.idx === hover) : undefined;

  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
        <div style={{ display: "inline-flex", border: "1px solid rgba(255,255,255,.12)", borderRadius: 8, overflow: "hidden" }}>
          {(["lines", "stacked"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{ appearance: "none", border: "none", cursor: "pointer", background: mode === m ? "rgba(255,255,255,.1)" : "transparent", color: mode === m ? "#e8ecf4" : "#9aa6bd", fontFamily: FONT, fontSize: 11.5, fontWeight: 500, padding: "5px 12px", transition: "background .12s, color .12s" }}
            >
              {m === "lines" ? "Per program" : "Stacked"}
            </button>
          ))}
        </div>
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke="rgba(255,255,255,.1)" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={padL} x2={W - padR} y1={Y(t)} y2={Y(t)} stroke="rgba(255,255,255,.05)" />
            <text x={padL - 6} y={Y(t) + 3} textAnchor="end" style={{ fontFamily: MONO, fontSize: 9, fill: "#5e6a83" }}>{t.toLocaleString("en-US")}</text>
          </g>
        ))}

        {mode === "lines"
          ? shown.map((it) => {
              const color = colorOf(it.s.top6);
              const on = hover === it.idx, faded = hover != null && !on;
              const pts: { x: number; y: number; k: number }[] = [];
              it.vals.forEach((v, k) => { if (v != null) pts.push({ x: X(k), y: Y(v), k }); });
              if (!pts.length) return null;
              const path = pts.map((q, j) => (j ? "L" : "M") + q.x.toFixed(1) + " " + q.y.toFixed(1)).join(" ");
              const lastPt = pts[pts.length - 1];
              return (
                <g key={it.s.top6}>
                  <path d={path} fill="none" stroke={color} strokeWidth={on ? 3 : 2} strokeLinejoin="round" strokeLinecap="round" opacity={faded ? 0.12 : on ? 1 : 0.82} />
                  {on
                    ? pts.map((q) => <circle key={q.k} cx={q.x} cy={q.y} r={3} fill={color} />)
                    : hover == null && <circle cx={lastPt.x} cy={lastPt.y} r={2.4} fill={color} />}
                  {/* invisible wide hit area so the thin line itself is hoverable */}
                  <path d={path} fill="none" stroke="transparent" strokeWidth={14} style={{ pointerEvents: "stroke", cursor: "pointer" }} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)} />
                </g>
              );
            })
          : bands.map(({ it, color, loY, hiY }) => {
              const on = hover === it.idx, faded = hover != null && !on;
              let shape: React.ReactNode;
              if (single) {
                const x = X(0) - barW / 2;
                shape = <rect x={x} y={Y(hiY[0])} width={barW} height={Math.max(0, Y(loY[0]) - Y(hiY[0]))} fill={color} opacity={faded ? 0.12 : on ? 0.72 : 0.5} />;
              } else {
                const up = cols.map((_, k) => `${k ? "L" : "M"}${X(k).toFixed(1)} ${Y(hiY[k]).toFixed(1)}`).join(" ");
                const down = cols.map((_, k) => n - 1 - k).map((k) => `L${X(k).toFixed(1)} ${Y(loY[k]).toFixed(1)}`).join(" ");
                shape = (
                  <>
                    <path d={`${up} ${down} Z`} fill={color} opacity={faded ? 0.12 : on ? 0.62 : 0.4} stroke="none" />
                    <path d={up} fill="none" stroke={color} strokeWidth={on ? 2.4 : 1.4} strokeLinejoin="round" opacity={faded ? 0.2 : 1} />
                  </>
                );
              }
              return (
                <g key={it.s.top6} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)} style={{ cursor: "pointer" }}>
                  {shape}
                </g>
              );
            })}

        {/* Stacked "Total": the summed trend along the top edge with its own
            value chips — focusable from the legend's Total row. */}
        {mode === "stacked" && hover === TOTAL_FOCUS && !single && (
          <path
            d={cols.map((_, k) => `${k ? "L" : "M"}${X(k).toFixed(1)} ${Y(totals[k]).toFixed(1)}`).join(" ")}
            fill="none" stroke="#e8ecf4" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round"
          />
        )}
        {mode === "stacked" && hover === TOTAL_FOCUS && (() => {
          const pts = totals.map((tv, k) => ({ x: X(k), y: Y(tv), v: tv })).filter((p) => p.v > 0);
          const ys = placeChipYs(pts, top + 9, base - 9);
          return <g>{pts.map((p, i) => valueChip(p.x, ys[i], p.v, "#e8ecf4", i))}</g>;
        })()}
        {/* Focused program: a value on every term, placed just above its point
            and bumped to the other side only if it would overlap its neighbor,
            so all show without colliding. Drawn last, on top of every series. */}
        {focused && (() => {
          const color = colorOf(focused.s.top6);
          const pts: { x: number; y: number; v: number }[] = [];
          if (mode === "lines") {
            focused.vals.forEach((v, k) => { if (v != null) pts.push({ x: X(k), y: Y(v), v }); });
          } else {
            const b = bands.find((x) => x.it.idx === focused.idx);
            if (!b) return null;
            b.hiY.forEach((hv, k) => { if ((b.it.vals[k] ?? 0) > 0) pts.push({ x: X(k), y: Y(hv), v: b.it.vals[k] as number }); });
          }
          const ys = placeChipYs(pts, top + 9, base - 9);
          return <g>{pts.map((p, i) => valueChip(p.x, ys[i], p.v, color, i))}</g>;
        })()}

        {twoTier ? (() => {
          // Two-tier axis: a compact season label under every term, the year
          // grouped beneath with faint dividers — names every term without
          // crowding, so a focused program's per-term numbers all read off it.
          const parsed = cols.map((c) => parseTerm(labels[c]));
          const seasonEls = parsed.map((p, k) => (
            <g key={`s${k}`}>
              <line x1={X(k)} x2={X(k)} y1={base} y2={base + 3} stroke="rgba(255,255,255,.12)" />
              <text x={X(k)} y={base + 14} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 8.5, fill: "#5e6a83" }}>{p.season}</text>
            </g>
          ));
          const groups: { year: string; ks: number[] }[] = [];
          parsed.forEach((p, k) => {
            const last = groups[groups.length - 1];
            if (last && last.year === p.year) last.ks.push(k);
            else groups.push({ year: p.year, ks: [k] });
          });
          const yearEls = groups.map((g, gi) => {
            const cx = g.ks.reduce((a, b) => a + X(b), 0) / g.ks.length;
            const lx = Math.min(Math.max(cx, padL + 16), W - padR - 16);
            return (
              <g key={`y${gi}`}>
                {gi > 0 && <line x1={(X(g.ks[0]) + X(g.ks[0] - 1)) / 2} x2={(X(g.ks[0]) + X(g.ks[0] - 1)) / 2} y1={top} y2={base + 34} stroke="rgba(255,255,255,.13)" />}
                <text x={lx} y={base + 33} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10.5, fill: "#9aa6bd" }}>{g.year}</text>
              </g>
            );
          });
          return <>{seasonEls}{yearEls}</>;
        })() : (() => {
          // Thin labels so a long axis never crowds: show at most ~12, always
          // including the last term.
          const stride = Math.ceil(n / 12);
          return cols.map((c, k) => ((k % stride === 0 || k === n - 1) ? (
            <text key={c} x={X(k)} y={H - 8} textAnchor={n === 1 ? "middle" : edgeAnchor(k, n)} style={{ fontFamily: MONO, fontSize: 9.5, fill: "#5e6a83" }}>{labels[c]}</text>
          ) : null));
        })()}
      </svg>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", marginTop: 12 }}>
        {mode === "stacked" && (() => {
          const ton = hover === TOTAL_FOCUS, tdim = hover != null && hover !== TOTAL_FOCUS;
          return (
            <div onMouseEnter={() => setHover(TOTAL_FOCUS)} onMouseLeave={() => setHover(null)}
              style={{ gridColumn: "1 / -1", display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, background: ton ? "rgba(255,255,255,.07)" : "transparent", opacity: tdim ? 0.45 : 1, transition: "background .12s, opacity .12s", minWidth: 0 }}>
              <span style={{ width: 16, height: 3, borderRadius: 2, background: "#e8ecf4", flex: "none" }} />
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#e8ecf4", fontWeight: 500 }}>Total</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#5e6a83", flex: "none" }}>{totals[n - 1].toLocaleString("en-US")}</span>
            </div>
          );
        })()}
        {shown.map((it) => {
          const color = colorOf(it.s.top6);
          const on = hover === it.idx, dim = hover != null && !on;
          return (
            <div key={it.s.top6} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)}
              style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, background: on ? "rgba(255,255,255,.07)" : "transparent", opacity: dim ? 0.45 : 1, transition: "background .12s, opacity .12s", minWidth: 0 }}>
              <span style={{ width: 16, height: mode === "stacked" ? 10 : 3, borderRadius: mode === "stacked" ? 3 : 2, background: color, opacity: mode === "stacked" ? 0.62 : 1, flex: "none" }} />
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#9aa6bd" }}>{it.s.name}</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#5e6a83", flex: "none" }}>TOP {it.s.top6}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Program wage outcomes (dumbbell) ──────────────────────────────────────
// Median earnings for completers of each feeder program at three checkpoints
// relative to award completion (2 yrs before / 2 after / 5 after), pooled
// STATEWIDE at the TOP6 grain by credential type — not college-specific, and
// not a time series. Each row is one cohort: a track from the before-wage to
// the 5-year wage (the gap is the lift), the three stages color-coded and
// keyed; ranked by 5-year earnings. The before / 5-year figures are labeled
// inline so the lift survives a screenshot; +2yr shows on hover. Stages are a
// single-hue intensity ramp of the school's brand color (faded → full), so the
// 5-year outcome lands in the full brand color and the ramp itself reads as the
// climb — branding the panel per school the way the rest of the report is.

function wageRecipientLabel(rt: string): string {
  if (/Associate or Bacc/i.test(rt)) return "Degree";
  if (/Chancellor.?s Office/i.test(rt)) return "CO Cert";
  if (/Locally Approved/i.test(rt)) return "Local Cert";
  return rt.replace(/\s*Recipient\s*$/i, "");
}
// Fixed credential order so the rows read consistently across every program.
const WAGE_RT_RANK: Record<string, number> = { "Degree": 0, "CO Cert": 1, "Local Cert": 2 };

type WageCohort = { rt: string; before: number; after2: number | null; after5: number; n: number | null };
type WageGroup = { name: string; top6: string; cohorts: WageCohort[] };

function WageOutcomes({ programs, brandColor }: { programs: ApiSvampProgram[]; brandColor: string }) {
  // Group by program; each program heads a block, its credential cohorts beneath
  // (ranked by 5-year wage). Programs ordered by their best 5-year outcome.
  const groups: WageGroup[] = programs
    .map((p) => ({
      name: p.name,
      top6: p.top6,
      cohorts: (p.wages ?? [])
        .filter((w) => w.wage_before != null && w.wage_after_5 != null)
        .map((w) => ({
          rt: wageRecipientLabel(w.recipient_type),
          before: w.wage_before as number,
          after2: w.wage_after_2,
          after5: w.wage_after_5 as number,
          n: w.n,
        }))
        .sort((a, b) => (WAGE_RT_RANK[a.rt] ?? 9) - (WAGE_RT_RANK[b.rt] ?? 9)),
    }))
    .filter((g) => g.cohorts.length > 0)
    .sort((a, b) =>
      Math.max(...b.cohorts.map((c) => c.after5)) - Math.max(...a.cohorts.map((c) => c.after5)));
  if (!groups.length) return null;

  const fmtK = (v: number) => "$" + Math.round(v / 1000) + "k";
  const wageWindow = programs.flatMap((p) => p.wages ?? []).find((w) => w.window)?.window ?? "";
  const maxVal = Math.max(...groups.flatMap((g) => g.cohorts.flatMap((c) => [c.before, c.after2 ?? 0, c.after5])));
  const step = 20000;
  const axisMax = Math.max(step, Math.ceil(maxVal / step) * step);
  const W = 760, plotL = 126, padR = 16, padT = 10, headerH = 38, rowH = 34, gap = 20, axisH = 30;
  let H = padT;
  groups.forEach((g) => { H += headerH + g.cohorts.length * rowH + gap; });
  H += axisH;
  const axisY = H - axisH + 6;
  const X = (w: number) => plotL + (w / axisMax) * (W - plotL - padR);
  const ticks: number[] = [];
  for (let t = 0; t <= axisMax; t += step) ticks.push(t);
  // Stage ramp: faded brand → full brand (the 5-year destination). Accent only
  // on the data; chrome (TOP code, labels, axis) stays neutral.
  const stageB = hexA(brandColor, 0.5), stageA2 = hexA(brandColor, 0.72);
  const stageKey: [string, string, number][] = [
    ["2 yrs before award", stageB, 11], ["2 yrs after", stageA2, 11], ["5 yrs after", brandColor, 13],
  ];

  const els: React.ReactNode[] = [];
  let y = padT;
  groups.forEach((g, gi) => {
    els.push(
      <g key={`h${gi}`}>
        <text x={2} y={y + 15} style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, fill: "#e8ecf4" }}>
          {g.name}
          <tspan dx={9} style={{ fontWeight: 400, fill: "rgba(255,255,255,0.25)" }}>·</tspan>
          <tspan dx={7} style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.03em", fill: "#8893ab" }}>TOP {g.top6}</tspan>
        </text>
        <line x1={2} x2={W - padR} y1={y + 24} y2={y + 24} stroke="rgba(255,255,255,.08)" />
      </g>,
    );
    y += headerH;
    g.cohorts.forEach((c, ci) => {
      const cy = y + rowH / 2;
      // 5-year value sits right of its dot, but flips to the left if the dot is
      // so far right the label would overflow the chart.
      const a5x = X(c.after5);
      const a5lbl = fmtK(c.after5);
      const a5flip = a5x + 12 + a5lbl.length * 7 + 6 > W;
      els.push(
        <g key={`r${gi}-${ci}`}>
          <text x={16} y={cy + 4} style={{ fontFamily: FONT, fontSize: 12.5, fill: "#9aa6bd" }}>
            {c.rt}
            <tspan style={{ fontFamily: MONO, fontSize: 10, fill: "#5e6a83" }}>{c.n != null ? ` · n=${c.n}` : ""}</tspan>
          </text>
          <line x1={X(c.before)} x2={X(c.after5)} y1={cy} y2={cy} stroke={hexA(brandColor, 0.28)} strokeWidth={3} strokeLinecap="round" />
          <circle cx={X(c.before)} cy={cy} r={4} fill={stageB} />
          {c.after2 != null && <circle cx={X(c.after2)} cy={cy} r={4} fill={stageA2} />}
          <circle cx={X(c.after5)} cy={cy} r={6.5} fill={brandColor} stroke="#060d1f" strokeWidth={1.5} />
          <text x={X(c.before) - 10} y={cy + 4} textAnchor="end" style={{ fontFamily: MONO, fontSize: 10, fill: hexA(brandColor, 0.8) }}>{fmtK(c.before)}</text>
          {c.after2 != null && <text x={X(c.after2)} y={cy - 11} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 9.5, fill: hexA(brandColor, 0.7) }}>{fmtK(c.after2)}</text>}
          <text x={a5flip ? a5x - 11 : a5x + 12} y={cy + 4} textAnchor={a5flip ? "end" : "start"} style={{ fontFamily: MONO, fontSize: 12, fontWeight: 500, fill: brandColor }}>{a5lbl}</text>
        </g>,
      );
      y += rowH;
    });
    y += gap;
  });

  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: "flex", gap: 18, flexWrap: "wrap", justifyContent: "flex-end", paddingRight: `${(padR / W) * 100}%`, fontSize: 12, color: "#9aa6bd", marginBottom: 12 }}>
        {stageKey.map(([lbl, col, sz]) => (
          <span key={lbl} style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
            <span style={{ width: sz, height: sz, borderRadius: "50%", background: col, display: "inline-block" }} />
            {lbl}
          </span>
        ))}
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        {els}
        {/* Clean bottom axis — baseline + short ticks, no full-height gridlines
            (which used to strike through the program headers). */}
        <line x1={plotL} x2={W - padR} y1={axisY} y2={axisY} stroke="rgba(255,255,255,.1)" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={X(t)} x2={X(t)} y1={axisY} y2={axisY + 4} stroke="rgba(255,255,255,.18)" />
            <text x={X(t)} y={axisY + 16} textAnchor={t === 0 ? "start" : t === axisMax ? "end" : "middle"} style={{ fontFamily: MONO, fontSize: 9, fill: "#5e6a83" }}>{fmtK(t)}</text>
          </g>
        ))}
      </svg>
      <div style={{ fontSize: 11, color: "#5e6a83", marginTop: 12, lineHeight: 1.6 }}>
        Degree = Associate or Baccalaureate Degree; CO Cert = Chancellor&apos;s Office Approved Certificate; Local Cert = Locally Approved Certificate; n = Total Awards{wageWindow ? ` ${wageWindow}` : ""}.
      </div>
    </div>
  );
}

// ── Demand composition hero (treemap) ─────────────────────────────────────
// Squarified treemap: area = annual openings, so the rectangle is the regional
// total. Cells label the SOC code + openings (the full title is surfaced in the
// readout on hover) — compact and visual rather than prose-in-cell.
function squarify(values: number[], X: number, Y: number, W: number, H: number): { x: number; y: number; w: number; h: number }[] {
  const sum = values.reduce((a, b) => a + b, 0) || 1;
  const areas = values.map((v) => (v * W * H) / sum);
  const rects: { x: number; y: number; w: number; h: number }[] = new Array(values.length);
  let x = X, y = Y, w = W, h = H, i = 0;
  while (i < areas.length) {
    const side = Math.min(w, h), start = i;
    const row = [areas[i]]; i++;
    const worst = (r: number[]) => {
      const s = r.reduce((a, b) => a + b, 0), mx = Math.max(...r), mn = Math.min(...r), s2 = s * s, d2 = side * side;
      return Math.max((d2 * mx) / s2, s2 / (d2 * mn));
    };
    while (i < areas.length && worst([...row, areas[i]]) <= worst(row)) { row.push(areas[i]); i++; }
    const rs = row.reduce((a, b) => a + b, 0), thick = rs / side;
    if (w >= h) { let yy = y; row.forEach((a, k) => { const ch = a / thick; rects[start + k] = { x, y: yy, w: thick, h: ch }; yy += ch; }); x += thick; w -= thick; }
    else { let xx = x; row.forEach((a, k) => { const cw = a / thick; rects[start + k] = { x: xx, y, w: cw, h: thick }; xx += cw; }); y += thick; h -= thick; }
  }
  return rects;
}

function DemandTreemap({ cells, total }: { cells: ApiSvampCell[]; total: number }) {
  const [hover, setHover] = useState<{ i: number; x: number; y: number } | null>(null);
  const data = cells
    .filter((c) => (c.annual_openings ?? 0) > 0)
    .map((c) => ({ soc: c.soc_code, title: c.title, op: c.annual_openings as number }))
    .sort((a, b) => b.op - a.op);
  if (!data.length) return null;
  const W = 860, H = 300, g = 2;
  const rects = squarify(data.map((d) => d.op), 0, 0, W, H);
  const color = (i: number) => hexA(ACCENT, 1 - (i / Math.max(data.length - 1, 1)) * 0.62);
  const hd = hover != null ? data[hover.i] : null;
  const top3 = data.slice(0, 3);
  const top3sh = Math.round((top3.reduce((s, d) => s + d.op, 0) / total) * 100);
  return (
    <div style={{ marginTop: 16 }}>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ display: "block", height: H }} onMouseLeave={() => setHover(null)}>
        {data.map((d, i) => {
          const r = rects[i];
          return (
            <g key={d.soc} onMouseMove={(e) => setHover({ i, x: e.clientX, y: e.clientY })} style={{ cursor: "default" }}>
              <rect x={r.x + g / 2} y={r.y + g / 2} width={Math.max(r.w - g, 0)} height={Math.max(r.h - g, 0)} rx={3} fill={color(i)} opacity={hover != null && hover.i !== i ? 0.4 : 1} />
              {(() => {
                // Adaptive label: font scales to the cell so every cell can carry
                // "SOC <code>" + "<openings>/yr" without enlarging the whole chart.
                // The widest line ("SOC 49-9041") sets the size; very narrow cells
                // drop the "SOC " prefix before the font hits its floor.
                const pad = 8, cw = 0.6; // cw ≈ mono char-width / em
                const availW = r.w - 2 * pad;
                if (availW < 22 || r.h < 18) return null;
                const full = `SOC ${d.soc}`;
                const label = availW / (full.length * cw) >= 7 ? full : d.soc;
                const fs = Math.max(7, Math.min(11.5, availW / (label.length * cw)));
                const lh = fs + 3;
                const two = r.h >= 2 * lh + 4;
                return (
                  <g style={{ pointerEvents: "none" }}>
                    <text x={r.x + pad} y={r.y + pad + fs - 1} style={{ fontFamily: MONO, fontSize: fs, fontWeight: 500, fill: "#fff" }}>{label}</text>
                    {two && <text x={r.x + pad} y={r.y + pad + fs - 1 + lh} style={{ fontFamily: MONO, fontSize: Math.max(fs - 1, 6.5), fill: "rgba(255,255,255,.82)" }}>{d.op}/yr</text>}
                  </g>
                );
              })()}
            </g>
          );
        })}
      </svg>
      <div style={{ fontFamily: FONT, fontSize: 12.5, color: "#9aa6bd", marginTop: 10 }}>
        Area is annual openings. The top three occupations account for <span style={{ color: "#e8ecf4", fontWeight: 600 }}>{top3sh}%</span> of regional demand — hover a cell for the occupation.
      </div>
      {/* Floating tooltip, portaled to <body> so position:fixed escapes the
          transformed overlay ancestor and tracks the cursor in viewport space. */}
      {hd && hover && typeof document !== "undefined" && createPortal(
        <div style={{
          position: "fixed", left: Math.min(hover.x + 14, window.innerWidth - 356), top: hover.y + 14,
          pointerEvents: "none", zIndex: 1000, maxWidth: 340,
          background: "#0b1530", border: "1px solid rgba(255,255,255,.09)", borderRadius: 8,
          padding: "8px 11px", boxShadow: "0 6px 24px rgba(0,0,0,.4)", fontFamily: FONT,
        }}>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: "#e8ecf4", marginBottom: 2 }}>{hd.title}</div>
          <div style={{ fontFamily: MONO, fontSize: 11, color: ACCENT, whiteSpace: "nowrap" }}>SOC {hd.soc} · {hd.op.toLocaleString()} openings/yr · {Math.round((hd.op / total) * 100)}% of demand</div>
        </div>,
        document.body,
      )}
    </div>
  );
}

export default function SvampView({ colleges, onBack }: Props) {
  const [data, setData] = useState<ApiSvampLandscape | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>(colleges[0]?.id ?? "");
  const [selectedSoc, setSelectedSoc] = useState<string | null>(null);
  // Sticky context banner: shown once the report header scrolls under the nav.
  const [ctxShow, setCtxShow] = useState(false);
  const ctxSentinel = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getSvampLandscape().then(setData).catch((e) => setError(e.message));
  }, []);

  // Reveal the context banner when the sentinel (at the report's top) passes
  // under the 72px nav, hide it again on scroll back up.
  useEffect(() => {
    const el = ctxSentinel.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => setCtxShow(e.boundingClientRect.top < 72),
      { rootMargin: "-72px 0px 0px 0px", threshold: 0 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [selectedSoc]);

  const byName = useMemo(() => {
    const m = new Map<string, CollegeRef>();
    colleges.forEach((c) => m.set(c.config.name, c));
    return m;
  }, [colleges]);

  // Auto-select the default college's strongest occupation once data lands.
  useEffect(() => {
    if (!data) return;
    const def = data.colleges.find((c) => byName.get(c.name)?.id === selected) ?? data.colleges[0];
    setSelectedSoc(topTaughtSoc(def));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const wrap = (children: React.ReactNode) => (
    <div style={{ minHeight: "100vh", background: "#060d1f", color: "#e8ecf4", fontFamily: FONT }}>
      <AtlasHeader title="Silicon Valley Advanced Manufacturing Partnership" onBack={onBack} rightSlot={<KallipolisBrand />} position="sticky" cubeTint={ACCENT} showPreview titleSize="15px" />
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 28px 90px" }}>{children}</div>
    </div>
  );

  if (error) {
    return wrap(<div style={{ padding: "80px 0", color: GAP, fontFamily: MONO, fontSize: 13 }}>Failed to load: {error}</div>);
  }
  if (!data) {
    return wrap(
      <div style={{ display: "flex", justifyContent: "center", padding: "120px 0" }}>
        <RisingSun style={{ width: 64, height: "auto" }} />
      </div>,
    );
  }

  const agg = data.aggregate;
  const selCollege: ApiSvampCollege | undefined =
    data.colleges.find((c) => byName.get(c.name)?.id === selected) ?? data.colleges[0];
  const selRef = selCollege ? byName.get(selCollege.name) : undefined;
  const selBrand = selRef?.config.brandColorLight ?? ACCENT;
  const selectedCell = selCollege?.cells.find((c) => c.soc_code === selectedSoc);
  // Gap selection: the college teaches none of this SOC's crosswalk. The detail
  // collapses to the Curriculum Alignment crosswalk — supply/demand projections
  // (hollow at zero supply) and Partnership Opportunities (no program to anchor)
  // are suppressed.
  const isGapSel = level(selectedCell) === "none";

  // SVAMP-owned Program Outcomes panel — injected into the embedded report
  // between Curriculum Alignment and Student Impact via OpportunityReportBody's
  // `programOutcomes` slot (so it reads as a peer report section without
  // touching the shared per-college report). Null when the selection has no
  // DataMart program data.
  const hasAwards =
    !!selectedCell &&
    data.award_years.length > 0 &&
    selectedCell.programs.some((p) => (p.awards ?? []).some((v) => v > 0));
  const hasWages =
    !!selectedCell &&
    selectedCell.programs.some((p) => (p.wages ?? []).some((w) => w.wage_before != null && w.wage_after_5 != null));
  const wageWindow =
    selectedCell?.programs.flatMap((p) => p.wages ?? []).find((w) => w.window)?.window ?? "";
  const awardsWindow = data.award_years.length
    ? `${data.award_years[0]} to ${data.award_years[data.award_years.length - 1]}`
    : "";

  // One shared color per program for the whole cell, so a program reads as the
  // same color in BOTH the enrollment and award charts. One program is the
  // "lead" and takes the school brand in both — chosen, where possible, among
  // programs present in both charts (so the brand is guaranteed to appear in
  // each) and the most prominent across them; every other program keeps a
  // stable palette hue by its position in the cell.
  const cellPrograms = selectedCell?.programs ?? [];
  const enrollTotal = (p: ApiSvampProgram) => (p.enrollment ?? []).reduce((s: number, v) => s + (v ?? 0), 0);
  const awardTotal = (p: ApiSvampProgram) => (p.awards ?? []).reduce((s: number, v) => s + (v ?? 0), 0);
  const sumE = cellPrograms.reduce((s, p) => s + enrollTotal(p), 0) || 1;
  const sumA = cellPrograms.reduce((s, p) => s + awardTotal(p), 0) || 1;
  const prominence = (p: ApiSvampProgram) => enrollTotal(p) / sumE + awardTotal(p) / sumA;
  const inBoth = cellPrograms.filter((p) => enrollTotal(p) > 0 && awardTotal(p) > 0);
  const leadPool = inBoth.length ? inBoth : cellPrograms;
  const lead = leadPool.reduce<ApiSvampProgram | null>(
    (best, p) => (best && prominence(best) >= prominence(p) ? best : p), null);
  // Non-lead programs draw from the palette filtered to hues clearly distinct
  // from the brand (so none mimics it), assigned in cell order.
  const [bh, bs] = hexToHsl(selBrand);
  const distinct = bs < 25
    ? OVERLAY_COLORS
    : OVERLAY_COLORS.filter((c) => { const [ch, cs] = hexToHsl(c); return cs < 25 || hueDist(ch, bh) >= 40; });
  const palette = distinct.length ? distinct : OVERLAY_COLORS;
  const programColor = new Map<string, string>();
  let pi = 0;
  cellPrograms.forEach((p) => {
    programColor.set(p.top6, p.top6 === lead?.top6 ? selBrand : palette[pi++ % palette.length]);
  });
  const colorOf = (top6: string) => programColor.get(top6) ?? palette[0];
  const programOutcomesPanel =
    selectedCell && selectedCell.programs.length > 0 && selRef ? (
      <>
        <Section title="Program Enrollments" brandColor={selBrand}>
          <Prose>
            Term-by-term enrollment for the {selRef.config.name} programs that prepare students for this occupation, excluding the structurally-low summer terms. Toggle between per-program trends and the combined total; hover a program to focus it.
          </Prose>
          <TrendChart
            series={selectedCell.programs.map((p) => ({ top6: p.top6, name: p.name, vals: p.enrollment }))}
            labels={data.enrollment_terms}
            defaultMode="lines"
            colorOf={colorOf}
            axisStyle="twoTier"
          />
        </Section>
        {hasAwards ? (
          <Section title="Program Awards" brandColor={selBrand}>
            <Prose>
              Credentials conferred per year by those same programs. Toggle between the stacked total and per-program trends; hover a program to focus it.
            </Prose>
            <TrendChart
              series={selectedCell.programs.map((p) => ({ top6: p.top6, name: p.name, vals: p.awards ?? [] }))}
              labels={data.award_years.map(awardYearLabel)}
              defaultMode="stacked"
              colorOf={colorOf}
            />
          </Section>
        ) : (
          // No award rows exist for these (college, TOP) programs in the DataMart
          // export — the series would zero-fill, so we state the data absence
          // explicitly rather than render an empty chart or silently drop it.
          <Section title="Program Awards" brandColor={selBrand}>
            <Prose>
              No awards data is reported for these programs{awardsWindow ? ` over ${awardsWindow}` : ""} via CCCCO DataMart.
            </Prose>
          </Section>
        )}
        {hasWages && (
          <Section title="Program Wage Outcomes" brandColor={selBrand}>
            <Prose>
              Median annual earnings for completers of these programs at three points relative to award completion — 2 years before, 2 years after, and 5 years after. Derived from statewide data at the program (TOP6) level by credential type{wageWindow ? ` for award years ${wageWindow}` : ""}.
            </Prose>
            <WageOutcomes programs={selectedCell.programs} brandColor={selBrand} />
          </Section>
        )}
      </>
    ) : null;

  // Columns = member colleges (with a soc→cell map); rows = the 12 roles.
  const columns = colleges.map((ref) => {
    const c = data.colleges.find((x) => x.name === ref.config.name);
    return { ref, cellMap: new Map((c?.cells ?? []).map((cell) => [cell.soc_code, cell])) };
  });
  // Rows ranked by regional demand (descending) — one well-defined order since
  // demand is regional, and it matches the demand-sorted treemap above so the
  // highest-opportunity roles surface at the top of both views.
  const socRows = [...(data.colleges[0]?.cells ?? [])].sort(
    (a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0),
  );

  // Build the transposed coverage grid: roles (rows, English) × colleges (cols).
  const grid: React.ReactNode[] = [];
  grid.push(
    <div key="corner" style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: ".1em", textTransform: "uppercase", color: "#5e6a83", alignSelf: "end", paddingBottom: 6, whiteSpace: "nowrap" }}>↓ role (by demand) · → college</div>,
  );
  columns.forEach(({ ref }) => {
    const on = ref.id === selRef?.id;
    const cb = ref.config.brandColorLight;
    grid.push(
      <div key={"h-" + ref.id} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 11.5, fontWeight: 600, paddingBottom: 11, color: on ? cb : "#9aa6bd", boxShadow: on ? `inset 0 -2px 0 ${cb}` : "none", transition: "color .15s" }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: ref.config.brandColorLight, flex: "none" }} />
        {shortName(ref.config.name)}
      </div>,
    );
  });
  socRows.forEach((soc) => {
    const short = ROLE_LABEL[soc.soc_code] ?? soc.title;
    const rowSel = soc.soc_code === selectedSoc;
    // Stacked label: role name leads, SOC code rides beneath as provenance.
    grid.push(
      <div key={"r-" + soc.soc_code} title={soc.title} style={{ paddingRight: 14, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: rowSel ? 600 : 500, color: rowSel ? selBrand : "rgba(255,255,255,.82)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{rowSel ? "▸ " : ""}{short}</div>
        <div style={{ fontFamily: MONO, fontSize: 10, color: rowSel ? selBrand : "#5e6a83", letterSpacing: ".02em", marginTop: 1, opacity: rowSel ? 0.85 : 1, transition: "color .15s" }}>SOC {soc.soc_code}</div>
      </div>,
    );
    columns.forEach(({ ref, cellMap }) => {
      const cell = cellMap.get(soc.soc_code);
      const lv = level(cell);
      const key = ref.id + "-" + soc.soc_code;
      const brand = ref.config.brandColorLight;
      const isSel = ref.id === selRef?.id && soc.soc_code === selectedSoc;
      const isGap = lv === "none";
      // Gap cells are selectable too — they open the crosswalk-only view
      // ("0 of M TOP groups…"), useful for spotting build/partner opportunities.
      // They keep their faint resting look; brand fill is reserved for coverage.
      const gapBg = "rgba(255,255,255,.035)";
      const base: React.CSSProperties = {
        height: 32, borderRadius: 7, cursor: "pointer",
        background: isGap ? gapBg : lv === "strong" ? hexA(brand, 0.9) : hexA(brand, 0.3),
        boxShadow: isGap ? "none" : `inset 0 0 0 1px ${hexA(brand, 0.5)}`,
        transition: "transform .12s, box-shadow .12s, background .12s",
      };
      const sel: React.CSSProperties = isSel
        ? isGap
          ? { boxShadow: "0 0 0 2px rgba(255,255,255,.85), 0 6px 16px rgba(0,0,0,.5)", transform: "scale(1.08)", zIndex: 2 }
          : { boxShadow: `0 0 0 2px rgba(255,255,255,.92), 0 0 12px ${hexA(brand, 0.6)}, 0 6px 16px rgba(0,0,0,.5)`, transform: "scale(1.08)", zIndex: 2 }
        : {};
      grid.push(
        <div
          key={key}
          title={isGap ? `${shortName(ref.config.name)} · ${soc.title} — no aligned curriculum (view crosswalk)` : `${shortName(ref.config.name)} · ${soc.title}`}
          onClick={() => { setSelected(ref.id); setSelectedSoc(soc.soc_code); }}
          onMouseEnter={(e) => { if (isSel) return; const el = e.currentTarget as HTMLElement; el.style.transform = "translateY(-2px)"; if (isGap) el.style.background = "rgba(255,255,255,.08)"; }}
          onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; if (isGap) el.style.background = gapBg; if (!isSel) el.style.transform = "none"; }}
          style={{ ...base, ...sel }}
        />,
      );
    });
  });

  return wrap(
    <>
      {/* Sticky context banner — College · Occupation · SOC, pinned under the
          nav once the report header scrolls away, so the (college, occupation)
          identity stays visible deep in the report. Echoes the report eyebrow
          (accent college name) and meta (mono SOC code). */}
      {selectedCell && selRef && (
        <div
          style={{
            position: "fixed", top: 72, left: 0, right: 0, zIndex: 25, height: 46,
            background: "rgba(6,13,31,0.92)", backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            display: "flex", alignItems: "center",
            opacity: ctxShow ? 1 : 0,
            transform: ctxShow ? "translateY(0)" : "translateY(-8px)",
            pointerEvents: ctxShow ? "auto" : "none",
            transition: "opacity .22s ease, transform .22s ease",
          }}
        >
          <div style={{ maxWidth: 900, width: "100%", margin: "0 auto", padding: "0 28px", display: "flex", alignItems: "baseline", gap: 10, minWidth: 0 }}>
            <span style={{ fontFamily: FONT, fontSize: 11.5, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase", color: selBrand, flex: "none", whiteSpace: "nowrap" }}>
              {selRef.config.name}
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)", flex: "none" }}>·</span>
            <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.9)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {selectedCell.title}
            </span>
            <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.05em", color: hexA(selBrand, 0.65), flex: "none", whiteSpace: "nowrap" }}>
              SOC {selectedSoc}
            </span>
          </div>
        </div>
      )}
      {/* Report header — same magazine idiom as the per-occupation report */}
      <ReportHeader eyebrow="Partnership Landscape Report" title="Silicon Valley Advanced Manufacturing Partnership" accent={ACCENT}>
        <span style={{ color: ACCENT, opacity: 0.7 }}>{agg.n_colleges} Member Colleges</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{agg.n_occupations} Occupations</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)", letterSpacing: "0.08em" }}>{data.sector}</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{data.region_display}</span>
        {data.is_sector_priority && (
          <><Dot /><span style={{ color: ACCENT, letterSpacing: "0.1em", fontWeight: 600 }}>Regional Priority Sector</span></>
        )}
      </ReportHeader>

      {/* Executive summary — backend-composed thesis, then the coverage grid
          that selects what renders inline below it. */}
      <Section title="Executive Summary" brandColor={ACCENT}>
        <Prose>{data.executive_summary}</Prose>
        <DemandTreemap cells={data.colleges[0]?.cells ?? []} total={agg.regional_demand_total} />
        <div style={{ marginTop: 18 }}>
          <Prose>Select a college and occupation in the coverage grid below to examine how each college aligns with a particular SOC.</Prose>
        </div>

        {/* coverage grid */}
        <div style={{ marginTop: 20, border: "1px solid rgba(255,255,255,.09)", borderRadius: 12, background: "rgba(0,0,0,.18)", padding: "16px 18px", overflowX: "auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: `230px repeat(${columns.length}, minmax(58px,1fr))`, gap: 4, alignItems: "center", minWidth: 540 }}>
            {grid}
          </div>
          {/* Coverage key — aligned to the data columns: it reuses the grid's
              column template and spans column 2 → end, so the left edge of
              "Covered" sits exactly at the De Anza column's left edge, clear of
              the role-label column. Neutral swatches read as fill depth (the
              intensity axis), not any one college's hue. */}
          <div style={{ marginTop: 16, paddingTop: 13, borderTop: "1px solid rgba(255,255,255,.06)", display: "grid", gridTemplateColumns: `230px repeat(${columns.length}, minmax(58px,1fr))`, gap: 4, minWidth: 540 }}>
            <div />
            <div style={{ gridColumn: "2 / -1", display: "flex", alignItems: "center", gap: 48, flexWrap: "wrap" }}>
              {[
                { k: "Covered", sub: "teaches it · has supply", bg: "rgba(148,168,201,.92)", ring: true },
                { k: "Partial", sub: "teaches it · no supply", bg: "rgba(148,168,201,.3)", ring: true },
                { k: "Gap", sub: "no curriculum", bg: "rgba(255,255,255,.035)", ring: false },
              ].map((it) => (
                <div key={it.k} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ width: 40, height: 20, borderRadius: 6, background: it.bg, boxShadow: it.ring ? "inset 0 0 0 1px rgba(148,168,201,.5)" : "none", flex: "none" }} />
                  <span style={{ fontSize: 12.5, fontWeight: 500, color: "rgba(255,255,255,.9)", lineHeight: 1.2 }}>
                    {it.k}
                    <span style={{ display: "block", fontSize: 11, color: "#5e6a83", fontWeight: 400 }}>{it.sub}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      {/* Inline detail — the selected occupation's report, exec summary
          suppressed so it opens on Occupational Demand. The Program Outcomes
          panel is injected between Curriculum Alignment and Student Impact via
          the programOutcomes slot. Uses the selected college's own brand color,
          distinct from the red consortium chrome. */}
      {selectedSoc && selRef && (
        <div style={{ marginTop: 36 }}>
          <div ref={ctxSentinel} style={{ height: 1 }} />
          <OpportunityReportBody school={selRef.config} socCode={selectedSoc} sector={data.sector} hideExecutiveSummary hideStudentImpact embedded programOutcomes={programOutcomesPanel} demandTitle="Centers of Excellence Projections (Supply / Demand)" hideLaborMarket={isGapSel} suppressEmptySupplyGap />
        </div>
      )}
    </>,
  );
}
