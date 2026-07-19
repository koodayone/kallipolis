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
// A priority split: render the first `after` rows, then a muted expander that
// reveals the rest under a labeled section naming the `criteria` the split reads
// on. Omit (or null) ⇒ every row renders flat, the report's behavior unchanged.
export type CoverageSplit = { after: number; restLabel: string; criteria: string[] };

function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}

const LABEL_W = 262;        // unit-label column (px) — fits the occupation demand line (SOC · openings/yr · wage/yr)
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
  // flush: drop the standalone figure chrome (top margin + bordered card) —
  // for the dashboard, where the DashPanel is the card and the matrix should
  // sit flush in it. Default false ⇒ the report's figure, unchanged.
  flush?: boolean;
  // Priority-default: split the rows into a leading in-demand set and a collapsed
  // rest. Omitted ⇒ no split (all rows render).
  split?: CoverageSplit | null;
};

// Selection reads as white-glow everywhere — the whole-row bracket (aggregate)
// and the single-cell ring (targeted) share this neutral language, so the
// matrix's color budget stays with the data (per-college coverage shades).
const SEL_RING = "rgba(255,255,255,.85)";
const SEL_TEXT = "rgba(255,255,255,.98)";
const SEL_GLOW = "0 0 8px rgba(255,255,255,.35)";

export default function CoverageMatrix({
  cols, rows, level, selectedRow, selectedCol, cornerLabel, gapCellHint, legend, caption, onSelect, onSelectRow, flush = false, split = null,
}: Props) {
  // ROW mode = a row is selected with no specific column (aggregate / treemap)
  // → neutral white glow. CELL mode (a specific college) → that college's brand.
  const rowMode = selectedRow != null && selectedCol == null;
  const selColBrand = cols.find((c) => c.id === selectedCol)?.brand ?? SEL_TEXT;
  // Label hover previews the whole-row selection (a ghosted bracket), so the
  // unit column self-evidently reads as a row selector.
  const [hoverRow, setHoverRow] = useState<string | null>(null);
  // The priority split's rest section is collapsed by default; the expander toggles it.
  const [restOpen, setRestOpen] = useState(false);

  // Many-column (consortium-level) joins flip the headers vertical: 26 college
  // names sit directly over their cells with no diagonal bleed, so columns pack
  // tighter and alignment is unambiguous. Few-column instances (SVAMP=5,
  // SMCCD=3) keep the horizontal headers unchanged — vertical is purely the
  // consortium accommodation. The threshold (12) is the point past which
  // horizontal labels stop fitting their cells.
  const vertical = cols.length > 12;
  const cellMin = vertical ? 32 : CELL_MIN;   // tighter cells when many columns
  const VHEAD = 134;                            // vertical-header row height (px)

  // flush also makes the matrix HEIGHT-RESPONSIVE: rows flex-grow over their
  // natural sizes (never shrink — in auto bands the matrix still defines its
  // row height), so an expanded panel's surplus distributes into the rows
  // and the swatches stretch with them (cell size encodes nothing, so
  // stretching is semantically free — unlike value-encoding marks).

  // One unit row: the label (name + demand sublabel) then a coverage cell per
  // college. Extracted so the priority slice and the collapsed rest map the same body.
  const renderRow = (row: CoverageRow) => {
    const rowSel = row.id === selectedRow;
    const rowHalo = rowMode && rowSel;                     // bracket the whole selected row
    const rowPreview = hoverRow === row.id && !rowHalo;    // label-hover ghost
    return (
      <div
        key={"r-" + row.id}
        style={{
          display: "flex", gap: 4, alignItems: flush ? "stretch" : "center", padding: ROW_PAD, borderRadius: 8,
          // Height-responsive stretch only when the full row set is fixed. A split's
          // visible count changes on expand, so its rows keep natural height instead.
          ...(flush && !split ? { flex: "1 0 auto" } : {}),
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
          style={{ flex: `0 0 ${LABEL_W}px`, minWidth: 0, paddingRight: 14, cursor: onSelectRow ? "pointer" : "default", ...(flush ? { display: "flex", flexDirection: "column", justifyContent: "center" } : {}) }}
        >
          <div style={{ fontSize: 12.5, fontWeight: rowSel ? 600 : 500, color: rowSel ? (rowMode ? SEL_TEXT : selColBrand) : "rgba(255,255,255,.82)", textShadow: rowMode && rowSel ? SEL_GLOW : "none", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{row.label}</div>
          <div style={{ fontFamily: MONO, fontSize: 10, color: rowSel ? (rowMode ? "rgba(255,255,255,.6)" : selColBrand) : "#5e6a83", letterSpacing: ".02em", marginTop: 1, transition: "color .15s", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", fontVariantNumeric: "tabular-nums" }}>{row.sublabel}</div>
        </div>
        {cols.map((col) => {
          const lv = level(row.id, col.id);
          const brand = col.brand;
          const isSel = col.id === selectedCol && row.id === selectedRow;
          const isGap = lv === "none";
          const gapBg = "rgba(255,255,255,.035)";
          const base: CSSProperties = {
            flex: "1 1 0", minWidth: cellMin, borderRadius: 7, cursor: "pointer",
            ...(flush ? { minHeight: 32 } : { height: 32 }),
            background: isGap ? gapBg : lv === "strong" ? hexA(brand, 0.9) : hexA(brand, 0.3),
            boxShadow: isGap ? "none" : `inset 0 0 0 1px ${hexA(brand, 0.5)}`,
            transition: "transform .12s, box-shadow .12s, background .12s",
          };
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
  };

  // Priority-default: with a split, render the in-demand rows, then a MUTED
  // expander revealing the rest under a labeled section that names the criteria
  // (the gold pills — the one place the eye should land when the rest opens).
  const renderRows = () => {
    const active = split != null && split.after >= 0 && split.after < rows.length;
    if (!active) return rows.map(renderRow);
    const s = split as CoverageSplit;
    const priority = rows.slice(0, s.after);
    const rest = rows.slice(s.after);
    const restIds = new Set(rest.map((r) => r.id));
    // Auto-reveal when a collapsed row is the current selection (e.g. picked from
    // the treemap): the selected row must never hide behind the expander.
    const shown = restOpen || (selectedRow != null && restIds.has(selectedRow));
    // Expander + section chrome keep their natural height in flush mode (only the
    // data rows flex-grow), so the split doesn't distort the row-stretch math.
    const flexNat = flush ? { flex: "0 0 auto" as const } : {};
    return (
      <>
        {priority.map(renderRow)}
        <div style={{ padding: "12px 6px 4px", ...flexNat }}>
          <button
            type="button"
            aria-expanded={shown}
            onClick={() => setRestOpen((o) => !o)}
            onMouseEnter={(e) => { const el = e.currentTarget; el.style.color = "#9aa6bd"; el.style.background = "rgba(255,255,255,.035)"; el.style.borderColor = "rgba(255,255,255,.08)"; }}
            onMouseLeave={(e) => { const el = e.currentTarget; el.style.color = "#5e6a83"; el.style.background = "none"; el.style.borderColor = "transparent"; }}
            style={{ display: "inline-flex", alignItems: "center", gap: 9, background: "none", border: "1px solid transparent", cursor: "pointer", fontFamily: MONO, fontSize: 11.5, letterSpacing: ".03em", color: "#5e6a83", padding: "8px 13px", borderRadius: 9, transition: "color .16s, background .16s, border-color .16s" }}
          >
            <span style={{ fontSize: 10, transition: "transform .2s", transform: shown ? "rotate(90deg)" : "none" }}>▸</span>
            {`+ ${rest.length} more`}
          </button>
        </div>
        {shown && (
          <>
            <div style={{ height: 1, background: "rgba(255,255,255,.06)", margin: "10px 6px", ...flexNat }} />
            <div style={{ display: "flex", alignItems: "center", gap: 9, flexWrap: "wrap", padding: "8px 6px 12px", ...flexNat }}>
              <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: ".08em", textTransform: "uppercase", color: "#5e6a83" }}>{s.restLabel}</span>
              {s.criteria.map((c) => (
                <span key={c} style={{ fontFamily: MONO, fontSize: 10, color: "#9aa6bd", border: "1px solid rgba(255,255,255,.14)", borderRadius: 999, padding: "2px 9px", whiteSpace: "nowrap" }}>{c}</span>
              ))}
            </div>
            {rest.map(renderRow)}
          </>
        )}
      </>
    );
  };

  return (
    <>
    <div style={flush ? { overflowX: "auto", padding: "4px 2px 0", flex: 1, minHeight: 0, display: "flex", flexDirection: "column" } : { marginTop: 20, border: "1px solid rgba(255,255,255,.09)", borderRadius: 12, background: "rgba(0,0,0,.18)", padding: "16px 18px", overflowX: "auto" }}>
      <div style={{ minWidth: LABEL_W + cols.length * (cellMin + 4), ...(flush ? { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" } : {}) }}>
        {/* header row */}
        <div style={{ display: "flex", gap: 4, alignItems: "flex-end", padding: "0 6px" }}>
          <div style={{ flex: `0 0 ${LABEL_W}px`, fontFamily: MONO, fontSize: 9.5, letterSpacing: ".1em", textTransform: "uppercase", color: "#5e6a83", whiteSpace: "nowrap", paddingBottom: 11 }}>
            {cornerLabel}
          </div>
          {cols.map((col) => {
            const on = col.id === selectedCol;
            return vertical ? (
              // Vertical header — the name reads bottom-to-top directly over its
              // column (no diagonal bleed); a 2px brand bar at the base ties the
              // color to the column in lieu of the inline dot.
              <div key={"h-" + col.id} style={{ flex: "1 1 0", minWidth: cellMin, position: "relative", height: VHEAD, borderBottom: `2px solid ${on ? col.brand : hexA(col.brand, 0.5)}` }}>
                <div style={{ position: "absolute", bottom: 9, left: "50%", transform: "translateX(-50%) rotate(180deg)", writingMode: "vertical-rl", whiteSpace: "nowrap", fontSize: 11, fontWeight: 600, color: on ? col.brand : "#9aa6bd", transition: "color .15s" }}>
                  {col.label}
                </div>
              </div>
            ) : (
              <div key={"h-" + col.id} style={{ flex: "1 1 0", minWidth: cellMin, display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 11.5, fontWeight: 600, paddingBottom: 11, color: on ? col.brand : "#9aa6bd", boxShadow: on ? `inset 0 -2px 0 ${col.brand}` : "none", transition: "color .15s" }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: col.brand, flex: "none" }} />
                {col.label}
              </div>
            );
          })}
        </div>

        {/* unit rows — priority-default; the rest collapse behind the expander
            when a split is given (else every row renders, unchanged). */}
        {renderRows()}

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
