"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { hexA } from "@/college-atlas/partnerships/chartKit";
import { squarify } from "@/college-atlas/partnerships/treemap";
import type { ApiSvampCell } from "@/college-atlas/partnerships/api";

// Occupations-lens demand red (SvampView's module ACCENT, mirrored verbatim so
// the extraction is behavior-identical).
const ACCENT = "#ff5a5a";

// ── Demand composition hero (treemap) ─────────────────────────────────────
// Squarified treemap: area = annual openings, so the rectangle is the regional
// total. Cells label the SOC code + openings (the full title is surfaced in the
// readout on hover) — compact and visual rather than prose-in-cell.
function DemandTreemap({ cells, total, selected, onSelect }: { cells: ApiSvampCell[]; total: number; selected?: string | null; onSelect?: (soc: string) => void }) {
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
            <g key={d.soc} onMouseMove={(e) => setHover({ i, x: e.clientX, y: e.clientY })} onClick={() => onSelect?.(d.soc)} style={{ cursor: onSelect ? "pointer" : "default" }}>
              <rect x={r.x + g / 2} y={r.y + g / 2} width={Math.max(r.w - g, 0)} height={Math.max(r.h - g, 0)} rx={3} fill={color(i)} opacity={hover != null && hover.i !== i ? 0.4 : 1} stroke={d.soc === selected ? "#fff" : "none"} strokeWidth={d.soc === selected ? 2.5 : 0} />
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
        Area is annual openings. The top three occupations account for <span style={{ color: "#e8ecf4", fontWeight: 600 }}>{top3sh}%</span> of regional demand — click an occupation for the consortium view.
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

export default DemandTreemap;
