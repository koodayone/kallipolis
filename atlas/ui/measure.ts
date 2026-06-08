"use client";

/* ── Container measurement hooks ────────────────────────────────────────────
   Cross-cutting infrastructure: components that respond to their MEASURED
   CONTAINER (not the viewport) use these. Originally chartKit's fill-mode
   machinery; hoisted to ui/ so header chrome can share them without a
   cross-feature dependency (chartKit re-exports for its existing consumers).

   The ref is a CALLBACK ref, not an object ref: a consumer may attach it to
   different DOM nodes across renders, and an observer bound once at mount
   would keep watching the detached node — freezing the measurement. The
   callback re-observes on every element change; the observer's initial fire
   on observe() delivers the fresh measurement. SSR/test-safe: measurements
   start null and stay null where ResizeObserver doesn't exist. */

import { useCallback, useRef, useState } from "react";

export function useMeasuredBox(enabled: boolean) {
  const [box, setBox] = useState<{ w: number; h: number } | null>(null);
  const roRef = useRef<ResizeObserver | null>(null);
  const ref = useCallback((el: HTMLDivElement | null) => {
    roRef.current?.disconnect();
    roRef.current = null;
    if (!enabled || !el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => setBox({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    roRef.current = ro;
  }, [enabled]);
  return { ref, box };
}

// Width-only sibling for consumers whose layout depends only on horizontal
// space. Updating state only when clientWidth CHANGES (functional set with an
// equality bail) means height-only observer fires cause no re-render, which
// also breaks the height half of any measure feedback loop.
export function useMeasuredWidth(enabled: boolean) {
  const [width, setWidth] = useState<number | null>(null);
  const roRef = useRef<ResizeObserver | null>(null);
  const ref = useCallback((el: HTMLDivElement | null) => {
    roRef.current?.disconnect();
    roRef.current = null;
    if (!enabled || !el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth;
      setWidth((prev) => (prev === w ? prev : w));
    });
    ro.observe(el);
    roRef.current = ro;
  }, [enabled]);
  return { ref, width };
}
