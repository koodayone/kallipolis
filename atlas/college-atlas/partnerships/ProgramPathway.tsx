/**
 * ProgramPathway — the TOP-anchored TOP → CIP → SOC pathway for the SVAMP
 * Programs lens. The dual of CurriculumPathway (which is SOC-anchored): here a
 * single focused TOP program fans out, through its bridging federal CIPs, to
 * the SVAMP occupations it prepares students for — visualizing the one-to-many
 * crosswalk that a single program manifests.
 *
 * Layout: emphasized TOP anchor (left) → CIP pills (middle, federal-blue
 * substrate) → SOC pills (right). Click a CIP or SOC to isolate its pathway;
 * click the TOP (or outside) to clear. Deterministic — same input renders the
 * same output. This is a Programs-lens-only component; the per-college report's
 * CurriculumPathway is deliberately left untouched.
 */

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ApiProgramCrosswalk } from "@/college-atlas/partnerships/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

// Federal CIP substrate — constant blue, independent of the lens accent
// (mirrors CurriculumPathway: the CIP layer reads as the same federal taxonomy
// everywhere). TOP + SOC endpoints carry the lens accent (green) and the
// kallipolis sun-gold ring marks the focused anchor.
const CIP_COLOR = "#7ab8e6";
const TAUGHT_GLOW = "#c9a84c";
const INK_FAINT = "#5a6378";
const INK_BODY = "#c8cdda";
const BG = "#060d1f";

type Props = {
  crosswalk: ApiProgramCrosswalk;
  accent: string; // Programs-lens green
};

type Selection =
  | { kind: "cip"; code: string }
  | { kind: "soc"; code: string }
  // TOP-selected: the focus program — highlight every edge in the fan-out.
  | { kind: "top" }
  | null;

export default function ProgramPathway({ crosswalk, accent }: Props) {
  const [selection, setSelection] = useState<Selection>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (svgRef.current && !svgRef.current.contains(e.target as Node)) {
        setSelection(null);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  // cip → SOCs that route through it; soc → its bridging CIPs.
  const socsByCip = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const s of crosswalk.socs) {
      for (const c of s.cips) {
        if (!m.has(c)) m.set(c, new Set());
        m.get(c)!.add(s.code);
      }
    }
    return m;
  }, [crosswalk.socs]);

  const cipsBySoc = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const s of crosswalk.socs) m.set(s.code, new Set(s.cips));
    return m;
  }, [crosswalk.socs]);

  // Highlight state under the active selection (null ⇒ default render).
  function highlightCip(code: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") return true;
    if (selection.kind === "cip") return selection.code === code;
    return cipsBySoc.get(selection.code)?.has(code) ?? false;
  }
  function highlightSoc(code: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") return true;
    if (selection.kind === "soc") return selection.code === code;
    return socsByCip.get(selection.code)?.has(code) ?? false;
  }
  function highlightTopCipEdge(cipCode: string): boolean | null {
    return highlightCip(cipCode);
  }
  function highlightCipSocEdge(cipCode: string, socCode: string): boolean | null {
    if (!selection) return null;
    if (selection.kind === "top") return true;
    if (selection.kind === "cip") return selection.code === cipCode;
    return selection.code === socCode && (cipsBySoc.get(socCode)?.has(cipCode) ?? false);
  }

  // ── Layout (flipped vs CurriculumPathway: anchor on the LEFT, fan to the
  //    RIGHT). Header centers: TOP at TOP_CX, CIP at CIP mid, SOC at SOC mid. ──
  const SVG_W = 1024;
  const TOP_CX = 90;
  const TOP_R = 76;
  const CIP_X_L = 256;
  const CIP_X_R = 626;
  const SOC_X_L = 706;
  const SOC_X_R = 1018;
  const BADGE_H = 38;
  const ROW_H = 50;
  const HEADER_Y = 28;
  const PADDING_TOP = 88;
  const PADDING_BOTTOM = 16;
  const CIP_TITLE_CHARS_PER_LINE = 38;
  const SOC_TITLE_CHARS_PER_LINE = 26;

  const sortedCips = useMemo(
    () => [...crosswalk.cips].sort((a, b) => a.code.localeCompare(b.code)),
    [crosswalk.cips],
  );
  // SOCs keep the server's order (openings-desc, matching the demand table).
  const socs = crosswalk.socs;

  const nRows = Math.max(sortedCips.length, socs.length, 1);
  const bandH = nRows * ROW_H;
  // Reserve bottom space for the fixed-radius TOP anchor circle (overflow is
  // visible; with few rows the circle would spill past the SVG box).
  const bottomPad = Math.max(PADDING_BOTTOM, TOP_R - bandH / 2 + 12);
  const SVG_H = PADDING_TOP + bottomPad + bandH;

  const distribute = (count: number, totalH: number, pad: number) => {
    if (count === 1) return [pad + totalH / 2];
    return Array.from({ length: count }, (_, i) => pad + (i * totalH) / (count - 1));
  };
  const innerH = bandH;
  const cipYs = distribute(sortedCips.length, innerH, PADDING_TOP);
  const socYs = distribute(socs.length, innerH, PADDING_TOP);
  const anchorY = PADDING_TOP + innerH / 2;

  const cipYByCode = new Map<string, number>(sortedCips.map((c, i) => [c.code, cipYs[i]]));

  // Edges: TOP → every CIP; each CIP → the SOCs that route through it.
  type Edge = { d: string; kind: "top-cip" | "cip-soc"; cipCode: string; socCode?: string };
  const edges: Edge[] = [];
  sortedCips.forEach((cip, i) => {
    edges.push({
      d: bezier(TOP_CX + TOP_R, anchorY, CIP_X_L, cipYs[i]),
      kind: "top-cip",
      cipCode: cip.code,
    });
  });
  socs.forEach((soc, i) => {
    for (const cipCode of soc.cips) {
      const cy = cipYByCode.get(cipCode);
      if (cy === undefined) continue;
      edges.push({
        d: bezier(CIP_X_R, cy, SOC_X_L, socYs[i]),
        kind: "cip-soc",
        cipCode,
        socCode: soc.code,
      });
    }
  });

  const nSoc = socs.length;
  const nCip = sortedCips.length;
  const topSelected = selection?.kind === "top";

  return (
    <div style={{ marginTop: 24 }}>
      {/* Headline — "TOP X crosswalks to N occupations", mirroring the
          occupations view's "N of M TOP groups crosswalk to SOC X". */}
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
        <span style={{ color: accent, fontFamily: MONO, fontWeight: 700 }}>
          TOP {crosswalk.top6}
        </span>{" "}
        crosswalks to{" "}
        <span style={{ color: accent, fontFamily: MONO, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
          {nSoc}
        </span>{" "}
        {nSoc === 1 ? "advanced manufacturing occupation" : "advanced manufacturing occupations"}
      </div>

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
        {crosswalk.top_name} prepares students for {nSoc}{" "}
        {nSoc === 1 ? "occupation" : "occupations"} through {nCip} federal{" "}
        {nCip === 1 ? "CIP" : "CIPs"}, mapped via the Chancellor&rsquo;s Office TOP-CIP
        crosswalk and the NCES CIP-SOC crosswalk to the federal occupation
        classification.
      </p>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        width="100%"
        style={{ display: "block", overflow: "visible" }}
        aria-label="TOP-CIP-SOC program pathway visualization"
        onClick={() => setSelection(null)}
      >
        {/* Column headers */}
        <text x={TOP_CX} y={HEADER_Y} fontFamily={MONO} fontSize={16} fontWeight={700} fill={accent} letterSpacing="0.4em" textAnchor="middle">
          T O P
        </text>
        <text x={(CIP_X_L + CIP_X_R) / 2} y={HEADER_Y} fontFamily={MONO} fontSize={16} fontWeight={700} fill={accent} letterSpacing="0.4em" textAnchor="middle">
          C I P
        </text>
        <text x={(SOC_X_L + SOC_X_R) / 2} y={HEADER_Y} fontFamily={MONO} fontSize={16} fontWeight={700} fill={accent} letterSpacing="0.4em" textAnchor="middle">
          S O C
        </text>

        {/* Edges first, badges layer on top. */}
        {edges.map((e, i) => {
          const hl =
            e.kind === "top-cip"
              ? highlightTopCipEdge(e.cipCode)
              : highlightCipSocEdge(e.cipCode, e.socCode!);
          const opacity = hl === null ? 0.6 : hl ? 0.95 : 0.07;
          const strokeWidth = hl ? 2.0 : 1.5;
          return (
            <path
              key={`edge-${i}`}
              d={e.d}
              fill="none"
              stroke={accent}
              strokeWidth={strokeWidth}
              opacity={opacity}
              style={{ transition: "opacity 0.18s, stroke-width 0.18s" }}
            />
          );
        })}

        {/* TOP anchor — the focus program, an emphasized green circle with the
            sun-gold ring. Clicking it lights the whole fan-out. */}
        {(() => {
          const lines = wrapToNLines(crosswalk.top_name, 16, 3);
          const CODE_FONT = 17;
          const NAME_FONT = 10;
          const NAME_LINE_H = 12;
          const blockH = CODE_FONT + 8 + lines.length * NAME_LINE_H;
          const blockTop = anchorY - blockH / 2;
          const codeY = blockTop + CODE_FONT - 2;
          const nameY0 = blockTop + CODE_FONT + 16;
          return (
            <g
              onClick={(ev) => {
                ev.stopPropagation();
                setSelection(topSelected ? null : { kind: "top" });
              }}
              style={{ cursor: "pointer" }}
            >
              <circle
                cx={TOP_CX}
                cy={anchorY}
                r={TOP_R}
                fill={accent}
                stroke={TAUGHT_GLOW}
                strokeWidth={topSelected ? 4 : 2}
                style={{ transition: "stroke-width 0.18s" }}
              />
              <text x={TOP_CX} y={codeY} fontFamily={MONO} fontSize={CODE_FONT} fontWeight={700} fill={BG} textAnchor="middle">
                {crosswalk.top6}
              </text>
              <text x={TOP_CX} y={nameY0} fontFamily={FONT} fontSize={NAME_FONT} fontWeight={600} fill={BG} textAnchor="middle">
                {lines.map((line, idx) => (
                  <tspan key={idx} x={TOP_CX} dy={idx === 0 ? 0 : NAME_LINE_H}>
                    {line}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })()}

        {/* CIP pills — federal-blue substrate. Click to isolate the CIP's
            feeder edge and the SOCs it bridges to. */}
        {sortedCips.map((cip, i) => {
          const y = cipYs[i];
          const lines = wrapToNLines(cip.title, CIP_TITLE_CHARS_PER_LINE, 2);
          const isTwoLine = lines.length === 2;
          const hl = highlightCip(cip.code);
          const sel = selection?.kind === "cip" && selection.code === cip.code;
          const opacity = hl === null ? 1 : hl ? 1 : 0.18;
          return (
            <g
              key={`cip-${cip.code}`}
              opacity={opacity}
              onClick={(ev) => {
                ev.stopPropagation();
                setSelection(sel ? null : { kind: "cip", code: cip.code });
              }}
              style={{ cursor: "pointer", transition: "opacity 0.18s" }}
            >
              <rect x={CIP_X_L} y={y - BADGE_H / 2} width={CIP_X_R - CIP_X_L} height={BADGE_H} rx={BADGE_H / 2} ry={BADGE_H / 2} fill={BG} stroke={CIP_COLOR} strokeWidth={sel ? 2.0 : 1.0} />
              <rect x={CIP_X_L} y={y - BADGE_H / 2 + 2} width={5} height={BADGE_H - 4} rx={2} fill={CIP_COLOR} />
              <text x={CIP_X_L + 18} y={y + 5} fontFamily={MONO} fontSize={12} fontWeight={700} fill={CIP_COLOR}>
                {cip.code}
              </text>
              <text x={CIP_X_L + 80} y={isTwoLine ? y - 3 : y + 5} fontFamily={FONT} fontSize={10.5} fill={INK_BODY}>
                <tspan x={CIP_X_L + 80}>{lines[0]}</tspan>
                {isTwoLine && <tspan x={CIP_X_L + 80} dy={13}>{lines[1]}</tspan>}
              </text>
            </g>
          );
        })}

        {/* SOC pills — the occupations this program feeds, in the lens accent.
            Click to isolate its bridging CIPs. */}
        {socs.map((soc, i) => {
          const y = socYs[i];
          const lines = wrapToNLines(soc.title, SOC_TITLE_CHARS_PER_LINE, 2);
          const isTwoLine = lines.length === 2;
          const hl = highlightSoc(soc.code);
          const sel = selection?.kind === "soc" && selection.code === soc.code;
          const opacity = hl === null ? 1 : hl ? 1 : 0.18;
          return (
            <g
              key={`soc-${soc.code}`}
              opacity={opacity}
              onClick={(ev) => {
                ev.stopPropagation();
                setSelection(sel ? null : { kind: "soc", code: soc.code });
              }}
              style={{ cursor: "pointer", transition: "opacity 0.18s" }}
            >
              <rect x={SOC_X_L} y={y - BADGE_H / 2} width={SOC_X_R - SOC_X_L} height={BADGE_H} rx={BADGE_H / 2} ry={BADGE_H / 2} fill={BG} stroke={accent} strokeWidth={sel ? 2.0 : 1.2} />
              <rect x={SOC_X_L} y={y - BADGE_H / 2 + 2} width={5} height={BADGE_H - 4} rx={2} fill={accent} />
              <text x={SOC_X_L + 18} y={y + 5} fontFamily={MONO} fontSize={12} fontWeight={700} fill={accent}>
                {soc.code}
              </text>
              <text x={SOC_X_L + 86} y={isTwoLine ? y - 3 : y + 5} fontFamily={FONT} fontSize={10.5} fill={INK_BODY}>
                <tspan x={SOC_X_L + 86}>{lines[0]}</tspan>
                {isTwoLine && <tspan x={SOC_X_L + 86} dy={13}>{lines[1]}</tspan>}
              </text>
            </g>
          );
        })}
      </svg>

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
        Pathways via the CCCCO PCAH TOP-CIP crosswalk and the NCES CIP-SOC
        crosswalk. Click a CIP or occupation to isolate its pathway.
      </p>
    </div>
  );
}

// ── helpers (mirrors CurriculumPathway) ─────────────────────────────────────

function bezier(x1: number, y1: number, x2: number, y2: number): string {
  const curvature = 0.55;
  const cx1 = x1 + (x2 - x1) * curvature;
  const cx2 = x2 - (x2 - x1) * curvature;
  return `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;
}

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
