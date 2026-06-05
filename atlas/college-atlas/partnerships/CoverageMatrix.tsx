/**
 * CoverageMatrix — the shared (unit × college) coverage grid used by both SVAMP
 * lenses. Occupations: rows = SOC occupations, cell = does this college's
 * curriculum prepare for it + has supply. Programs: rows = TOP programs, cell =
 * does this college teach it + has awards. Same visual language, dual meaning.
 *
 * Two selection modes, expressed distinctly:
 *   • ROW mode (aggregate / treemap or unit-label selection): a row is selected
 *     with no column → the whole row gets a white-glow bracket. The other rows
 *     stay fully legible so the coverage topology (gaps, depth per college)
 *     remains scannable — no dimming.
 *   • CELL mode (targeted / matrix-cell selection): a (row, col) is selected →
 *     that cell carries the white perimeter ring with a brand-tinted glow, and
 *     the row's label + column header adopt the college's brand.
 *
 * Rendered as per-row flex containers (not one flat grid) so row-level styling
 * is clean. `level()` returns gap/partial/strong per (rowId, colId).
 */

"use client";

import { useState, type CSSProperties } from "react";
import { MONO } from "@/college-atlas/partnerships/reportChrome";

export type CoverageLevel = "none" | "partial" | "strong";
export type CoverageCol = { id: string; label: string; brand: string };
export type CoverageRow = { id: string; label: string; sublabel: string; title: string };
export type CoverageLegendEntry = { k: string; sub: string; bg: string; ring: boolean };

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

const LABEL_W = 230;        // unit-label column (px)
const CELL_MIN = 58;        // min data-cell width (px)
const ROW_PAD = "4px 6px";  // row padding — gives the bracket breathing room

type Props = {
  cols: CoverageCol[];
  rows: CoverageRow[];
  level: (rowId: string, colId: string) => CoverageLevel;
  selectedRow: string | null;
  selectedCol: string | null;
  cornerLabel: string;
  gapCellHint: string;
  legend: CoverageLegendEntry[];
  caption?: string;   // one-line interaction caption under the card
  onSelect: (rowId: string, colId: string) => void;
  // Clicking the unit label selects the whole row (the aggregate view), the
  // same entry the treemap provides. Omitted ⇒ labels aren't clickable.
  onSelectRow?: (rowId: string) => void;
};

// Selection reads as white-glow everywhere — the whole-row bracket (aggregate)
// and the single-cell ring (targeted) share this neutral language, so the
// matrix's color budget stays with the data (per-college coverage shades).
const SEL_RING = "rgba(255,255,255,.85)";
const SEL_TEXT = "rgba(255,255,255,.98)";
const SEL_GLOW = "0 0 8px rgba(255,255,255,.35)";

export default function CoverageMatrix({
  cols, rows, level, selectedRow, selectedCol, cornerLabel, gapCellHint, legend, caption, onSelect, onSelectRow,
}: Props) {
  // ROW mode = a row is selected with no specific column (aggregate / treemap)
  // → neutral white glow. CELL mode (a specific college) → that college's brand.
  const rowMode = selectedRow != null && selectedCol == null;
  const selColBrand = cols.find((c) => c.id === selectedCol)?.brand ?? SEL_TEXT;
  // Label hover previews the whole-row selection (a ghosted bracket), so the
  // unit column self-evidently reads as a row selector.
  const [hoverRow, setHoverRow] = useState<string | null>(null);

  return (
    <>
    <div style={{ marginTop: 20, border: "1px solid rgba(255,255,255,.09)", borderRadius: 12, background: "rgba(0,0,0,.18)", padding: "16px 18px", overflowX: "auto" }}>
      <div style={{ minWidth: LABEL_W + cols.length * (CELL_MIN + 4) }}>
        {/* header row */}
        <div style={{ display: "flex", gap: 4, alignItems: "flex-end", padding: "0 6px" }}>
          <div style={{ flex: `0 0 ${LABEL_W}px`, fontFamily: MONO, fontSize: 9.5, letterSpacing: ".1em", textTransform: "uppercase", color: "#5e6a83", whiteSpace: "nowrap", paddingBottom: 11 }}>
            {cornerLabel}
          </div>
          {cols.map((col) => {
            const on = col.id === selectedCol;
            return (
              <div key={"h-" + col.id} style={{ flex: "1 1 0", minWidth: CELL_MIN, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 11.5, fontWeight: 600, paddingBottom: 11, color: on ? col.brand : "#9aa6bd", boxShadow: on ? `inset 0 -2px 0 ${col.brand}` : "none", transition: "color .15s" }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: col.brand, flex: "none" }} />
                {col.label}
              </div>
            );
          })}
        </div>

        {/* unit rows */}
        {rows.map((row) => {
          const rowSel = row.id === selectedRow;
          const rowHalo = rowMode && rowSel;   // bracket the whole selected row
          const rowPreview = hoverRow === row.id && !rowHalo;  // label-hover ghost
          // No dimming of the other rows — the full coverage topology (gaps,
          // depth per college) stays scannable; the bracket alone marks the row.
          return (
            <div
              key={"r-" + row.id}
              style={{
                display: "flex", gap: 4, alignItems: "center", padding: ROW_PAD, borderRadius: 8,
                boxShadow: rowHalo
                  ? `inset 0 0 0 1.5px ${SEL_RING}, 0 0 14px rgba(255,255,255,.12)`
                  : rowPreview ? "inset 0 0 0 1.5px rgba(255,255,255,.28)" : "none",
                transition: "box-shadow .18s",
              }}
            >
              <div
                title={row.title}
                onClick={() => onSelectRow?.(row.id)}
                onMouseEnter={() => setHoverRow(row.id)}
                onMouseLeave={() => setHoverRow(null)}
                style={{ flex: `0 0 ${LABEL_W}px`, minWidth: 0, paddingRight: 14, cursor: onSelectRow ? "pointer" : "default" }}
              >
                <div style={{ fontSize: 12.5, fontWeight: rowSel ? 600 : 500, color: rowSel ? (rowMode ? SEL_TEXT : selColBrand) : "rgba(255,255,255,.82)", textShadow: rowMode && rowSel ? SEL_GLOW : "none", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{row.label}</div>
                <div style={{ fontFamily: MONO, fontSize: 10, color: rowSel ? (rowMode ? "rgba(255,255,255,.6)" : selColBrand) : "#5e6a83", letterSpacing: ".02em", marginTop: 1, transition: "color .15s" }}>{row.sublabel}</div>
              </div>
              {cols.map((col) => {
                const lv = level(row.id, col.id);
                const brand = col.brand;
                const isSel = col.id === selectedCol && row.id === selectedRow;
                const isGap = lv === "none";
                const gapBg = "rgba(255,255,255,.035)";
                const base: CSSProperties = {
                  flex: "1 1 0", minWidth: CELL_MIN, height: 32, borderRadius: 7, cursor: "pointer",
                  background: isGap ? gapBg : lv === "strong" ? hexA(brand, 0.9) : hexA(brand, 0.3),
                  boxShadow: isGap ? "none" : `inset 0 0 0 1px ${hexA(brand, 0.5)}`,
                  transition: "transform .12s, box-shadow .12s, background .12s",
                };
                // Individual-college (cell) selection: white perimeter ring with
                // a brand-tinted glow — the white frame is the "selected" signal,
                // the glow ties it to the college (whose brand also colors the row
                // label + column header).
                const sel: CSSProperties = isSel
                  ? isGap
                    ? { boxShadow: "0 0 0 2px rgba(255,255,255,.85), 0 6px 16px rgba(0,0,0,.5)", transform: "scale(1.08)", zIndex: 2 }
                    : { boxShadow: `0 0 0 2px rgba(255,255,255,.92), 0 0 12px ${hexA(brand, 0.6)}, 0 6px 16px rgba(0,0,0,.5)`, transform: "scale(1.08)", zIndex: 2 }
                  : {};
                return (
                  <div
                    key={col.id + "-" + row.id}
                    title={isGap ? `${col.label} · ${row.title} — ${gapCellHint}` : `${col.label} · ${row.title}`}
                    onClick={() => onSelect(row.id, col.id)}
                    onMouseEnter={(e) => { if (isSel) return; const el = e.currentTarget as HTMLElement; el.style.transform = "translateY(-2px)"; if (isGap) el.style.background = "rgba(255,255,255,.08)"; }}
                    onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; if (isGap) el.style.background = gapBg; if (!isSel) el.style.transform = "none"; }}
                    style={{ ...base, ...sel }}
                  />
                );
              })}
            </div>
          );
        })}

        {/* legend — spacer in the label column, swatches across the data columns */}
        <div style={{ display: "flex", gap: 4, marginTop: 16, borderTop: "1px solid rgba(255,255,255,.06)", padding: "13px 6px 0" }}>
          <div style={{ flex: `0 0 ${LABEL_W}px` }} />
          <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 48, flexWrap: "wrap" }}>
            {legend.map((it) => (
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
    </div>
    {caption && (
      <div style={{ fontSize: 12.5, color: "#9aa6bd", marginTop: 10, lineHeight: 1.5 }}>
        {caption}
      </div>
    )}
    </>
  );
}
