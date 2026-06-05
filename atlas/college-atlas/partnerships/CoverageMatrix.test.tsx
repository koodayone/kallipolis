/**
 * Tests for CoverageMatrix — the shared (unit × college) coverage grid used by
 * both SVAMP lenses (occupations: SOC × college; programs: TOP × college).
 *
 * Uses React Testing Library against happy-dom to assert the public contract:
 * the corner label, column headers, and unit rows render, and clicking any
 * cell — covered or gap — invokes onSelect with (rowId, colId). Coverage state
 * (from the caller's level()) must NOT gate selectability: gap cells stay
 * clickable so they can open the crosswalk-only view.
 *
 * Coverage:
 *   - corner label, column header labels, and row labels render
 *   - clicking a covered cell calls onSelect(rowId, colId)
 *   - clicking a gap cell (level "none") still calls onSelect (selectable)
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CoverageMatrix, { type CoverageLevel } from "./CoverageMatrix";

const cols = [
  { id: "de-anza", label: "De Anza", brand: "#86c2dd" },
  { id: "ohlone", label: "Ohlone", brand: "#c97b84" },
];
const rows = [
  { id: "094800", label: "Automotive Technology", sublabel: "TOP 094800", title: "Automotive Technology" },
  { id: "095600", label: "Manufacturing", sublabel: "TOP 095600", title: "Manufacturing" },
];
// De Anza × 094800 is strong; everything else is a gap.
const level = (rowId: string, colId: string): CoverageLevel =>
  rowId === "094800" && colId === "de-anza" ? "strong" : "none";

function renderMatrix(onSelect = vi.fn()) {
  render(
    <CoverageMatrix
      cols={cols}
      rows={rows}
      level={level}
      selectedRow={null}
      selectedCol={null}
      cornerLabel="↓ program (by awards) · → college"
      gapCellHint="doesn't teach this program"
      legend={[{ k: "Covered", sub: "teaches it · has awards", bg: "#fff", ring: true }]}
      onSelect={onSelect}
    />,
  );
  return onSelect;
}

describe("CoverageMatrix", () => {
  it("renders the corner label, column headers, and unit rows", () => {
    renderMatrix();
    expect(screen.getByText("↓ program (by awards) · → college")).toBeTruthy();
    expect(screen.getByText("De Anza")).toBeTruthy();
    expect(screen.getByText("Ohlone")).toBeTruthy();
    expect(screen.getByText("Automotive Technology")).toBeTruthy();
    expect(screen.getByText("TOP 094800")).toBeTruthy();
  });

  it("clicking a covered cell calls onSelect with (rowId, colId)", async () => {
    const onSelect = renderMatrix();
    await userEvent.click(screen.getByTitle("De Anza · Automotive Technology"));
    expect(onSelect).toHaveBeenCalledWith("094800", "de-anza");
  });

  it("clicking a gap cell still calls onSelect (gap cells are selectable)", async () => {
    const onSelect = renderMatrix();
    await userEvent.click(
      screen.getByTitle("Ohlone · Automotive Technology — doesn't teach this program"),
    );
    expect(onSelect).toHaveBeenCalledWith("094800", "ohlone");
  });
});
