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
 *   - priority split: only the leading `after` rows + a muted expander show by default
 *   - expanding reveals the collapsed rest and the criteria pills
 *   - a collapsed row that is the current selection auto-reveals
 *   - no split ⇒ every row renders, no expander
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

const splitRows = [
  { id: "11-1111", label: "Alpha Role", sublabel: "SOC 11-1111 · 800 openings/yr · $70k", title: "Alpha Role" },
  { id: "22-2222", label: "Beta Role", sublabel: "SOC 22-2222 · 100 openings/yr · $70k", title: "Beta Role" },
  { id: "33-3333", label: "Gamma Role", sublabel: "SOC 33-3333 · 800 openings/yr · $40k", title: "Gamma Role" },
];
const splitProp = {
  after: 1,   // only Alpha is priority; Beta + Gamma collapse
  restLabel: "below the priority bar",
  criteria: ["> 239 openings", "≥ $54k median", "non-declining"],
};

function renderSplit(selectedRow: string | null = null, split: typeof splitProp | null = splitProp) {
  render(
    <CoverageMatrix
      cols={cols}
      rows={splitRows}
      split={split}
      level={() => "none"}
      selectedRow={selectedRow}
      selectedCol={null}
      cornerLabel="↓ role · → college"
      gapCellHint="no activity"
      legend={[{ k: "Gap", sub: "none", bg: "#fff", ring: false }]}
      onSelect={vi.fn()}
    />,
  );
}

describe("CoverageMatrix priority split", () => {
  it("shows only the priority rows and a muted expander by default", () => {
    renderSplit();
    expect(screen.getByText("Alpha Role")).toBeTruthy();     // priority (after = 1)
    expect(screen.queryByText("Beta Role")).toBeNull();       // collapsed
    expect(screen.queryByText("Gamma Role")).toBeNull();
    expect(screen.getByRole("button").textContent).toContain("2 more");
    // Criteria pills ride with the rest — not shown until expanded.
    expect(screen.queryByText("> 239 openings")).toBeNull();
  });

  it("reveals the rest and the criteria pills when the expander is clicked", async () => {
    renderSplit();
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByText("Beta Role")).toBeTruthy();
    expect(screen.getByText("Gamma Role")).toBeTruthy();
    expect(screen.getByText("below the priority bar")).toBeTruthy();
    expect(screen.getByText("> 239 openings")).toBeTruthy();
    expect(screen.getByText("≥ $54k median")).toBeTruthy();
    expect(screen.getByText("non-declining")).toBeTruthy();
  });

  it("auto-reveals a collapsed row when it is the current selection", () => {
    renderSplit("33-3333");   // Gamma is in the collapsed rest
    expect(screen.getByText("Gamma Role")).toBeTruthy();      // visible without a click
  });

  it("renders every row and no expander when no split is given", () => {
    renderSplit(null, null);
    expect(screen.getByText("Alpha Role")).toBeTruthy();
    expect(screen.getByText("Beta Role")).toBeTruthy();
    expect(screen.getByText("Gamma Role")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
