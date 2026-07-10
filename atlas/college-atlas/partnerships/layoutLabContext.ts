/* ── Layout-lab context — the dashboard's authoring seam ────────────────────
   The proportion-discovery instrument (the LayoutLab provider + its readout,
   mounted only by the now-removed /svamp/concepts/layout design record) was
   deleted once the dashboard's layout defaults settled. This context is the
   seam it plugged into: LandscapeDashboard reads it (useContext) and, when a
   provider supplies a non-null value, switches its band set from the
   responsive (measured-width) composition to the lab's declared drag-to-tune
   composition. With no provider mounted, the value is always null and the
   dashboard renders its production layout — so these types + context are inert
   in production but kept as the re-mount point should the lab ever return.

   Extracted from LayoutLab.tsx (deleted) so the dashboard keeps this contract
   without depending on the design-lab UI. */

export type BandManifest = {
  band: string;
  height: number | "auto";
  panels: { id: string; weight: number }[];
};

export type LabState = {
  // Overrides — weights keyed by panel id (panel ids are author-qualified,
  // e.g. "programs.supply", so a panel keeps its weight even when conditional
  // composition moves it between bands); heights keyed by band id;
  // arrangement keyed by band id (the ordered panel ids that band should
  // render, when the user has swapped panels around).
  weights: Record<string, number>;
  heights: Record<string, number>;
  arrangement: Record<string, string[]>;
  setWeights: (patch: Record<string, number>) => void;
  setHeight: (band: string, h: number) => void;
  // Swap two panels' positions (same band or across bands). The slot keeps
  // its size: the panels also exchange their effective weights, so the
  // layout's shape holds while the windows trade places.
  swapPanels: (a: string, b: string) => void;
  // Bands report their effective manifest so the readout shows exactly what
  // is on screen (registration follows mount/unmount across lens switches).
  register: (m: BandManifest) => void;
  unregister: (band: string) => void;
};

import { createContext } from "react";

export const LayoutLabContext = createContext<LabState | null>(null);
