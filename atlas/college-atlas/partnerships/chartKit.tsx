/* ── Chart kit — the SVAMP report's shared chart vocabulary ────────────────
   Color science (brand-distinct overlay palette, lead/overlay assignment),
   plot constants, value chips with collision-aware placement, axis helpers,
   and the DataMart label formatters. Extracted verbatim from SvampView so the
   dashboard (and any future surface) composes the same vocabulary; SvampView
   remains the reference composition. */

import React from "react";
import { MONO } from "@/college-atlas/partnerships/reportChrome";

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

// Lead/overlay color assignment (the targeted-cell idiom): the dominant series
// — largest total over the window — takes the school brand; every other series
// keeps a stable palette hue (filtered to stay hue-distinct from the brand) by
// its position, so adjacent bands/lines contrast by hue rather than alpha.
function leadOverlayColors(series: { key: string; vals: (number | null)[] }[], brand: string): (k: string) => string {
  const total = (s: { vals: (number | null)[] }) => s.vals.reduce((t: number, v) => t + (v ?? 0), 0);
  const lead = series.reduce<{ key: string; vals: (number | null)[] } | null>(
    (best, s) => (best && total(best) >= total(s) ? best : s), null);
  const [bh, bs] = hexToHsl(brand);
  const distinct = bs < 25
    ? OVERLAY_COLORS
    : OVERLAY_COLORS.filter((c) => { const [ch, cs] = hexToHsl(c); return cs < 25 || hueDist(ch, bh) >= 40; });
  const palette = distinct.length ? distinct : OVERLAY_COLORS;
  const map = new Map<string, string>();
  let i = 0;
  series.forEach((s) => map.set(s.key, s.key === lead?.key ? brand : palette[i++ % palette.length]));
  return (k: string) => map.get(k) ?? palette[0];
}

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

// Compact legend labels for DataMart credential-type names — "Certificate
// requiring 16 to fewer than 30 semester units" → "Certificate · 16–30 units",
// "Associate of Science (A.S.) degree" → "A.S. degree". Verbatim fallback for
// any shape the parser doesn't know.
function shortAwardType(t: string): string {
  const paren = t.match(/\(([^)]+)\)/);
  if (/associate/i.test(t) && paren) return `${paren[1]} degree`;
  const nums = t.match(/\d+/g);
  if (/^certificate/i.test(t) && nums?.length === 2) return `Certificate · ${nums[0]}–${nums[1]} units`;
  if (/^noncredit/i.test(t) && nums?.length === 2) return `Noncredit · ${nums[0]}–${nums[1]} hrs`;
  if (/^noncredit/i.test(t) && nums?.length === 1) return `Noncredit · <${nums[0]} hrs`;
  return t;
}

// Compact legend labels for DataMart credit families.
const CREDIT_FAMILY_LABELS: Record<string, string> = {
  "Credit - Degree Applicable": "Credit · degree-applicable",
  "Credit - Not Degree Applicable": "Credit · not degree-applicable",
  "Non-Credit": "Noncredit",
};
const shortCreditType = (t: string) => CREDIT_FAMILY_LABELS[t] ?? t;

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

export {
  Dot,
  shortName, hexA, hexToHsl, hueDist, OVERLAY_COLORS, leadOverlayColors,
  parseTerm, edgeAnchor, PLOT, valueChip, placeChipYs,
  awardYearLabel, shortAwardType, shortCreditType, niceStep,
};
