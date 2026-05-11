/**
 * CurriculumPathway — institutional pathway hero for the partnership
 * landscape report. Renders the TOP → CIP → SOC chain for a single
 * (college, SOC) pair with click-to-isolate interactivity.
 *
 * Interaction model:
 *   • Default state: full crosswalk rendered. Taught pathway lit in
 *     per-college brand color; missing pathway dimmed. SOC destination
 *     circle and taught-TOP badges carry the kallipolis sun-gold ring.
 *   • Click a TOP or CIP badge: dim everything except the selected
 *     pathway. For TOP-selected: highlight edges from that TOP to its
 *     CIPs and from those CIPs onward to the SOC (even when the CIP is
 *     inactive — exploratory view of what the pathway WOULD look like
 *     if this TOP were taught). For CIP-selected: highlight all TOP
 *     feeders and the CIP→SOC edge.
 *   • Click outside the SVG (or click the same badge again): clear
 *     selection, return to default state.
 *
 * Data comes from the partnership opportunity report's
 * curriculum_crosswalk field. Sort orders, sentence templates, and
 * coordinate constants are deterministic — same input always renders
 * byte-for-byte the same output.
 */

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ApiCurriculumCrosswalk } from "@/college-atlas/partnerships/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

// Locked institutional color — the CIP layer reads as "federal
// substrate, constant" across all colleges regardless of brand.
const CIP_COLOR = "#7ab8e6";
// Taught-TOP glow ring color — kallipolis sun gold (matches the
// queryshell RisingSun mark). A separate signal axis from per-college
// brand: this ring identifies the institutional pathway as taught,
// regardless of which college is in view.
const TAUGHT_GLOW = "#c9a84c";
// Visual color for missing-TOP edges and inactive-CIP treatment.
const INK_FAINT = "#5a6378";
const INK_DIM = "#9ba0b3";
const INK_BODY = "#c8cdda";
const BG = "#060d1f";
const GAP_GRAY = "#3a4257";

type Props = {
  crosswalk: ApiCurriculumCrosswalk;
  collegeName: string;
  socCode: string;
  socTitle: string;
  brandColor: string;
};

type Selection =
  | { kind: "top"; code: string }
  | { kind: "cip"; code: string }
  | null;

export default function CurriculumPathway({
  crosswalk,
  collegeName,
  socCode,
  socTitle,
  brandColor,
}: Props) {
  const [selection, setSelection] = useState<Selection>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Click-outside detection — clears selection when the user clicks
  // anywhere outside the SVG. SVG-internal clicks (badges, whitespace)
  // are handled by per-element handlers and stopPropagation where
  // needed.
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (svgRef.current && !svgRef.current.contains(e.target as Node)) {
        setSelection(null);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const isSelected = (kind: "top" | "cip", code: string) =>
    selection?.kind === kind && selection.code === code;

  // Look up which CIPs are bridged from a given TOP, and which TOPs
  // feed into a given CIP. Used to determine which elements participate
  // in the highlighted pathway when a selection is active.
  const cipsByTop = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const t of crosswalk.tops) {
      m.set(t.code, new Set(t.cips));
    }
    return m;
  }, [crosswalk.tops]);

  const topsByCip = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const t of crosswalk.tops) {
      for (const c of t.cips) {
        if (!m.has(c)) m.set(c, new Set());
        m.get(c)!.add(t.code);
      }
    }
    return m;
  }, [crosswalk.tops]);

  // Compute whether a given element (top, cip, or edge) is part of the
  // currently-selected pathway. When nothing is selected, returns null
  // (meaning "render in default state").
  function highlightTop(topCode: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") return selection.code === topCode;
    if (selection.kind === "cip") {
      return topsByCip.get(selection.code)?.has(topCode) ?? false;
    }
    return null;
  }
  function highlightCip(cipCode: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") {
      return cipsByTop.get(selection.code)?.has(cipCode) ?? false;
    }
    if (selection.kind === "cip") return selection.code === cipCode;
    return null;
  }
  function highlightTopCipEdge(topCode: string, cipCode: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") {
      return selection.code === topCode && (cipsByTop.get(topCode)?.has(cipCode) ?? false);
    }
    if (selection.kind === "cip") {
      return selection.code === cipCode;
    }
    return null;
  }
  function highlightCipSocEdge(cipCode: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") {
      return cipsByTop.get(selection.code)?.has(cipCode) ?? false;
    }
    if (selection.kind === "cip") return selection.code === cipCode;
    return null;
  }
  // ── Layout coordinates (all in SVG user units) ─────────────────────
  // Three-column layout with badge-bearing nodes. Bezier curves enter
  // the left edge of the right-column badge and exit the right edge of
  // the left-column badge — no overlap with text.
  // Wider badges + headers-inside-SVG so the column labels always
  // align with the content beneath them regardless of viewport scaling.
  //
  // SVG width chosen so the three column header centers (TOP at 145,
  // CIP at 545, SOC at 945) are evenly spaced — equal 400-unit gaps
  // between adjacent header midpoints. This gives the layout an even
  // visual rhythm. The cost is a slight overall rescale (~10%) since
  // the SVG renders at width=100% within its container.
  const SVG_W = 1024;
  const TOP_X_L = 0;
  const TOP_X_R = 290;
  const CIP_X_L = 370;
  const CIP_X_R = 720;
  const SOC_X = 945;
  // SOC destination circle radius — increased so the SOC code + title
  // can both live inside the circle. Edges from CIPs terminate at the
  // circle's left edge (SOC_X - SOC_EDGE_RADIUS) to avoid bleeding into
  // the filled disc.
  const SOC_EDGE_RADIUS = 78;
  // Badge tall enough for 2 lines of label text. Single-line names
  // center vertically; long names wrap to 2 lines via wrapText().
  const BADGE_H = 38;
  const ROW_H = 50;
  const HEADER_Y = 28;       // baseline for in-SVG column headers
  const PADDING_TOP = 88;    // gap between headers and first row of content
  const PADDING_BOTTOM = 16;
  // Max chars per line — empirically tuned to each column's badge
  // width after subtracting the code-prefix region. Two lines lets us
  // accommodate ~60-char TOP names and ~75-char CIP titles before
  // any truncation kicks in.
  const TOP_NAME_CHARS_PER_LINE = 28;
  const CIP_TITLE_CHARS_PER_LINE = 38;

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

  // Build edge paths. We retain enough metadata on each edge to
  // determine its render state under any selection — which TOP it
  // departs from, which CIP it terminates at, and whether the CIP is
  // currently active.
  type Edge = {
    d: string;
    kind: "top-cip" | "cip-soc";
    topCode?: string;
    cipCode: string;
    cipActive: boolean;
    topTaught: boolean;
  };
  const edges: Edge[] = [];

  // TOP → CIP edges.
  sortedTops.forEach((top, i) => {
    const ty = topYs[i];
    for (const cipCode of top.cips) {
      const cy = cipYByCode.get(cipCode);
      if (cy === undefined) continue;
      const cip = sortedCips.find((c) => c.code === cipCode);
      edges.push({
        d: bezier(TOP_X_R, ty, CIP_X_L, cy),
        kind: "top-cip",
        topCode: top.code,
        cipCode,
        cipActive: cip?.active ?? false,
        topTaught: top.taught_at_college,
      });
    }
  });

  // CIP → SOC edges. In the interactive view we draw ALL of them so
  // that selecting a missing-TOP pathway can light up its CIP→SOC
  // segment. The default render keeps inactive ones invisible (opacity
  // 0) so the static appearance matches the production hero.
  sortedCips.forEach((cip, i) => {
    const cy = cipYs[i];
    edges.push({
      d: bezier(CIP_X_R, cy, SOC_X - SOC_EDGE_RADIUS, socY),
      kind: "cip-soc",
      cipCode: cip.code,
      cipActive: cip.active,
      topTaught: false, // unused for cip-soc edges
    });
  });

  // Deterministic narrative paragraph composed from graph data.
  // Frames the wider institutional pathway context before the
  // visualization renders. Same college + SOC always yields the same
  // sentence, byte-for-byte — institutional-deference principle.
  const n_missing = crosswalk.n_total - crosswalk.n_taught;
  const narrative =
    `${collegeName}'s curriculum prepares students for SOC ${socCode}` +
    ` (${socTitle}) through ${crosswalk.n_taught} TOP code` +
    ` ${crosswalk.n_taught === 1 ? "group" : "groups"},` +
    ` mapped via the Chancellor's Office TOP-CIP crosswalk and the NCES` +
    ` CIP-SOC crosswalk to the federal occupation classification.` +
    ` The complete preparation pathway encompasses ${crosswalk.n_total} TOP` +
    ` ${crosswalk.n_total === 1 ? "group" : "groups"} and` +
    ` ${crosswalk.cips.length} federal` +
    ` ${crosswalk.cips.length === 1 ? "CIP" : "CIPs"} in total` +
    (n_missing > 0
      ? ` — the remaining ${n_missing} TOP` +
        ` ${n_missing === 1
            ? "group represents a potential curriculum-development surface"
            : "groups represent potential curriculum-development surfaces"}` +
        ` for partnership opportunities.`
      : `.`);

  return (
    <div style={{ marginTop: 32 }}>
      {/* Headline metric — sub-section header. Reads as one sentence:
          "N of M TOP groups supporting SOC X". Numbers and SOC code in
          brand color so the data points pop visually; the connective
          tissue between them stays plain so the headline is a compact
          declarative statement. The college name is implicit (the
          report is already scoped to one college) and lives in the
          narrative paragraph below for full attribution. */}
      <div
        style={{
          fontFamily: FONT,
          fontSize: 18,
          fontWeight: 600,
          color: "rgba(255,255,255,0.95)",
          letterSpacing: "-0.005em",
          marginBottom: 14,
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
        {crosswalk.n_total === 1
          ? "TOP group crosswalks to"
          : "TOP groups crosswalk to"}{" "}
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

      {/* Deterministic prose — supporting explanation that unpacks the
          headline metric and names the institutional sources. */}
      <p
        style={{
          fontFamily: FONT,
          fontSize: 14,
          lineHeight: 1.65,
          color: INK_BODY,
          marginTop: 0,
          marginBottom: 24,
          maxWidth: 920,
        }}
      >
        {narrative}
      </p>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        width="100%"
        style={{ display: "block", overflow: "visible" }}
        aria-label="TOP-CIP-SOC institutional pathway visualization"
        onClick={() => setSelection(null)}
      >
        {/* Column headers — inside the SVG so they share the
            coordinate system with the content beneath. Centered over
            each column's badge midpoint. Sized larger than the body
            text to anchor the section visually. */}
        <text
          x={(TOP_X_L + TOP_X_R) / 2}
          y={HEADER_Y}
          fontFamily={MONO}
          fontSize={16}
          fontWeight={700}
          fill={brandColor}
          letterSpacing="0.4em"
          textAnchor="middle"
        >
          T O P
        </text>
        <text
          x={(CIP_X_L + CIP_X_R) / 2}
          y={HEADER_Y}
          fontFamily={MONO}
          fontSize={16}
          fontWeight={700}
          fill={brandColor}
          letterSpacing="0.4em"
          textAnchor="middle"
        >
          C I P
        </text>
        <text
          x={SOC_X}
          y={HEADER_Y}
          fontFamily={MONO}
          fontSize={16}
          fontWeight={700}
          fill={brandColor}
          letterSpacing="0.4em"
          textAnchor="middle"
        >
          S O C
        </text>

        {/* Edges first, so badges layer on top. Lit pathway uses the
            brand color end-to-end (TOP→CIP and CIP→SOC both); missing
            pathways drop to gap_gray. One consistent color reads as
            "the chain that is active for this college." */}
        {edges.map((e, i) => {
          // Default render state mirrors the production component:
          //   • TOP→CIP edges where the TOP is taught: brand color
          //   • TOP→CIP edges where the TOP is missing: gap-gray
          //   • CIP→SOC edges where the CIP is active: brand color
          //   • CIP→SOC edges where the CIP is inactive: invisible
          // Selected state overrides: highlighted edges full brand,
          // non-highlighted edges drop to a faint dim.
          let stroke: string;
          let strokeWidth: number;
          let opacity: number;
          if (e.kind === "top-cip") {
            const def_stroke = e.topTaught ? brandColor : GAP_GRAY;
            const def_width = e.topTaught ? 1.6 : 0.8;
            const def_opacity = e.topTaught ? 0.75 : 0.32;
            const hl = e.topCode
              ? highlightTopCipEdge(e.topCode, e.cipCode)
              : null;
            stroke = hl ? brandColor : def_stroke;
            strokeWidth = hl ? 2.0 : def_width;
            opacity = hl === null ? def_opacity : hl ? 0.95 : 0.08;
          } else {
            // cip-soc
            const def_stroke = brandColor;
            const def_width = 1.6;
            const def_opacity = e.cipActive ? 0.75 : 0;
            const hl = highlightCipSocEdge(e.cipCode);
            stroke = def_stroke;
            strokeWidth = hl ? 2.0 : def_width;
            opacity = hl === null ? def_opacity : hl ? 0.95 : 0.08;
          }
          return (
            <path
              key={`edge-${i}`}
              d={e.d}
              fill="none"
              stroke={stroke}
              strokeWidth={strokeWidth}
              opacity={opacity}
              style={{ transition: "opacity 0.18s, stroke-width 0.18s" }}
            />
          );
        })}

        {/* TOP pill badges. Name wraps to 2 lines if it exceeds the
            single-line budget; single-line names center vertically.
            Click to isolate the TOP's pathway through the chain. */}
        {sortedTops.map((top, i) => {
          const y = topYs[i];
          const taught = top.taught_at_college;
          const lines = wrapText(top.name, TOP_NAME_CHARS_PER_LINE);
          const isTwoLine = lines.length === 2;
          const hl = highlightTop(top.code);
          const sel = isSelected("top", top.code);
          const groupOpacity = hl === null ? 1 : hl ? 1 : 0.25;
          return (
            <g
              key={`top-${top.code}`}
              onClick={(e) => {
                e.stopPropagation();
                setSelection(sel ? null : { kind: "top", code: top.code });
              }}
              style={{
                cursor: "pointer",
                opacity: groupOpacity,
                transition: "opacity 0.18s",
              }}
            >
              <rect
                x={TOP_X_L}
                y={y - BADGE_H / 2}
                width={TOP_X_R - TOP_X_L}
                height={BADGE_H}
                rx={BADGE_H / 2}
                ry={BADGE_H / 2}
                fill={taught ? brandColor : BG}
                stroke={taught || sel ? TAUGHT_GLOW : INK_FAINT}
                strokeWidth={sel ? 2.5 : taught ? 1.5 : 0.8}
                opacity={taught ? 1 : 0.85}
              />
              <text
                x={TOP_X_L + 16}
                y={y + 5}
                fontFamily={MONO}
                fontSize={13}
                fontWeight={700}
                fill={taught ? BG : INK_DIM}
              >
                {top.code}
              </text>
              <text
                x={TOP_X_L + 70}
                y={isTwoLine ? y - 3 : y + 5}
                fontFamily={FONT}
                fontSize={11}
                fontWeight={taught ? 600 : 400}
                fill={taught ? BG : INK_DIM}
              >
                <tspan x={TOP_X_L + 70}>{lines[0]}</tspan>
                {isTwoLine && (
                  <tspan x={TOP_X_L + 70} dy={13}>
                    {lines[1]}
                  </tspan>
                )}
              </text>
            </g>
          );
        })}

        {/* CIP pill badges. Title wraps to 2 lines when it exceeds the
            single-line budget. Click to isolate the CIP's feeders and
            its CIP→SOC edge. */}
        {sortedCips.map((cip, i) => {
          const y = cipYs[i];
          const lines = wrapText(cip.title, CIP_TITLE_CHARS_PER_LINE);
          const isTwoLine = lines.length === 2;
          const hl = highlightCip(cip.code);
          const sel = isSelected("cip", cip.code);
          // Group opacity composites with the standard active/inactive
          // dimming. When nothing is selected: active=1.0, inactive=0.55.
          // When a selection is active: highlighted=1.0, others=0.18.
          const defOpacity = cip.active ? 1.0 : 0.55;
          const opacity = hl === null ? defOpacity : hl ? 1.0 : 0.18;
          return (
            <g
              key={`cip-${cip.code}`}
              opacity={opacity}
              onClick={(e) => {
                e.stopPropagation();
                setSelection(sel ? null : { kind: "cip", code: cip.code });
              }}
              style={{ cursor: "pointer", transition: "opacity 0.18s" }}
            >
              <rect
                x={CIP_X_L}
                y={y - BADGE_H / 2}
                width={CIP_X_R - CIP_X_L}
                height={BADGE_H}
                rx={BADGE_H / 2}
                ry={BADGE_H / 2}
                fill={BG}
                stroke={CIP_COLOR}
                strokeWidth={sel ? 2.0 : cip.active ? 1.0 : 0.6}
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
                y={y + 5}
                fontFamily={MONO}
                fontSize={12}
                fontWeight={700}
                fill={CIP_COLOR}
              >
                {cip.code}
              </text>
              <text
                x={CIP_X_L + 80}
                y={isTwoLine ? y - 3 : y + 5}
                fontFamily={FONT}
                fontSize={10.5}
                fill={INK_BODY}
              >
                <tspan x={CIP_X_L + 80}>{lines[0]}</tspan>
                {isTwoLine && (
                  <tspan x={CIP_X_L + 80} dy={13}>
                    {lines[1]}
                  </tspan>
                )}
              </text>
            </g>
          );
        })}

        {/* SOC destination — large brand-filled circle with both the
            SOC code and the title contained inside. Title wraps to
            multiple lines as needed; very long titles truncate cleanly
            at the line budget. The circle is the visual culmination
            of the chain — sized to anchor the right side of the layout. */}
        {(() => {
          const SOC_R = SOC_EDGE_RADIUS;
          // Code line at the top inside the circle.
          // Title wraps to up to 3 lines inside, below the code.
          const SOC_TITLE_CHARS_PER_LINE = 16;
          const wrappedTitle = wrapToNLines(
            socTitle,
            SOC_TITLE_CHARS_PER_LINE,
            3
          );
          // Vertical placement: code anchored above center, title block
          // anchored below center. Both share the circle's vertical
          // axis (socY).
          const CODE_FONT = 18;
          const TITLE_FONT = 10;
          const TITLE_LINE_H = 12;
          // Center the (code + gap + N title lines) block vertically.
          const blockH = CODE_FONT + 8 + wrappedTitle.length * TITLE_LINE_H;
          const blockTop = socY - blockH / 2;
          const codeY = blockTop + CODE_FONT - 2;
          const titleY0 = blockTop + CODE_FONT + 16;
          return (
            <g>
              {/* Brand fill + taught-glow ring matches the visual
                  treatment on taught TOP badges. The SOC sits at the
                  end of the lit pathway, so it carries the same
                  "active/reached" visual signal. */}
              <circle
                cx={SOC_X}
                cy={socY}
                r={SOC_R}
                fill={brandColor}
                stroke={TAUGHT_GLOW}
                strokeWidth={2}
              />
              <text
                x={SOC_X}
                y={codeY}
                fontFamily={MONO}
                fontSize={CODE_FONT}
                fontWeight={700}
                fill={BG}
                textAnchor="middle"
              >
                {socCode}
              </text>
              <text
                x={SOC_X}
                y={titleY0}
                fontFamily={FONT}
                fontSize={TITLE_FONT}
                fontWeight={600}
                fill={BG}
                textAnchor="middle"
              >
                {wrappedTitle.map((line, idx) => (
                  <tspan
                    key={idx}
                    x={SOC_X}
                    dy={idx === 0 ? 0 : TITLE_LINE_H}
                  >
                    {line}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })()}
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

/**
 * Wrap a single string to at most 2 lines of `maxChars` each, splitting
 * on word boundaries (space, slash, comma). If the full string fits in
 * one line, returns [text]. If it needs two lines, returns [line1,
 * line2]. If line 2 would still overflow, truncates it with an ellipsis.
 *
 * Use case: TOP names and CIP titles that may exceed a single badge's
 * horizontal capacity. Two lines preserves readability without
 * resorting to opaque truncation mid-word.
 */
function wrapText(text: string, maxChars: number): string[] {
  return wrapToNLines(text, maxChars, 2);
}

/**
 * Wrap a string to at most `maxLines` lines of `maxChars` each, splitting
 * on word boundaries (space, slash, comma). The last line truncates with
 * an ellipsis if it would overflow.
 *
 * Used for the SOC label inside the destination circle, which has more
 * vertical room and benefits from a 3-line layout.
 */
function wrapToNLines(text: string, maxChars: number, maxLines: number): string[] {
  if (text.length <= maxChars) return [text];
  const SPLIT_CHARS = new Set([" ", "/", ","]);
  const lines: string[] = [];
  let remaining = text;
  while (lines.length < maxLines - 1 && remaining.length > maxChars) {
    let splitAt = -1;
    for (let i = Math.min(maxChars, remaining.length - 1); i > 0; i--) {
      if (SPLIT_CHARS.has(remaining[i])) {
        splitAt = i;
        break;
      }
    }
    if (splitAt === -1) splitAt = maxChars;
    const includeSep = remaining[splitAt] === "/";
    lines.push(remaining.slice(0, splitAt + (includeSep ? 1 : 0)).trim());
    remaining = remaining.slice(splitAt + (remaining[splitAt] === " " ? 1 : 0)).trim();
  }
  if (remaining.length > maxChars) {
    remaining = remaining.slice(0, maxChars - 1) + "…";
  }
  lines.push(remaining);
  return lines;
}
