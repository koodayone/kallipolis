"use client";

import React, { useState } from "react";
import { createPortal } from "react-dom";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { useMeasuredBox } from "@/college-atlas/partnerships/chartKit";
import { squarify } from "@/college-atlas/partnerships/treemap";
import type { ApiSvampTopSummary } from "@/college-atlas/partnerships/api";

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

/**
 * Supply hero + picker for the SVAMP Programs lens — the mirror of the
 * occupation DemandTreemap. Area = projected annual supply (3-year-average
 * credentials awarded) across the consortium (supply IS awards/yr; enrollment is
 * pipeline, not supply) — the same supply definition the occupation landscape and
 * the MCP use. Each cell is a TOP6 program and is itself the picker (click →
 * select); the selected cell carries a white ring. Programs that awarded nothing
 * in the recent window have no area and so don't appear here.
 */
export default function SupplyTreemap({
  tops, selectedTop, onSelect, accent = "#50c878", caption, fill = false, scope = null,
}: {
  tops: ApiSvampTopSummary[];
  selectedTop: string | null;
  // Omitted ⇒ display-only (no picker affordance) — used by the aggregated
  // occupation view to show the programs feeding the SOC.
  onSelect?: (top6: string) => void;
  accent?: string;
  caption?: string;
  // fill: lay the treemap out in the CONTAINER's measured pixel space, so the
  // blocks re-proportion to whatever size the panel manifests at (the
  // dashboard). Default false ⇒ the report's fixed 860×300 figure, unchanged.
  fill?: boolean;
  // Scope overlay (part-to-whole). When a college is in scope, the box area STILL
  // encodes the program's regional supply, but a fill from the base shows THAT
  // college's share of it, and labels/tooltip read its own number + "% of region".
  // Null ⇒ consortium scope: the plain regional treemap, unchanged.
  scope?: { label: string; byTop: Record<string, number> } | null;
}) {
  const [hover, setHover] = useState<{ i: number; x: number; y: number } | null>(null);
  const { ref: boxRef, box } = useMeasuredBox(fill);
  const data = tops
    .filter((t) => t.projected_supply > 0)
    .map((t) => {
      const pv = scope ? (scope.byTop[t.top6] ?? 0) : null;
      return { top: t.top6, name: t.name, v: t.projected_supply, socs: t.soc_count, pv, share: pv != null ? pv / t.projected_supply : null };
    })
    .sort((a, b) => b.v - a.v);
  const W = fill ? Math.max(box?.w ?? 0, 1) : 860;
  const H = fill ? Math.max(box?.h ?? 0, 1) : 300;
  const g = 2;
  const rects = data.length && (!fill || box) ? squarify(data.map((d) => d.v), 0, 0, W, H) : [];
  const color = (i: number) => hexA(accent, 1 - (i / Math.max(data.length - 1, 1)) * 0.62);
  const hd = hover != null ? data[hover.i] : null;

  const renderCells = () =>
    data.map((d, i) => {
      const r = rects[i];
      const sel = d.top === selectedTop;
      const bx = r.x + g / 2, by = r.y + g / 2, bw = Math.max(r.w - g, 0), bh = Math.max(r.h - g, 0);
      // Part-to-whole (college view): the box area is the regional supply; the
      // fill from the base is the scope college's share of it.
      const fillH = d.share != null ? bh * d.share : 0;
      const pct = d.share != null ? Math.round(d.share * 100) : null;
      return (
        <g
          key={d.top}
          onMouseMove={(e) => setHover({ i, x: e.clientX, y: e.clientY })}
          onClick={() => onSelect?.(d.top)}
          style={{ cursor: onSelect ? "pointer" : "default", opacity: hover != null && hover.i !== i && !sel ? 0.45 : 1 }}
        >
          <rect
            x={bx} y={by} width={bw} height={bh} rx={3}
            fill={scope ? hexA(accent, 0.16) : color(i)}
            stroke={sel ? "rgba(255,255,255,.92)" : scope ? hexA(accent, 0.34) : "transparent"}
            strokeWidth={sel ? 2 : scope ? 1 : 0}
          />
          {scope && fillH > 0.5 && (
            <rect x={bx} y={by + bh - fillH} width={bw} height={fillH} rx={Math.min(3, fillH / 2)} fill={hexA(accent, 0.92)} style={{ pointerEvents: "none" }} />
          )}
          {(() => {
            const pad = 8, cw = 0.6;
            const availW = bw - 2 * pad;
            if (availW < 22 || bh < 18) return null;
            const full = `TOP ${d.top}`;
            const label = availW / (full.length * cw) >= 7 ? full : d.top;
            const fs = Math.max(7, Math.min(11.5, availW / (label.length * cw)));
            const lh = fs + 3;
            const two = bh >= 2 * lh + 4;
            const three = bh >= 3 * lh + 4;
            const primVal = d.pv != null ? `${d.pv.toLocaleString(undefined, { maximumFractionDigits: 1 })}/yr` : "";
            const line2 = scope ? (three ? primVal : `${primVal} · ${pct}%`) : `${d.v.toLocaleString()}/yr`;
            return (
              <g style={{ pointerEvents: "none" }}>
                <text x={bx + pad} y={by + pad + fs - 1} style={{ fontFamily: MONO, fontSize: fs, fontWeight: 500, fill: "#fff" }}>{label}</text>
                {two && <text x={bx + pad} y={by + pad + fs - 1 + lh} style={{ fontFamily: MONO, fontSize: Math.max(fs - 1, 6.5), fill: "rgba(255,255,255,.85)" }}>{line2}</text>}
                {scope && three && <text x={bx + pad} y={by + pad + fs - 1 + 2 * lh} style={{ fontFamily: MONO, fontSize: Math.max(fs - 1.5, 6.5), fill: "rgba(255,255,255,.66)" }}>{pct}% of region</text>}
              </g>
            );
          })()}
        </g>
      );
    });

  return (
    <div style={fill ? { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } : { marginTop: 14 }}>
      {data.length === 0 ? (
        <div style={{ fontFamily: FONT, fontSize: 13, color: "#9aa6bd", padding: "40px 0", textAlign: "center" }}>
          No credentials were awarded recently for these programs.
        </div>
      ) : fill ? (
        // Measured-space layout: svg pixels == layout units, so nothing
        // stretches and labels stay crisp at any panel shape.
        <div ref={boxRef} style={{ flex: 1, minHeight: 0 }}>
          {box && (
            <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }} onMouseLeave={() => setHover(null)}>
              {renderCells()}
            </svg>
          )}
        </div>
      ) : (
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ display: "block", height: H }} onMouseLeave={() => setHover(null)}>
          {renderCells()}
        </svg>
      )}
      {/* Caption is report-only — the dashboard visualizes without prose. */}
      {!fill && (
        <div style={{ fontFamily: FONT, fontSize: 12.5, color: "#9aa6bd", marginTop: 10 }}>
          {caption ?? "Area is projected annual supply (3-year average) across the consortium — click a program to open its report."}
        </div>
      )}
      {hd && hover && typeof document !== "undefined" && createPortal(
        <div style={{
          position: "fixed", left: Math.min(hover.x + 14, window.innerWidth - 356), top: hover.y + 14,
          pointerEvents: "none", zIndex: 1000, maxWidth: 340,
          background: "#0b1530", border: "1px solid rgba(255,255,255,.09)", borderRadius: 8,
          padding: "8px 11px", boxShadow: "0 6px 24px rgba(0,0,0,.4)", fontFamily: FONT,
        }}>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: "#e8ecf4", marginBottom: 2 }}>{hd.name}</div>
          <div style={{ fontFamily: MONO, fontSize: 11, color: accent, whiteSpace: scope ? "normal" : "nowrap" }}>
            {scope && hd.pv != null
              ? `TOP ${hd.top} · ${scope.label} ${hd.pv.toLocaleString(undefined, { maximumFractionDigits: 1 })}/yr of ${hd.v.toLocaleString()}/yr region · ${Math.round((hd.share ?? 0) * 100)}% of region · supports ${hd.socs} occupation${hd.socs === 1 ? "" : "s"}`
              : `TOP ${hd.top} · ${hd.v.toLocaleString()}/yr projected · supports ${hd.socs} occupation${hd.socs === 1 ? "" : "s"}`}
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
