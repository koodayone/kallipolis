/**
 * Tests for AtlasHeader — the shared slot-based header used by the
 * College Atlas home, the State Atlas, and every focused form view.
 *
 * AtlasHeader is high-leverage: every atlas route mounts it, and a
 * regression here (missing back button, wrong aria-label, broken click
 * handler) ships a visible bug to every page at once. These tests use
 * React Testing Library against happy-dom to assert the public
 * contract: what renders, what's reachable by role/label, and what
 * happens when the user clicks.
 *
 * Coverage:
 *   - Title renders as text in the header
 *   - When onBack is provided and leftSlot is not, a back button
 *     renders with the default "Back to College Atlas" aria-label
 *   - When a school is provided, the back button's aria-label reads
 *     "Back to {school.name}"
 *   - Clicking the default back button invokes the onBack callback
 *   - When neither onBack nor leftSlot is provided, no back button
 *     is rendered
 *   - A custom leftSlot overrides the default back button even when
 *     onBack is also provided
 *   - A rightSlot renders in the trailing slot
 *   - The "Preview Mode" eyebrow is hidden when PREVIEW_MODE is false
 *   - The "Preview Mode" eyebrow renders when PREVIEW_MODE is true
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock @/preview/mode with a getter over hoisted mutable state so each
// test can toggle PREVIEW_MODE before rendering. The getter preserves
// ES-module live-binding semantics: AtlasHeader reads the current value
// at render time, not at import time.
const previewState = vi.hoisted(() => ({ enabled: false }));
vi.mock("@/preview/mode", () => ({
  get PREVIEW_MODE() {
    return previewState.enabled;
  },
}));

import AtlasHeader from "./AtlasHeader";
import type { SchoolConfig } from "@/config/schoolConfig";

describe("AtlasHeader", () => {
  beforeEach(() => {
    previewState.enabled = false;
  });

  it("renders the title text", () => {
    render(<AtlasHeader title="COLLEGE ATLAS" />);
    expect(screen.getByText("COLLEGE ATLAS")).toBeInTheDocument();
  });

  it("renders a default back button with the generic aria-label when onBack is provided without a school", () => {
    render(<AtlasHeader title="STUDENTS" onBack={() => {}} />);
    expect(
      screen.getByRole("button", { name: "Back to College Atlas" }),
    ).toBeInTheDocument();
  });

  it("uses the school name in the back button aria-label when a school is provided", () => {
    const school = { name: "Foothill College", brandColorNeon: "#abcdef" } as SchoolConfig;
    render(<AtlasHeader title="STUDENTS" onBack={() => {}} school={school} />);
    expect(
      screen.getByRole("button", { name: "Back to Foothill College" }),
    ).toBeInTheDocument();
  });

  it("invokes onBack when the default back button is clicked", async () => {
    const onBack = vi.fn();
    render(<AtlasHeader title="STUDENTS" onBack={onBack} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Back to College Atlas" }),
    );

    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders no back button when neither onBack nor leftSlot is provided", () => {
    render(<AtlasHeader title="COLLEGE ATLAS" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("prefers a custom leftSlot over the default back button", () => {
    render(
      <AtlasHeader
        title="STUDENTS"
        onBack={() => {}}
        leftSlot={<button type="button">Custom Left</button>}
      />,
    );
    expect(screen.getByRole("button", { name: "Custom Left" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Back to College Atlas" }),
    ).not.toBeInTheDocument();
  });

  it("renders the rightSlot content", () => {
    render(
      <AtlasHeader
        title="COLLEGE ATLAS"
        rightSlot={<span data-testid="right">Profile Menu</span>}
      />,
    );
    expect(screen.getByTestId("right")).toHaveTextContent("Profile Menu");
  });

  it("does not render the Preview Mode eyebrow when PREVIEW_MODE is false", () => {
    previewState.enabled = false;
    render(<AtlasHeader title="STATE ATLAS" />);
    expect(screen.queryByText("Preview Mode")).not.toBeInTheDocument();
  });

  it("renders the Preview Mode eyebrow when PREVIEW_MODE is true", () => {
    previewState.enabled = true;
    render(<AtlasHeader title="STATE ATLAS" />);
    expect(screen.getByText("Preview Mode")).toBeInTheDocument();
  });
});
