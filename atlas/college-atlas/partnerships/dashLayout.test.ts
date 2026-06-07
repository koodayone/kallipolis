/**
 * Tests for dashLayout — the pure band-layout policy that turns each band's
 * panel manifest (id, weight, minWidth, height) plus a measured width into
 * rows, replacing the dashboard's former ≥1440px viewport gate.
 *
 * The function is the load-bearing piece of the responsive re-architecture:
 * if it reorders panels or lets a row overflow its members' minimums, the
 * dashboard either rearranges under the user (identity loss) or clips a
 * visualization. Pure function, no DOM — pinned the same way the backend
 * pins its aggregation invariants on pure assembly functions.
 *
 * Coverage:
 *   - exact-fit boundary: panels whose minimums + gap equal the width share a row
 *   - split at the first panel that no longer fits, preserving declared order
 *   - no backfill: a small panel after a too-wide one opens a new row rather
 *     than rejoining an earlier one
 *   - a panel wider than the container still gets its own row (never dropped)
 *   - gap accounting: N panels need sum(minWidths) + (N−1)·gap
 *   - DEFAULT_PANEL_MIN_WIDTH applies when minWidth is omitted
 *   - width 0 (and widths below every minimum) ⇒ every panel solo
 *   - empty panel list ⇒ no rows
 *   - four-panel continuum: 4 → 2+2 → 2+1+1 → 1+1+1+1 as width steps down
 *   - rowHeight: max of declared member heights; "auto" when none declared;
 *     undeclared members ignored when mixed with declared ones
 */

import { describe, expect, it } from "vitest";
import { computeBandRows, rowHeight, DEFAULT_PANEL_MIN_WIDTH } from "./dashLayout";

const GAP = 8;
const p = (id: string, minWidth?: number, height?: number) => ({ id, minWidth, height });

describe("computeBandRows", () => {
  it("keeps panels in one row when minimums plus gap fit the width exactly", () => {
    // 560 + 8 + 340 = 908 — the boundary fits.
    const rows = computeBandRows([p("matrix", 560), p("treemap", 340)], 908, GAP);
    expect(rows.map((r) => r.ids)).toEqual([["matrix", "treemap"]]);
  });

  it("splits at the first panel that no longer fits, preserving declared order", () => {
    const rows = computeBandRows([p("matrix", 560), p("treemap", 340)], 907, GAP);
    expect(rows.map((r) => r.ids)).toEqual([["matrix"], ["treemap"]]);
  });

  it("never backfills: a small panel after a too-wide one opens a new row", () => {
    // a+b fit together; c overflows the container alone (its internal
    // overflow owns that); d would have fit beside a+b but must NOT jump
    // back — declared reading order is the identity guarantee — and cannot
    // join c's already-overflowing row (900 + 8 + 100 > 700).
    const rows = computeBandRows(
      [p("a", 300), p("b", 300), p("c", 900), p("d", 100)],
      700,
      GAP,
    );
    expect(rows.map((r) => r.ids)).toEqual([["a", "b"], ["c"], ["d"]]);
  });

  it("gives a panel wider than the container its own row instead of dropping it", () => {
    const rows = computeBandRows([p("matrix", 560)], 400, GAP);
    expect(rows.map((r) => r.ids)).toEqual([["matrix"]]);
  });

  it("accounts for the gap: N panels need sum(minWidths) + (N−1)·gap", () => {
    // Three 320s: 960 alone, 976 with two gaps. 970 fits only two.
    const panels = [p("a", 320), p("b", 320), p("c", 320)];
    expect(computeBandRows(panels, 976, GAP).map((r) => r.ids)).toEqual([["a", "b", "c"]]);
    expect(computeBandRows(panels, 970, GAP).map((r) => r.ids)).toEqual([["a", "b"], ["c"]]);
  });

  it("applies DEFAULT_PANEL_MIN_WIDTH when minWidth is omitted", () => {
    // Two defaults: 320 + 8 + 320 = 648.
    expect(DEFAULT_PANEL_MIN_WIDTH).toBe(320);
    expect(computeBandRows([p("a"), p("b")], 648, GAP).map((r) => r.ids)).toEqual([["a", "b"]]);
    expect(computeBandRows([p("a"), p("b")], 647, GAP).map((r) => r.ids)).toEqual([["a"], ["b"]]);
  });

  it("puts every panel in its own row at width 0", () => {
    const rows = computeBandRows([p("a", 320), p("b", 320), p("c", 560)], 0, GAP);
    expect(rows.map((r) => r.ids)).toEqual([["a"], ["b"], ["c"]]);
  });

  it("returns no rows for an empty panel list", () => {
    expect(computeBandRows([], 1440, GAP)).toEqual([]);
  });

  it("wraps a four-panel band 4 → 2+2 → 2+1+1 → solo as width steps down", () => {
    const panels = [p("a", 360), p("b", 360), p("c", 520), p("d", 360)];
    // 360+360+520+360 + 3·8 = 1624 — all four share a row.
    expect(computeBandRows(panels, 1624, GAP).map((r) => r.ids)).toEqual([
      ["a", "b", "c", "d"],
    ]);
    // a+b (728) fit; c+d (888) fit.
    expect(computeBandRows(panels, 900, GAP).map((r) => r.ids)).toEqual([
      ["a", "b"],
      ["c", "d"],
    ]);
    // a+b (728) fit; c (520) can't take d (888 > 800) — c solo, d solo.
    expect(computeBandRows(panels, 800, GAP).map((r) => r.ids)).toEqual([
      ["a", "b"],
      ["c"],
      ["d"],
    ]);
    // Below every pair: all solo.
    expect(computeBandRows(panels, 500, GAP).map((r) => r.ids)).toEqual([
      ["a"],
      ["b"],
      ["c"],
      ["d"],
    ]);
  });
});

describe("rowHeight", () => {
  it("returns the max of declared member heights", () => {
    expect(rowHeight([p("a", 360, 445), p("b", 520, 508)])).toBe(508);
    const rows = computeBandRows([p("a", 360, 445), p("b", 360, 508)], 2000, GAP);
    expect(rows[0].height).toBe(508);
  });

  it('returns "auto" when no member declares a height', () => {
    expect(rowHeight([p("a", 560), p("b", 340)])).toBe("auto");
  });

  it("ignores undeclared heights when mixed with declared ones", () => {
    expect(rowHeight([p("a", 560), p("b", 340, 400)])).toBe(400);
    // And the per-row split carries each row's own rule: declared-height
    // panel keeps its height when stacked solo; the other row goes auto.
    const rows = computeBandRows([p("a", 560), p("b", 340, 400)], 700, GAP);
    expect(rows.map((r) => r.height)).toEqual(["auto", 400]);
  });
});
