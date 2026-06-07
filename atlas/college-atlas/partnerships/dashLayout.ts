/**
 * Dashboard band layout policy — pure, no React.
 *
 * The dashboard's grammar (bands of panels) is separate from its rendition:
 * which panels share a row is a FUNCTION OF MEASURED SPACE, computed here from
 * each panel's intrinsic minimum width. One algorithm serves every width —
 * full monitors, half-snapped windows, laptops, phones — so there is no
 * viewport gate and no parallel "mobile layout". Kept pure so the row
 * invariants are unit-testable without a DOM (the repo's pure-assembly
 * pattern; see backend/partnerships/svamp.py's _assemble_landscape).
 *
 * Invariants the tests pin:
 *   - declared order is never reordered (identity preservation: a familiar
 *     layout compresses, it never rearranges);
 *   - a panel joins the open row only while every member can still get its
 *     declared minimum (sum of minWidths + gaps ≤ width);
 *   - a panel wider than the container still renders (its own row — the
 *     panel's internal overflow handles sub-minimum widths).
 */

/** Default intrinsic minimum for panels that don't declare one — the trend
 *  charts' fill-mode clamp (chartKit PLOT) is the narrowest legible chart. */
export const DEFAULT_PANEL_MIN_WIDTH = 320;

/** Floor at which the crosswalk pathway diagrams stop scaling down and start
 *  panning instead (the CoverageMatrix precedent: below intrinsic min, pan —
 *  never scale text below legibility). Consumed by ProgramPathway /
 *  CurriculumPathway fill mode. */
export const PATHWAY_MIN_RENDER_W = 500;

export type LayoutPanelMeta = {
  id: string;
  weight?: number;   // fr share when co-rowed (default 1)
  minWidth?: number; // intrinsic minimum px (default DEFAULT_PANEL_MIN_WIDTH)
  height?: number;   // target row height px; absent ⇒ content-driven
};

export type LayoutRow = {
  ids: string[];               // member panel ids, declared order preserved
  height: number | "auto";     // max of declared member heights, else "auto"
};

/** Row height rule: the max of the members' declared heights (rendered as
 *  minmax(min-content, Xpx) — a target, never a clip), or "auto" when no
 *  member declares one. Shared by the lab path's one-row-per-band rendering. */
export function rowHeight(panels: LayoutPanelMeta[]): number | "auto" {
  const declared = panels.map((p) => p.height).filter((h): h is number => h != null);
  return declared.length ? Math.max(...declared) : "auto";
}

/**
 * Assign a band's panels to rows for a measured width.
 *
 * Greedy first-fit in DECLARED order: a panel joins the open row while
 * sum(member minWidths) + gap·(n−1) ≤ width; otherwise it opens a new row.
 * No reordering and no backfill — a small panel after a too-wide one starts
 * the next row rather than jumping back, so the reading order is always the
 * declared order. A panel whose own minimum exceeds the width still gets a
 * row (rendered minmax(0,1fr); its internal overflow governs below minimum).
 */
export function computeBandRows(
  panels: LayoutPanelMeta[],
  width: number,
  gap: number,
): LayoutRow[] {
  const rows: LayoutPanelMeta[][] = [];
  let open: LayoutPanelMeta[] = [];
  let openMin = 0; // sum of open row's minWidths + inner gaps

  for (const p of panels) {
    const min = p.minWidth ?? DEFAULT_PANEL_MIN_WIDTH;
    if (open.length && openMin + gap + min <= width) {
      open.push(p);
      openMin += gap + min;
    } else {
      if (open.length) rows.push(open);
      open = [p];
      openMin = min;
    }
  }
  if (open.length) rows.push(open);

  return rows.map((members) => ({
    ids: members.map((m) => m.id),
    height: rowHeight(members),
  }));
}
