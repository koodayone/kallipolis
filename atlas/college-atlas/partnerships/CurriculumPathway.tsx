/**
 * Hero visualization for the Curriculum Alignment section's second
 * half: a three-column institutional pathway from program (TOP) to
 * occupation (SOC), bridged by the federal CIP taxonomy.
 *
 * Sits BELOW the existing per-department course accordions in the
 * Curriculum Alignment section. The accordions show specific courses
 * at this college that institutionally prepare for the SOC (the
 * concrete evidence layer); this component zooms out to the full TOP
 * prep set and marks where the college's coverage sits within it.
 *
 * Visual language:
 *   • TOP pill (left)       brand-filled when this college teaches the
 *                           TOP family; outlined-and-dim when it's in
 *                           the institutional prep set but missing
 *                           here. Lines terminate at the badge edge.
 *   • CIP pill (middle)     locked institutional color (steel blue)
 *                           regardless of college brand — visually
 *                           reinforces "this is the federal substrate."
 *                           Dim when inactive (no taught TOP reaches it).
 *   • SOC circle (right)    large brand-filled destination; only
 *                           reached by lines from ACTIVE CIPs.
 *
 * Data source: ApiCurriculumCrosswalk, composed deterministically by
 * backend/partnerships/gather.py:_gather_curriculum_crosswalk. SAM-
 * filtered to A/B/C/D (occupational) per CCCCO MIS Data Element
 * Dictionary.
 */

import { useMemo } from "react";
import type { ApiCurriculumCrosswalk } from "@/college-atlas/partnerships/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

// Locked institutional color — the CIP layer reads as "federal
// substrate, constant" across all colleges regardless of brand.
const CIP_COLOR = "#7ab8e6";
// Taught-TOP glow ring color — a separate signal axis from brand.
const TAUGHT_GLOW = "#7df080";
// Visual color for missing-TOP edges and inactive-CIP treatment.
const INK_FAINT = "#5a6378";
const INK_DIM = "#9ba0b3";
const INK_BODY = "#c8cdda";
const BG = "#060d1f";
const GAP_GRAY = "#3a4257";

type Props = {
  crosswalk: ApiCurriculumCrosswalk;
  socCode: string;
  socTitle: string;
  brandColor: string;
};

export default function CurriculumPathway({
  crosswalk,
  socCode,
  socTitle,
  brandColor,
}: Props) {
  // ── Layout coordinates (all in SVG user units) ─────────────────────
  // Three-column layout with badge-bearing nodes. Bezier curves enter
  // the left edge of the right-column badge and exit the right edge of
  // the left-column badge — no overlap with text.
  const SVG_W = 880;
  const TOP_X_L = 0;
  const TOP_X_R = 240;
  const CIP_X_L = 360;
  const CIP_X_R = 680;
  const SOC_X = 820;
  const BADGE_H = 28;
  const ROW_H = 38;
  const PADDING_TOP = 36;
  const PADDING_BOTTOM = 16;

  // Sort: taught TOPs first (visually weighty content lives at top),
  // then missing TOPs alphabetically by code.
  const sortedTops = useMemo(() => {
    return [...crosswalk.tops].sort((a, b) => {
      if (a.taught_at_college !== b.taught_at_college) {
        return a.taught_at_college ? -1 : 1;
      }
      return a.code.localeCompare(b.code);
    });
  }, [crosswalk.tops]);

  // CIPs sorted alphabetically by code; active CIPs aren't lifted
  // because their badge is structurally identical — only the active
  // flag changes opacity, and the CIP→SOC line only renders for them.
  const sortedCips = useMemo(() => {
    return [...crosswalk.cips].sort((a, b) => a.code.localeCompare(b.code));
  }, [crosswalk.cips]);

  const nRows = Math.max(sortedTops.length, sortedCips.length, 1);
  const SVG_H = PADDING_TOP + PADDING_BOTTOM + nRows * ROW_H;

  // Per-column Y positions, evenly distributed across the viz height.
  const distribute = (count: number, totalH: number, pad: number) => {
    if (count === 1) return [pad + totalH / 2];
    const usable = totalH;
    return Array.from({ length: count }, (_, i) =>
      pad + (i * usable) / (count - 1)
    );
  };
  const innerH = SVG_H - PADDING_TOP - PADDING_BOTTOM;

  const topYs = distribute(sortedTops.length, innerH, PADDING_TOP);
  const cipYs = distribute(sortedCips.length, innerH, PADDING_TOP);
  const socY = PADDING_TOP + innerH / 2;

  // Lookup by code for edge routing.
  const cipYByCode = new Map<string, number>(
    sortedCips.map((c, i) => [c.code, cipYs[i]])
  );

  // Build edge paths.
  type Edge = { d: string; cls: "taught" | "missing" | "active" };
  const edges: Edge[] = [];

  // TOP → CIP edges (all of them, taught vs. missing as visual class).
  sortedTops.forEach((top, i) => {
    const ty = topYs[i];
    for (const cipCode of top.cips) {
      const cy = cipYByCode.get(cipCode);
      if (cy === undefined) continue;
      edges.push({
        d: bezier(TOP_X_R, ty, CIP_X_L, cy),
        cls: top.taught_at_college ? "taught" : "missing",
      });
    }
  });

  // CIP → SOC edges (only for ACTIVE CIPs — the lit pathway).
  sortedCips.forEach((cip, i) => {
    if (!cip.active) return;
    const cy = cipYs[i];
    edges.push({
      d: bezier(CIP_X_R, cy, SOC_X - 38, socY),
      cls: "active",
    });
  });

  return (
    <div style={{ marginTop: 24 }}>
      {/* Section transition — hairline divider between the per-
          department accordions above and this pathway view below. */}
      <div
        style={{
          height: 1,
          background: "rgba(255,255,255,0.06)",
          marginBottom: 24,
        }}
      />

      {/* Headline metric — the dominant data point. Reads as one
          sentence: "N of M TOP families supporting SOC X". */}
      <div
        style={{
          fontFamily: FONT,
          fontSize: 22,
          fontWeight: 600,
          color: "rgba(255,255,255,0.95)",
          letterSpacing: "-0.005em",
          marginBottom: 6,
        }}
      >
        <span
          style={{
            color: brandColor,
            fontFamily: MONO,
            fontWeight: 700,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {crosswalk.n_taught} of {crosswalk.n_total}
        </span>{" "}
        TOP families supporting{" "}
        <span
          style={{
            color: brandColor,
            fontFamily: MONO,
            fontWeight: 700,
          }}
        >
          SOC {socCode}
        </span>
      </div>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 10.5,
          color: INK_DIM,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          marginBottom: 24,
        }}
      >
        {Math.round(crosswalk.coverage_pct)}% institutional coverage ·
        curriculum-development surface: {crosswalk.n_total - crosswalk.n_taught} TOP
        families
      </div>

      {/* Column headers — minimal, no source attribution. */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontFamily: MONO,
          fontSize: 12,
          fontWeight: 700,
          color: brandColor,
          letterSpacing: "0.4em",
          padding: `0 ${(SOC_X - TOP_X_R) / 2}px 0 110px`,
          marginBottom: 4,
        }}
      >
        <span>T O P</span>
        <span>C I P</span>
        <span style={{ marginRight: 12 }}>S O C</span>
      </div>

      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        width="100%"
        style={{ display: "block", overflow: "visible" }}
        aria-label="TOP-CIP-SOC institutional pathway visualization"
      >
        {/* Edges first, so badges layer on top. */}
        {edges.map((e, i) => (
          <path
            key={`edge-${i}`}
            d={e.d}
            fill="none"
            stroke={
              e.cls === "taught"
                ? TAUGHT_GLOW
                : e.cls === "active"
                ? brandColor
                : GAP_GRAY
            }
            strokeWidth={e.cls === "missing" ? 0.8 : 1.6}
            opacity={
              e.cls === "missing" ? 0.32 : e.cls === "active" ? 0.7 : 0.75
            }
          />
        ))}

        {/* TOP pill badges. */}
        {sortedTops.map((top, i) => {
          const y = topYs[i];
          const taught = top.taught_at_college;
          return (
            <g key={`top-${top.code}`}>
              <rect
                x={TOP_X_L}
                y={y - BADGE_H / 2}
                width={TOP_X_R - TOP_X_L}
                height={BADGE_H}
                rx={14}
                ry={14}
                fill={taught ? brandColor : BG}
                stroke={taught ? TAUGHT_GLOW : INK_FAINT}
                strokeWidth={taught ? 1.5 : 0.8}
                opacity={taught ? 1 : 0.85}
              />
              <text
                x={TOP_X_L + 16}
                y={y + 4}
                fontFamily={MONO}
                fontSize={12}
                fontWeight={700}
                fill={taught ? BG : INK_DIM}
              >
                {top.code}
              </text>
              <text
                x={TOP_X_L + 70}
                y={y + 4}
                fontFamily={FONT}
                fontSize={11}
                fontWeight={taught ? 600 : 400}
                fill={taught ? BG : INK_DIM}
              >
                {truncate(top.name, 26)}
              </text>
            </g>
          );
        })}

        {/* CIP pill badges. */}
        {sortedCips.map((cip, i) => {
          const y = cipYs[i];
          const alpha = cip.active ? 1.0 : 0.55;
          return (
            <g key={`cip-${cip.code}`} opacity={alpha}>
              <rect
                x={CIP_X_L}
                y={y - BADGE_H / 2}
                width={CIP_X_R - CIP_X_L}
                height={BADGE_H}
                rx={14}
                ry={14}
                fill={BG}
                stroke={CIP_COLOR}
                strokeWidth={cip.active ? 1.0 : 0.6}
              />
              {/* Left-edge color tick — federal-taxonomy identity marker. */}
              <rect
                x={CIP_X_L}
                y={y - BADGE_H / 2 + 2}
                width={5}
                height={BADGE_H - 4}
                rx={2}
                fill={CIP_COLOR}
              />
              <text
                x={CIP_X_L + 18}
                y={y + 4}
                fontFamily={MONO}
                fontSize={11}
                fontWeight={700}
                fill={CIP_COLOR}
              >
                {cip.code}
              </text>
              <text
                x={CIP_X_L + 80}
                y={y + 4}
                fontFamily={FONT}
                fontSize={10.5}
                fill={INK_BODY}
              >
                {truncate(cip.title, 40)}
              </text>
            </g>
          );
        })}

        {/* SOC destination — single brand-filled circle. */}
        <circle
          cx={SOC_X}
          cy={socY}
          r={38}
          fill={brandColor}
          stroke="white"
          strokeWidth={2}
        />
        <text
          x={SOC_X}
          y={socY + 5}
          fontFamily={MONO}
          fontSize={13}
          fontWeight={700}
          fill={BG}
          textAnchor="middle"
        >
          {socCode}
        </text>
        <text
          x={SOC_X}
          y={socY + 60}
          fontFamily={FONT}
          fontSize={11}
          fontWeight={600}
          fill={brandColor}
          textAnchor="middle"
        >
          {truncate(socTitle, 28)}
        </text>
      </svg>

      {/* Filter caption — names the SAM filter and the active-CIP
          render rule, attributing both to their institutional source. */}
      <p
        style={{
          fontFamily: FONT,
          fontSize: 11,
          color: INK_FAINT,
          fontStyle: "italic",
          marginTop: 20,
          paddingTop: 14,
          borderTop: "1px solid rgba(255,255,255,0.05)",
          lineHeight: 1.5,
        }}
      >
        Showing courses classified SAM A/B/C/D (Apprenticeship → Possibly
        Occupational) per the CCCCO MIS Data Element Dictionary. CIP→SOC
        paths shown only for CIPs reached through TOPs actively taught at this
        college.
      </p>
    </div>
  );
}

// ── helpers ────────────────────────────────────────────────────────────────

/**
 * Bezier curve with horizontal control points — connects two y-aligned
 * column points with a smooth left-to-right S-curve that doesn't
 * overshoot vertically.
 */
function bezier(x1: number, y1: number, x2: number, y2: number): string {
  const curvature = 0.55;
  const cx1 = x1 + (x2 - x1) * curvature;
  const cx2 = x2 - (x2 - x1) * curvature;
  return `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;
}

function truncate(s: string, maxLen: number): string {
  if (s.length <= maxLen) return s;
  return s.slice(0, maxLen - 1) + "…";
}
