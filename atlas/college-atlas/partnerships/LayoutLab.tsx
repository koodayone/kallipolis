"use client";

/* ── Layout lab — the dashboard's proportion-discovery instrument ───────────
   The dashboard's bands render at declarative default weights (fr fractions
   keyed to panel identity) and heights (keyed to band identity). Inside this
   provider — mounted only by /svamp/concepts/layout — the bands' gaps become
   drag handles, and the live manifest is pinned in a readout for copy-paste
   back into the lens files as the new defaults.

   Deliberately NO persistence: plain state, refresh = reset. The destination
   of a good layout is the code (the declarative defaults), not storage.
   Sibling of the /svamp/concepts design records; delete together once the
   defaults settle. */

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";

export type BandManifest = {
  band: string;
  height: number | "auto";
  panels: { id: string; weight: number }[];
};

type LabState = {
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

export const LayoutLabContext = createContext<LabState | null>(null);

const round2 = (v: number) => Math.round(v * 100) / 100;

export function LayoutLabProvider({ children }: { children: React.ReactNode }) {
  const [weights, setWeightsState] = useState<Record<string, number>>({});
  const [heights, setHeightsState] = useState<Record<string, number>>({});
  const [arrangement, setArrangement] = useState<Record<string, string[]>>({});
  // Plain object — string keys keep insertion order, and spreading an existing
  // key updates in place, so the readout's band order is stable during drags.
  const [manifests, setManifests] = useState<Record<string, BandManifest>>({});
  // Ref mirror so swapPanels can read the current on-screen composition
  // without making the manifests part of the context value.
  const manifestsRef = useRef<Record<string, BandManifest>>({});

  const setWeights = useCallback((patch: Record<string, number>) => {
    setWeightsState((w) => ({ ...w, ...patch }));
  }, []);
  const setHeight = useCallback((band: string, h: number) => {
    setHeightsState((m) => ({ ...m, [band]: h }));
  }, []);
  const swapPanels = useCallback((a: string, b: string) => {
    if (a === b) return;
    // Locate both panels in the on-screen composition.
    let rowA: BandManifest | undefined, rowB: BandManifest | undefined;
    let wA = 1, wB = 1;
    for (const m of Object.values(manifestsRef.current)) {
      for (const p of m.panels) {
        if (p.id === a) { rowA = m; wA = p.weight; }
        if (p.id === b) { rowB = m; wB = p.weight; }
      }
    }
    if (!rowA || !rowB) return;
    const sub = (ids: string[]) => ids.map((id) => (id === a ? b : id === b ? a : id));
    setArrangement((arr) => {
      const next = { ...arr, [rowA!.band]: sub(rowA!.panels.map((p) => p.id)) };
      if (rowB!.band !== rowA!.band) next[rowB!.band] = sub(rowB!.panels.map((p) => p.id));
      return next;
    });
    // The slot keeps its size: the panels exchange effective weights.
    setWeightsState((w) => ({ ...w, [a]: wB, [b]: wA }));
  }, []);
  const register = useCallback((m: BandManifest) => {
    manifestsRef.current = { ...manifestsRef.current, [m.band]: m };
    setManifests((prev) => {
      // Bail to the same reference when nothing changed — registration runs in
      // a band effect whose deps include the context value, so an
      // unconditional new object would loop register → render → register.
      const cur = prev[m.band];
      if (cur && JSON.stringify(cur) === JSON.stringify(m)) return prev;
      return { ...prev, [m.band]: m };
    });
  }, []);
  const unregister = useCallback((band: string) => {
    const { [band]: _refGone, ...refRest } = manifestsRef.current;
    manifestsRef.current = refRest;
    setManifests((prev) => {
      const { [band]: _gone, ...rest } = prev;
      return rest;
    });
  }, []);
  const reset = () => { setWeightsState({}); setHeightsState({}); setArrangement({}); };
  const dirty = Object.keys(weights).length > 0 || Object.keys(heights).length > 0 || Object.keys(arrangement).length > 0;

  // Memoized so manifest registrations (readout-only state) don't churn the
  // context identity and re-render every band.
  const value = useMemo(
    () => ({ weights, heights, arrangement, setWeights, setHeight, swapPanels, register, unregister }),
    [weights, heights, arrangement, setWeights, setHeight, swapPanels, register, unregister],
  );

  return (
    <LayoutLabContext.Provider value={value}>
      {children}
      <LabReadout manifests={manifests} dirty={dirty} onReset={reset} />
    </LayoutLabContext.Provider>
  );
}

/* ── Readout — the lab's product ────────────────────────────────────────────
   The live manifest of every band on screen, as the literal to bake back into
   the lens defaults. Copy puts the JSON on the clipboard. */
function LabReadout({ manifests, dirty, onReset }: { manifests: Record<string, BandManifest>; dirty: boolean; onReset: () => void }) {
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 1200);
    return () => clearTimeout(t);
  }, [copied]);

  const bands = Object.values(manifests);
  const toJson = () =>
    JSON.stringify(
      Object.fromEntries(bands.map((b) => [b.band, {
        height: b.height,
        panels: Object.fromEntries(b.panels.map((p) => [p.id, round2(p.weight)])),
      }])),
      null, 2,
    );

  return (
    <div style={{ position: "fixed", right: 16, bottom: 16, zIndex: 300, width: 300, background: "#0b1530", border: "1px solid rgba(255,255,255,0.14)", borderRadius: 10, boxShadow: "0 8px 32px rgba(0,0,0,.5)", overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
        <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", color: "#c9a84c" }}>LAYOUT LAB</span>
        <span style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          {dirty && (
            <button onClick={onReset} style={{ appearance: "none", border: "1px solid rgba(255,255,255,0.14)", background: "transparent", color: "#9aa6bd", fontFamily: MONO, fontSize: 9.5, borderRadius: 6, padding: "3px 8px", cursor: "pointer" }}>
              reset
            </button>
          )}
          <button
            onClick={() => { navigator.clipboard.writeText(toJson()).then(() => setCopied(true)).catch(() => {}); }}
            style={{ appearance: "none", border: "1px solid rgba(255,255,255,0.14)", background: copied ? "rgba(80,200,120,0.18)" : "rgba(255,255,255,0.06)", color: copied ? "#50c878" : "#e8ecf4", fontFamily: MONO, fontSize: 9.5, borderRadius: 6, padding: "3px 8px", cursor: "pointer", transition: "background .12s, color .12s" }}
          >
            {copied ? "copied" : "copy"}
          </button>
        </span>
      </div>
      <div style={{ padding: "8px 12px 10px", maxHeight: 260, overflowY: "auto" }}>
        {bands.length === 0 && (
          <div style={{ fontFamily: FONT, fontSize: 11.5, color: "#5e6a83" }}>No bands mounted.</div>
        )}
        {bands.map((b) => (
          <div key={b.band} style={{ padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <div style={{ fontFamily: MONO, fontSize: 9.5, color: "#9aa6bd", marginBottom: 2 }}>
              {b.band}
              <span style={{ color: "#5e6a83" }}> · h {b.height === "auto" ? "auto" : `${b.height}px`}</span>
            </div>
            <div style={{ fontFamily: MONO, fontSize: 10, color: "#e8ecf4", display: "flex", flexWrap: "wrap", gap: "2px 10px" }}>
              {b.panels.map((p) => (
                // Display name: the segment after the last dot — full ids live in the copied JSON.
                <span key={p.id}>{p.id.split(".").pop()} <span style={{ color: "#c9a84c" }}>{round2(p.weight)}</span></span>
              ))}
            </div>
          </div>
        ))}
        <div style={{ fontFamily: FONT, fontSize: 10.5, color: "#5e6a83", paddingTop: 7, lineHeight: 1.5 }}>
          Drag the gap between panels to re-weight a band; drag a band&apos;s bottom edge to set its height;
          drag a panel&apos;s header onto another panel to swap their places (the slot keeps its size).
          Heights clamp at content — a visualization never renders clipped.
        </div>
      </div>
    </div>
  );
}

export function useLayoutLab() {
  return useContext(LayoutLabContext);
}
