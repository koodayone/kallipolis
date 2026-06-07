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
 * occupation DemandTreemap. Area = latest-year credentials awarded across the
 * consortium (supply IS awards/yr; enrollment is pipeline, not supply). Each
 * cell is a TOP6 program and is itself the picker (click → select); the selected
 * cell carries a white ring. Programs that awarded nothing in the latest year
 * have no area and so don't appear here.
 */
export default function SupplyTreemap({
  tops, selectedTop, onSelect, accent = "#50c878", caption, fill = false,
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
}) {
  const [hover, setHover] = useState<{ i: number; x: number; y: number } | null>(null);
  const { ref: boxRef, box } = useMeasuredBox(fill);
  const data = tops
    .filter((t) => t.awards_total > 0)
    .map((t) => ({ top: t.top6, name: t.name, v: t.awards_total, socs: t.soc_count }))
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
      return (
        <g key={d.top} onMouseMove={(e) => setHover({ i, x: e.clientX, y: e.clientY })} onClick={() => onSelect?.(d.top)} style={{ cursor: onSelect ? "pointer" : "default" }}>
          <rect
            x={r.x + g / 2} y={r.y + g / 2}
            width={Math.max(r.w - g, 0)} height={Math.max(r.h - g, 0)} rx={3}
            fill={color(i)}
            opacity={hover != null && hover.i !== i && !sel ? 0.4 : 1}
            stroke={sel ? "rgba(255,255,255,.92)" : "transparent"}
            strokeWidth={sel ? 2 : 0}
          />
          {(() => {
            const pad = 8, cw = 0.6;
            const availW = r.w - 2 * pad;
            if (availW < 22 || r.h < 18) return null;
            const full = `TOP ${d.top}`;
            const label = availW / (full.length * cw) >= 7 ? full : d.top;
            const fs = Math.max(7, Math.min(11.5, availW / (label.length * cw)));
            const lh = fs + 3;
            const two = r.h >= 2 * lh + 4;
            return (
              <g style={{ pointerEvents: "none" }}>
                <text x={r.x + pad} y={r.y + pad + fs - 1} style={{ fontFamily: MONO, fontSize: fs, fontWeight: 500, fill: "#fff" }}>{label}</text>
                {two && <text x={r.x + pad} y={r.y + pad + fs - 1 + lh} style={{ fontFamily: MONO, fontSize: Math.max(fs - 1, 6.5), fill: "rgba(255,255,255,.82)" }}>{d.v.toLocaleString()}/yr</text>}
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
          No credentials were awarded in the latest year for these programs.
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
      <div style={{ fontFamily: FONT, fontSize: 12.5, color: "#9aa6bd", marginTop: 10 }}>
        {caption ?? "Area is latest-year credentials awarded across the consortium — click a program to open its report."}
      </div>
      {hd && hover && typeof document !== "undefined" && createPortal(
        <div style={{
          position: "fixed", left: Math.min(hover.x + 14, window.innerWidth - 356), top: hover.y + 14,
          pointerEvents: "none", zIndex: 1000, maxWidth: 340,
          background: "#0b1530", border: "1px solid rgba(255,255,255,.09)", borderRadius: 8,
          padding: "8px 11px", boxShadow: "0 6px 24px rgba(0,0,0,.4)", fontFamily: FONT,
        }}>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: "#e8ecf4", marginBottom: 2 }}>{hd.name}</div>
          <div style={{ fontFamily: MONO, fontSize: 11, color: accent, whiteSpace: "nowrap" }}>TOP {hd.top} · {hd.v.toLocaleString()} awards/yr · supports {hd.socs} occupation{hd.socs === 1 ? "" : "s"}</div>
        </div>,
        document.body,
      )}
    </div>
  );
}
