"use client";

/* ── SVAMP Dashboard — the report transposed ────────────────────────────────
   Same visual vocabulary as the report (treemaps, coverage matrices, trend
   charts, the gold demand line), spatial simultaneity instead of narrative
   sequence. Report = argument (citeable, prose, scrolling); dashboard =
   instrument (at-a-glance, projectable). Prose dies here; its integrity
   obligations live in chrome — every DashPanel names its institutional
   authority.

   V1 requirements (decided 2026-06-06; design record at /svamp/concepts):
   1. One lens at a time via tabs. Programs and Occupations share the
      dashboard grammar (aggregates on top, single-scope band below);
      Employers is its own state — no selection crosses the lens boundary.
   2. Detail band = tiled single-scope grid. Treemap rect / matrix row ⇒
      consortium scope; matrix cell ⇒ that college's scope (decompositions
      live there).
   3. Viewport — REVISED in build: each visualization renders whole at its
      ideal width-driven proportion and the page scrolls; the nav and lens
      rail stay pinned. ≥1440px gate routes smaller screens to the report.
   4. Employers = standalone full-bleed map at State-Atlas parity.

   Header (decided at /svamp/concepts/header — H1): the report's AtlasHeader
   verbatim (cube · centered consortium title + PREVIEW MODE · surface-form
   navigation right), then the report's masthead (eyebrow, title, stats) which
   scrolls away, then the lens rail which pins under the nav — the report's
   sticky-banner behavior, transposed. The landing view is the cover; the
   working view is dense.

   URL anchoring reuses svampUrl verbatim (route-agnostic; same lens/top/
   soc/college vocabulary as the report), so dashboard views are shareable
   and the analytics record is the URL — and a view can hop between
   /svamp (dashboard, the root) and /svamp/report with its selection intact. */

import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { LayoutLabContext } from "@/college-atlas/partnerships/LayoutLab";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";
import { collegeAtlasIdByName, getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import AtlasHeader from "@/ui/AtlasHeader";
import SvampDashboardPrograms, { type CollegeRef } from "@/college-atlas/partnerships/SvampDashboardPrograms";
import SvampDashboardOccupations from "@/college-atlas/partnerships/SvampDashboardOccupations";
import SvampDashboardEmployers from "@/college-atlas/partnerships/SvampDashboardEmployers";
import LensTabs, { type Lens, LENS_ACCENTS } from "@/college-atlas/partnerships/LensTabs";
import IndustryRail from "@/college-atlas/partnerships/IndustryRail";
import SurfaceNav from "@/college-atlas/partnerships/SurfaceNav";
import { Dot, useMeasuredWidth } from "@/college-atlas/partnerships/chartKit";
import { computeBandRows, rowHeight, DEFAULT_PANEL_MIN_WIDTH } from "@/college-atlas/partnerships/dashLayout";
import { getSvampLandscape, getSvampPrograms } from "@/college-atlas/partnerships/api";
import { landscapeInstance, type LandscapeInstance } from "@/college-atlas/partnerships/landscapeInstances";

// The five member colleges, in display order (mirrors /svamp's ClientPage).
// College ids now come from the landscape instance registry (keyed by `instance`).

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";

type DashLens = Lens;

/* ── Panel expand — Grafana's full-viewport panel view, transposed ─────────
   Any band panel can expand to fill the viewport under the nav: the same
   panel node handed viewport dimensions (the fill machinery re-lays every
   chart), with the selection model still live behind it. Expanded state is
   shareable — `panel=<id>` rides the svampUrl vocabulary like every other
   view param. The context is provided by the dashboard shell; the affordance
   lives in DashPanel chrome and is injected per-panel by DashBand, so every
   present and future band panel inherits it. The employers map is exempt by
   construction (it doesn't render through bands). */
export const DashExpandContext = React.createContext<null | {
  expandedId: string | null;
  setExpanded: (id: string | null) => void;
}>(null);

/* ── Scope accent — the whole instrument wears the scope color ─────────────
   In college scope, every accent in the shell (active lens tab, rail stats)
   follows the college's brand instead of the lens hue — completing the rule
   that color answers exactly one question: whose scope am I looking at?
   Lenses report their scope brand upward through this context (null at
   consortium scope ⇒ the lens accent applies). Data semantics stay protected
   where they always have: panel titles and authority chips, not hue. */
export const ScopeAccentContext = React.createContext<null | {
  set: (accent: string | null) => void;
}>(null);

const GlyphExpand: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M19 5h8v8" /><path d="M27 5 18.5 13.5" /><path d="M13 27H5v-8" /><path d="M5 27l8.5-8.5" />
  </svg>
);
const GlyphCollapse: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M26 14h-8V6" /><path d="M18 14l9-9" /><path d="M6 18h8v8" /><path d="M14 18l-9 9" />
  </svg>
);

/* ── Panel chrome — the dashboard's signature element ─────────────────────
   Every panel header carries its authority chip (· DataMart, · COE, · EDD):
   the report's prose attributions, transposed into chrome. */
export function DashPanel({ title, authority, accent, children, grow = 1, expandId, style }: {
  title: string;
  authority: string;
  accent: string;
  children: React.ReactNode;
  grow?: number;
  // Injected by DashBand (the panel's manifest id) — presence wires the
  // hover-revealed expand affordance. Hidden inside the layout lab, whose
  // grip overlay owns the header strip.
  expandId?: string;
  // Caller layout overrides (merged last) — the employers lens uses this to
  // give its panels explicit heights in stacked mode, where flex grow no
  // longer distributes the viewport.
  style?: React.CSSProperties;
}) {
  const expand = useContext(DashExpandContext);
  const lab = useContext(LayoutLabContext);
  const expandable = !!(expand && expandId && !lab);
  const isExpanded = expandable && expand!.expandedId === expandId;
  return (
    <div style={{ flex: grow, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", border: `1px solid ${HAIR}`, borderRadius: 10, background: isExpanded ? "#0a1228" : "rgba(255,255,255,0.022)", overflow: "hidden", ...style }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)", flex: "none" }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: accent, flex: "none" }} />
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, letterSpacing: "0.04em", color: "rgba(255,255,255,0.88)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</span>
        <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 9.5, color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap", flex: "none" }}>· {authority}</span>
        {expandable && (
          // Always visible at chip quietness (hover affordances don't exist
          // when projecting or on touch); brightens under its own pointer.
          <button
            onClick={() => expand!.setExpanded(isExpanded ? null : expandId!)}
            title={isExpanded ? "Collapse (Esc)" : "Expand panel"}
            onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.95"; }}
            onMouseLeave={(e) => { e.currentTarget.style.opacity = isExpanded ? "0.9" : "0.4"; }}
            // translateY: optical correction — the authority chip has no
            // descenders, so its ink rides ~0.7px above its box center; the
            // geometrically-symmetric glyph must follow the ink, not the box.
            style={{ appearance: "none", border: 0, background: "transparent", cursor: "pointer", width: 15, height: 15, padding: 0, color: "#9aa6bd", opacity: isExpanded ? 0.9 : 0.4, transition: "opacity .15s", flex: "none", display: "flex", transform: "translateY(-0.75px)" }}
          >
            {isExpanded ? <GlyphCollapse /> : <GlyphExpand />}
          </button>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0, padding: 10, display: "flex", flexDirection: "column" }}>{children}</div>
    </div>
  );
}

/* ── Band — one row of panels, the dashboard's layout unit ─────────────────
   Renders its panels as an fr-grid driven by relative weights keyed to panel
   identity (author-qualified ids, e.g. "programs.supply"), so weights don't
   need to sum to anything and a conditionally-absent panel renormalizes the
   row by construction. Height is "auto" (content-driven — the standing
   viewport rule) or a px value rendered as minmax(min-content, px), so a
   band can never clip its content — a visualization always renders whole.

   In production the band is static. Inside the LayoutLab provider (mounted
   only by /svamp/concepts/layout), the inter-panel gaps become col-resize
   handles and the band's bottom edge a row-resize handle, and the band
   reports its effective manifest to the lab's readout. */
export type DashBandPanel = {
  id: string;
  weight?: number;     // fr share when co-rowed (default 1)
  minWidth?: number;   // intrinsic minimum px (default dashLayout's 320) — drives row packing
  height?: number;     // target row height px (minmax(min-content, X)); absent ⇒ content-driven
  node: React.ReactNode;
} | false | null | undefined;
type ConcretePanel = Exclude<DashBandPanel, false | null | undefined>;

const BAND_GAP = 8;       // production gap == lab handle width, so the two modes align
const PANEL_MIN_PX = 200; // a panel can't be dragged below readability

/* ── Band set — a lens's bands under one panel registry ────────────────────
   The set is what makes the lab's swap gesture lens-wide: every concrete
   panel in the lens registers here. RENDITION IS A FUNCTION OF MEASURED
   SPACE: in production the set measures its own width once (all bands are
   full-width siblings) and each band's panels pack into rows by their
   intrinsic minimums (dashLayout.computeBandRows) — declared order, never
   reordered, so the layout compresses without rearranging. Inside the
   LayoutLab the responsive computation is BYPASSED: the lab renders the
   declared one-row-per-band composition exactly, because its weight/height/
   swap gestures assume one row per band; its arrangement resolution stays
   defensive against stale state (unknown ids drop, displaced panels return
   to their declared band, duplicate placement keeps the first). `before`
   renders interstitial chrome before a band's first row, outside the swap
   system. */
export type DashBandDef = { id: string; before?: React.ReactNode; panels: DashBandPanel[] };

type RenderRow = { key: string; before?: React.ReactNode; height: number | "auto"; panels: ConcretePanel[] };

export function DashBandSet({ bands }: { bands: DashBandDef[] }) {
  const lab = useContext(LayoutLabContext);
  const expand = useContext(DashExpandContext);
  // One width observer for the whole set; lab mode skips measurement.
  const { ref: measureRef, width } = useMeasuredWidth(!lab);
  const reg = new Map<string, ConcretePanel>(
    bands.flatMap((b) => b.panels.filter(Boolean) as ConcretePanel[]).map((p) => [p.id, p]),
  );

  const renderRows: RenderRow[] = [];
  if (lab) {
    // Lab branch — declared one-row-per-band, arrangement-resolved.
    const placed = new Set<string>();
    const rows = bands.map((b) => {
      const declared = (b.panels.filter(Boolean) as ConcretePanel[]).map((p) => p.id);
      const ids = (lab.arrangement[b.id] ?? declared).filter((id) => reg.has(id) && !placed.has(id));
      ids.forEach((id) => placed.add(id));
      return { b, declared, ids };
    });
    // Leftovers — declared panels a stale arrangement displaced — return home.
    rows.forEach((r) => r.declared.forEach((id) => {
      if (!placed.has(id)) { r.ids.push(id); placed.add(id); }
    }));
    rows.filter((r) => r.ids.length > 0 || r.b.before).forEach((r) => renderRows.push({
      key: r.b.id,
      before: r.b.before,
      height: rowHeight(r.b.panels.filter(Boolean) as ConcretePanel[]),
      panels: r.ids.map((id) => reg.get(id)!),
    }));
  } else if (width != null) {
    // Production branch — rows computed from the measured width. Until the
    // first measurement lands the wrapper renders empty: the lenses gate on
    // data with SvampLoading, so this is ~one invisible frame, and the
    // static export prerenders only the loading state (no hydration skew).
    for (const b of bands) {
      const rows = computeBandRows(b.panels.filter(Boolean) as ConcretePanel[], width, BAND_GAP);
      if (!rows.length) {
        if (b.before) renderRows.push({ key: b.id, before: b.before, height: "auto", panels: [] });
        continue;
      }
      rows.forEach((row, i) => renderRows.push({
        key: `${b.id}:${i}`,
        before: i === 0 ? b.before : undefined,
        height: row.height,
        panels: row.ids.map((id) => reg.get(id)!),
      }));
    }
  }

  // Expanded panel — the same node at viewport size, portaled over the page
  // (under the nav, so identity stays visible). A stale or cross-lens id
  // simply misses the registry and nothing renders. Esc closes.
  const expandedPanel = expand?.expandedId ? reg.get(expand.expandedId) : undefined;
  useEffect(() => {
    if (!expandedPanel || !expand) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") expand.setExpanded(null); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [expandedPanel, expand]);

  return (
    <>
      {/* The measured wrapper owns the inter-row gap (identical to the old
          sibling spacing); the ref must render in both modes so production's
          first measurement can land. */}
      <div ref={measureRef} style={{ display: "flex", flexDirection: "column", gap: BAND_GAP }}>
        {renderRows.map((r) => (
          <React.Fragment key={r.key}>
            {r.before}
            {r.panels.length > 0 && <DashBand id={r.key} height={r.height} panels={r.panels} />}
          </React.Fragment>
        ))}
      </div>
      {expandedPanel && typeof document !== "undefined" && createPortal(
        <div
          onClick={() => expand!.setExpanded(null)}
          style={{ position: "fixed", left: 0, right: 0, top: `calc(${RAIL_BOTTOM_VAR} + 48px)`, bottom: 0, zIndex: 25, background: "rgba(4,9,22,0.82)", backdropFilter: "blur(4px)", padding: 16, display: "flex" }}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ flex: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column" }}>
            {React.isValidElement(expandedPanel.node)
              ? React.cloneElement(expandedPanel.node as React.ReactElement<{ expandId?: string }>, { expandId: expandedPanel.id })
              : expandedPanel.node}
          </div>
        </div>,
        document.body,
      )}
    </>
  );
}

export function DashBand({ id, height = "auto", panels }: {
  id: string;
  height?: number | "auto";
  panels: DashBandPanel[];
}) {
  const lab = useContext(LayoutLabContext);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const panelRefs = useRef<(HTMLDivElement | null)[]>([]);
  const present = panels.filter(Boolean) as ConcretePanel[];

  const effWeights = present.map((p) => lab?.weights[p.id] ?? p.weight ?? 1);
  const effHeight = lab?.heights[id] ?? height;

  // Report the effective manifest while mounted (update-in-place keeps the
  // readout's band order stable); unregister only on true unmount.
  const manifestStr = JSON.stringify({ band: id, height: effHeight, panels: present.map((p, i) => ({ id: p.id, weight: effWeights[i] })) });
  useEffect(() => {
    lab?.register(JSON.parse(manifestStr));
  }, [lab, manifestStr]);
  useEffect(() => {
    if (!lab) return;
    return () => lab.unregister(id);
    // register/unregister are stable; id never changes for a mounted band.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Width drag — the handle between panels i and i+1 redistributes their
  // weight pair (others untouched), preserving the pair's sum so the rest of
  // the row doesn't move.
  const onSplitDown = (e: React.PointerEvent<HTMLDivElement>, i: number) => {
    if (!lab) return;
    const L = panelRefs.current[i], R = panelRefs.current[i + 1];
    if (!L || !R) return;
    e.preventDefault();
    const pxL = L.getBoundingClientRect().width, pxR = R.getBoundingClientRect().width;
    const pair = effWeights[i] + effWeights[i + 1];
    const x0 = e.clientX;
    const handle = e.currentTarget;
    handle.setPointerCapture(e.pointerId);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    const move = (ev: PointerEvent) => {
      const span = pxL + pxR;
      const nL = Math.min(Math.max(pxL + (ev.clientX - x0), PANEL_MIN_PX), span - PANEL_MIN_PX);
      const share = nL / span;
      lab.setWeights({ [present[i].id]: pair * share, [present[i + 1].id]: pair * (1 - share) });
    };
    const up = () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      handle.removeEventListener("pointermove", move);
      handle.removeEventListener("pointerup", up);
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up);
  };

  // Height drag — the band's bottom edge. Stored height below the row's
  // min-content has no effect (minmax clamps), so a drag can squeeze a
  // height-flexible band but never clip a content-driven one.
  const onHeightDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!lab || !gridRef.current) return;
    e.preventDefault();
    const h0 = gridRef.current.getBoundingClientRect().height;
    const y0 = e.clientY;
    const handle = e.currentTarget;
    handle.setPointerCapture(e.pointerId);
    document.body.style.cursor = "row-resize";
    document.body.style.userSelect = "none";
    const move = (ev: PointerEvent) => {
      lab.setHeight(id, Math.round(Math.min(Math.max(h0 + (ev.clientY - y0), 80), 3000)));
    };
    const up = () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      handle.removeEventListener("pointermove", move);
      handle.removeEventListener("pointerup", up);
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up);
  };

  // Swap drag — grab a panel by its header strip and drop it on another
  // panel (any band in the lens) to switch their places. Target detection is
  // elementFromPoint → closest wrapper; highlight is direct DOM styling so
  // the drag doesn't churn React state until the drop commits. Near the
  // viewport's edges the dashboard auto-scrolls (pointer capture blocks
  // native scrolling), so a panel can swap with one below the fold.
  const onGripDown = (e: React.PointerEvent<HTMLDivElement>, srcId: string) => {
    if (!lab) return;
    e.preventDefault();
    const handle = e.currentTarget;
    handle.setPointerCapture(e.pointerId);
    document.body.style.cursor = "grabbing";
    document.body.style.userSelect = "none";
    const srcWrap = handle.parentElement as HTMLElement;
    srcWrap.style.opacity = "0.45";
    const scroller = handle.closest("[data-dash-scroll]") as HTMLElement | null;
    let target: HTMLElement | null = null;
    let lastX = e.clientX, lastY = e.clientY;
    let scrollDir = 0, rafId = 0;
    const clearTarget = () => {
      if (target) { target.style.outline = ""; target.style.outlineOffset = ""; }
      target = null;
    };
    const detect = () => {
      const el = document.elementFromPoint(lastX, lastY);
      const wrap = (el?.closest?.("[data-dash-panel]") ?? null) as HTMLElement | null;
      const overId = wrap?.getAttribute("data-dash-panel");
      if (wrap && overId && overId !== srcId) {
        if (wrap !== target) {
          clearTarget();
          target = wrap;
          wrap.style.outline = "2px solid rgba(201,168,76,0.85)";
          wrap.style.outlineOffset = "-2px";
        }
      } else {
        clearTarget();
      }
    };
    const scrollLoop = () => {
      if (scrollDir && scroller) {
        scroller.scrollTop += scrollDir;
        detect(); // the page moves under a stationary cursor
        rafId = requestAnimationFrame(scrollLoop);
      } else {
        rafId = 0;
      }
    };
    const move = (ev: PointerEvent) => {
      lastX = ev.clientX; lastY = ev.clientY;
      // Edge zones: below the sticky nav+rail up top, near the bottom edge.
      scrollDir = ev.clientY > window.innerHeight - 70 ? 14 : ev.clientY < 170 ? -14 : 0;
      if (scrollDir && !rafId) rafId = requestAnimationFrame(scrollLoop);
      detect();
    };
    const up = () => {
      const dstId = target?.getAttribute("data-dash-panel");
      clearTarget();
      scrollDir = 0;
      if (rafId) cancelAnimationFrame(rafId);
      srcWrap.style.opacity = "";
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      handle.removeEventListener("pointermove", move);
      handle.removeEventListener("pointerup", up);
      if (dstId) lab.swapPanels(srcId, dstId);
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up);
  };

  // Lab mode interleaves explicit handle tracks where production has gap.
  // Production columns: minmax(min, fr) per panel — computeBandRows already
  // guaranteed the minimums fit, so grid just absorbs the continuum between
  // comfortable and the wrap point. A SOLO panel uses minmax(0,1fr)
  // deliberately: a min there would push the band wider than the scroller
  // (page-level horizontal scrollbar); below its minimum the panel's own
  // fallback governs — the matrix and pathways pan, the charts clamp.
  const cols = lab
    ? effWeights.map((w) => `${w}fr`).join(` ${BAND_GAP}px `)
    : present.length === 1
      ? "minmax(0, 1fr)"
      : present.map((p, i) => `minmax(${p.minWidth ?? DEFAULT_PANEL_MIN_WIDTH}px, ${effWeights[i]}fr)`).join(" ");

  return (
    <div>
      <div
        ref={gridRef}
        style={{
          display: "grid",
          gridTemplateColumns: cols,
          gridTemplateRows: effHeight === "auto" ? undefined : `minmax(min-content, ${effHeight}px)`,
          gap: lab ? 0 : BAND_GAP,
          alignItems: "stretch",
        }}
      >
        {present.map((p, i) => (
          <React.Fragment key={p.id}>
            {i > 0 && lab && (
              <div
                onPointerDown={(e) => onSplitDown(e, i - 1)}
                style={{ cursor: "col-resize", display: "flex", alignItems: "stretch", justifyContent: "center", touchAction: "none" }}
                onMouseEnter={(e) => { (e.currentTarget.firstChild as HTMLElement).style.background = "rgba(201,168,76,0.55)"; }}
                onMouseLeave={(e) => { (e.currentTarget.firstChild as HTMLElement).style.background = "transparent"; }}
              >
                <span style={{ width: 2, borderRadius: 1, background: "transparent", transition: "background .12s" }} />
              </div>
            )}
            <div ref={(el) => { panelRefs.current[i] = el; }} data-dash-panel={p.id} style={{ minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", position: "relative" }}>
              {lab && (
                <div
                  onPointerDown={(e) => onGripDown(e, p.id)}
                  style={{ position: "absolute", top: 0, left: 0, right: 0, height: 28, cursor: "grab", zIndex: 5, touchAction: "none", borderRadius: "10px 10px 0 0", transition: "background .12s" }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(201,168,76,0.10)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                />
              )}
              {/* Inject the manifest id into the panel chrome so DashPanel can
                  wire its expand affordance — every band panel inherits it. */}
              {React.isValidElement(p.node)
                ? React.cloneElement(p.node as React.ReactElement<{ expandId?: string }>, { expandId: p.id })
                : p.node}
            </div>
          </React.Fragment>
        ))}
      </div>
      {lab && (
        <div
          onPointerDown={onHeightDown}
          style={{ height: 6, cursor: "row-resize", display: "flex", alignItems: "center", touchAction: "none" }}
          onMouseEnter={(e) => { (e.currentTarget.firstChild as HTMLElement).style.background = "rgba(201,168,76,0.55)"; }}
          onMouseLeave={(e) => { (e.currentTarget.firstChild as HTMLElement).style.background = "transparent"; }}
        >
          <span style={{ height: 2, width: "100%", borderRadius: 1, background: "transparent", transition: "background .12s" }} />
        </div>
      )}
    </div>
  );
}

/* ── Scope banner — the dashboard's "you are here" ─────────────────────────
   The REPORT's context banner, verbatim (decided B1 at /svamp/concepts/
   banner): scope smallcaps in the scope's brand color · dot · entity · code,
   46px, translucent over the scrolling panels. Display-only — the banner
   asserts, never acts; scope changes belong to the coverage matrix and the
   treemap. Completes the sticky stack — nav (surface) → lens rail (axis) →
   scope banner (entity): it sits in flow between the aggregate band and the
   scope bands, and pins under the lens rail once scrolled past, so the scope
   is never off-screen while its panels are. */
// The sticky stack's geometry is DERIVED, not hand-measured: the shell
// observes the lens rail's height (it wraps at narrow widths) and publishes
// nav + rail as --dash-rail-bottom on documentElement — documentElement, not
// the shell div, because the expand overlay portals into document.body and
// would not inherit a shell-scoped var. The banner pins at the var; the
// expand overlay starts 48px (the banner's height) below it, so the full
// stack — nav · rail · scope banner — stays visible over an expanded panel.
const NAV_H = 72; // AtlasHeader's fixed height
const RAIL_BOTTOM_VAR = "var(--dash-rail-bottom, 127px)"; // fallback = nav 72 + one-line rail 55
export function ScopeBanner({ brand, scope, name, code }: {
  brand: string;
  scope: string;        // "Consortium" or the college's short name
  name: string;         // selected program / occupation title
  code: string;         // "TOP 095600" / "49-9041"
}) {
  // The report's banner grammar scaled to this surface: the dashboard spans
  // full-bleed where the report sits in a 900px measure, so the type steps up
  // a notch and the content insets from the edges. No hairline — the blur
  // edge separates the pinned banner from panels sliding beneath it.
  return (
    <div style={{ position: "sticky", top: RAIL_BOTTOM_VAR, zIndex: 14, height: 48, background: "rgba(6,13,31,0.92)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", padding: "0 14px" }}>
      {/* Left-clustered: scope · name · code. The code is the selection — it
          rides with the name rather than hiding at the far edge, at visual
          parity with the scope label (same scale, full brand color). */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 11, minWidth: 0 }}>
        <span style={{ fontFamily: FONT, fontSize: 12.5, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase", color: brand, flex: "none", whiteSpace: "nowrap" }}>
          {scope}
        </span>
        <span style={{ color: "rgba(255,255,255,0.2)", flex: "none" }}>·</span>
        <span style={{ fontFamily: FONT, fontSize: 14.5, color: "rgba(255,255,255,0.9)", flex: "0 1 auto", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {name}
        </span>
        <span style={{ color: "rgba(255,255,255,0.2)", flex: "none" }}>·</span>
        <span style={{ fontFamily: MONO, fontSize: 12.5, fontWeight: 600, letterSpacing: "0.08em", color: brand, flex: "none", whiteSpace: "nowrap" }}>
          {code}
        </span>
      </div>
    </div>
  );
}

/* ── Loading — the Kallipolis rising sun, centered ─────────────────────────
   ONE loading language for every major state transition in the SVAMP
   experience (the report's idiom, transposed): the sun at low opacity,
   centered in the viewport space below the sticky stack. Lenses show it on
   their first data fetch only — the SVAMP getters are session-cached
   (api.svampCached), so every later lens switch renders instantly and this
   loader never replays. */
export function SvampLoading() {
  return (
    <div style={{ minHeight: "calc(100vh - 280px)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <RisingSun style={{ width: 90, height: "auto", opacity: 0.4 }} />
    </div>
  );
}

/* ── Viewport-width hook ────────────────────────────────────────────────────
   matchMedia is exact here because the dashboard scroller is fixed inset-0:
   viewport width ≡ container width. Used only for the employers lens's
   side-by-side vs stacked fit (a content-derived threshold, not a device
   breakpoint); the band lenses are container-measured instead. There is no
   gate — every width renders the dashboard, compressed by dashLayout. */
function useMinViewportWidth(px: number): boolean | null {
  const [fits, setFits] = useState<boolean | null>(null);
  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${px}px)`);
    const update = () => setFits(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, [px]);
  return fits;
}

/* ── Shell ────────────────────────────────────────────────────────────────── */
// A headline total above a treemap — the whole that the rects break down (the
// summed supply / demand of the shown items). A light block with a white number,
// so the summary reads first and the breakdown second.
export function TotalStrip({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "7px 11px", marginBottom: 8, borderRadius: 8, background: "rgba(255,255,255,0.055)", border: "1px solid rgba(255,255,255,0.09)", flex: "none" }}>
      <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: accent, flex: "none" }} />
        <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.6)" }}>{label}</span>
      </span>
      <span style={{ fontFamily: MONO, fontSize: 21, fontWeight: 600, color: "#fff", lineHeight: 1 }}>
        {value.toLocaleString("en-US")}
        <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.45)", marginLeft: 3 }}>/yr</span>
      </span>
    </div>
  );
}

export default function SvampDashboard({ instance = "svamp", identity }: { instance?: string; identity?: LandscapeInstance }) {
  // Pinned instances resolve identity from the registry; a generated instance
  // (no registry row) passes it in, built from the backend landscape index.
  const inst = identity ?? landscapeInstance(instance);
  const [lens, setLens] = useState<DashLens>("programs");
  // Employers side-by-side (map + rail) needs ~760px (350 map + 280 rail +
  // gaps/chrome); below it the lens stacks. The band lenses need no gate of
  // any kind — dashLayout compresses them continuously.
  const employersSideBySide = useMinViewportWidth(760);
  // Rail stats need ~510px beside the ~390px tabs; below the fit they hide
  // (masthead echo — ambient context sheds before anything else).
  const statsFit = useMinViewportWidth(960);

  // Publish the sticky stack's derived geometry (see RAIL_BOTTOM_VAR). The
  // observer writes the var directly — rail wrap/unwrap updates both the
  // banner and the expand overlay with zero React re-renders.
  const railRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = railRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      document.documentElement.style.setProperty("--dash-rail-bottom", `${NAV_H + el.offsetHeight}px`);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      document.documentElement.style.removeProperty("--dash-rail-bottom");
    };
  }, []);
  // The matrix column set. Normally the static instance colleges; but a
  // single-college lens is cluster-expanded server-side (the API returns the
  // co-member colleges), so when the payload carries MORE colleges than the
  // static config knows, rebuild the set from the API's college names. Pinned
  // multi-college instances (SVAMP/BACCC/SMCCD) have API == config and keep the
  // static set byte-for-byte.
  const [apiCollegeNames, setApiCollegeNames] = useState<string[] | null>(null);
  const colleges = useMemo(() => {
    const staticRefs = inst.collegeIds
      .map((id) => ({ id, config: getCollegeAtlasConfig(id) }))
      .filter((c): c is CollegeRef => c.config !== null);
    if (apiCollegeNames && apiCollegeNames.length > staticRefs.length) {
      const refs = apiCollegeNames
        .map((name) => {
          const id = collegeAtlasIdByName(name);
          const config = id ? getCollegeAtlasConfig(id) : null;
          return id && config ? { id, config } : null;
        })
        .filter((c): c is CollegeRef => c !== null);
      if (refs.length > staticRefs.length) {
        // Anchor the primary school (whose lens this is) as the left-most column;
        // the rest of the pool follows. staticRefs[0] is the instance's own college.
        const primaryId = staticRefs[0]?.id;
        return primaryId
          ? [...refs.filter((r) => r.id === primaryId), ...refs.filter((r) => r.id !== primaryId)]
          : refs;
      }
    }
    return staticRefs;
  }, [inst, apiCollegeNames]);

  // The school central to a single-college lens — scopes the Programs lens to its
  // OWN programs (the coordinator's portfolio); the cross-school pool view lives in
  // the Occupations lens. Null for multi-college consortium instances (show all).
  const primaryCollege = inst.collegeIds.length === 1
    ? getCollegeAtlasConfig(inst.collegeIds[0])?.name ?? null
    : null;
  // Single-college lenses expand to their cluster pool only once the API resolves
  // (apiCollegeNames). Hold the lens area until then so it paints once with the
  // final college set — no flash from the static 1-college fallback. Multi-college
  // instances are ready immediately (static set is already correct).
  const collegesReady = inst.collegeIds.length > 1 || apiCollegeNames !== null;

  // Masthead stats — the same institutional counts the report's masthead
  // shows, from the same payloads ("—" until they resolve, the report's idiom).
  const [agg, setAgg] = useState<{ colleges: number; occupations: number; region: string } | null>(null);
  const [activePrograms, setActivePrograms] = useState<number | null>(null);
  // Consortium (awards-gated) views drop colleges with no awarded supply in the
  // sector; the masthead then reads "N of M" so the consortium total stays
  // visible (no silent truncation). Curated SVAMP keeps all members.
  const [participating, setParticipating] = useState<{ n: number; awardsOnly: boolean } | null>(null);
  useEffect(() => {
    getSvampLandscape(instance)
      .then((x) => {
        setAgg({ colleges: x.aggregate.n_colleges, occupations: x.aggregate.n_occupations, region: x.region_display });
        setApiCollegeNames(x.colleges.map((c) => c.name));
      })
      .catch(() => {});
    getSvampPrograms(instance)
      .then((x) => {
        setActivePrograms(x.tops.filter((t) => t.enrollment_total > 0 || t.awards_total > 0).length);
        const withAwards = new Set((x.matrix?.cells ?? []).filter((c) => c.awards > 0).map((c) => c.college));
        setParticipating({ n: withAwards.size, awardsOnly: x.coverage_awards_only });
      })
      .catch(() => {});
  }, [instance]);

  // Expanded panel (Grafana-style) — shareable via the `panel` URL param.
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const expandCtx = useMemo(() => ({
    expandedId,
    setExpanded: (id: string | null) => { setExpandedId(id); writeSvampParams({ panel: id }); },
  }), [expandedId]);

  // Adopt the URL's lens + expanded panel after mount (post-hydration,
  // mirroring the report's static-export-safe pattern — no reactive
  // useSearchParams).
  useEffect(() => {
    const p = readSvampParams();
    if (p.lens === "occupations" || p.lens === "employers") setLens(p.lens);
    if (p.panel) setExpandedId(p.panel);
  }, []);

  const switchLens = (l: DashLens) => {
    setLens(l);
    // Absent lens param ⇒ programs default (the report's convention); clear
    // every cross-lens selection key on any switch (panel ids are
    // lens-qualified, so the expanded panel clears with the rest).
    setExpandedId(null);
    setScopeAccent(null);
    writeSvampParams({ lens: l === "programs" ? null : l, soc: null, top: null, college: null, emp: null, panel: null });
  };

  // Scope accent reported by the mounted lens (college scope only); the
  // shell's accents fall back to the lens hue at consortium scope.
  const [scopeAccent, setScopeAccent] = useState<string | null>(null);
  const scopeAccentCtx = useMemo(() => ({ set: setScopeAccent }), []);
  const lensAccent = scopeAccent ?? LENS_ACCENTS[lens];

  // Employers is full-viewport (State-Atlas parity) when the map + rail fit
  // side by side: the shell stops scrolling and becomes a fixed flex column
  // so the map fills the screen and only the search rail scrolls. Stacked
  // employers (narrow) and the band lenses keep the page scroll.
  // (null = first frame, before matchMedia lands ⇒ side-by-side default.)
  const employersFull = lens === "employers" && employersSideBySide !== false;

  return (
    <div data-dash-scroll style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, overscrollBehavior: "none", scrollbarGutter: "stable", ...(employersFull ? { display: "flex", flexDirection: "column", overflow: "hidden" } : { overflowY: "auto" }) }}>
      {/* Nav (revised from H1): Kallipolis brand left (no cube — the
          dashboard's identity is the product's), consortium title + PREVIEW
          MODE center, the surface forms (dashboard · report) right in
          glowing white. No masthead below — the nav already carries the
          title, so the old eyebrow/title were pure duplication. */}
      <AtlasHeader title={inst.name} shortTitle={inst.shortTitle} leftSlot={<KallipolisBrand />} rightSlot={<SurfaceNav active="dashboard" instance={instance} />} position="sticky" showPreview titleSize="15px" />

      {/* Lens rail — first row under the nav: tabs left, the consortium's
          stats right on the same rail (the masthead's surviving content),
          pinned together on scroll. */}
      <div ref={railRef} style={{ position: "sticky", top: NAV_H, zIndex: 15, background: BG, padding: "14px 16px 0" }}>
        {/* Industry rail — the SWP-sector channel selector, above the lens
            tabs. Renders only for member-set landscapes (SMCCD); SVAMP gets
            none. Wears the active lens accent. Its height feeds the sticky
            stack automatically (railRef's ResizeObserver → --dash-rail-bottom). */}
        <IndustryRail instance={instance} activeAccent={lensAccent} />
        {/* No flex gap between the tabs and the stats: their two borderBottom
            segments sit on one axis, and a gap would break the rail's line —
            the spacing lives inside the stats block instead. Shedding policy
            at narrow widths: the stats HIDE outright (below they'd have to
            share the line) — they are a masthead echo of static consortium
            facts, ambient context rather than view state, so they shed before
            any content chrome. Tabs then own the full rail line; LensTabs
            itself compresses further below 430/360. Viewport-keyed because
            the shell is fixed inset-0 (viewport ≡ rail width). */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: 0 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <LensTabs lens={lens} setLens={switchLens} activeAccent={scopeAccent ?? undefined} />
          </div>
          {statsFit !== false && (
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, paddingLeft: 24, paddingBottom: 14, borderBottom: `1px solid rgba(255,255,255,.08)`, marginBottom: 4, fontFamily: FONT, fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
            <span style={{ color: lensAccent, opacity: 0.8 }}>{
              !agg ? "— Member Colleges"
                : participating?.awardsOnly && participating.n < agg.colleges
                  ? `${participating.n} of ${agg.colleges} Colleges`
                  : `${agg.colleges} Member Colleges`
            }</span>
            <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{activePrograms ?? "—"} Programs</span>
            <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{agg ? agg.occupations : "—"} Occupations</span>
            <Dot /><span style={{ color: lensAccent, opacity: 0.8 }}>{agg ? agg.region : "—"}</span>
          </div>
          )}
        </div>
      </div>

      {/* Lens body — Programs and Occupations share the dashboard grammar;
          Employers is its own state. */}
      {/* No top padding on the banded lenses: the scope banner is their first
          child, and zero inset makes its natural position coincide with its
          sticky offset — pinned from the first pixel, no slide. */}
      <div style={{ display: "flex", flexDirection: "column", ...(employersFull ? { flex: 1, minHeight: 0, overflow: "hidden", padding: "12px 16px 16px" } : { padding: "0 16px 24px" }) }}>
        <ScopeAccentContext.Provider value={scopeAccentCtx}>
        <DashExpandContext.Provider value={expandCtx}>
          {!collegesReady ? <SvampLoading />
            : lens === "programs" ? <SvampDashboardPrograms colleges={colleges} instance={instance} primaryCollege={primaryCollege} />
            : lens === "occupations" ? <SvampDashboardOccupations colleges={colleges} instance={instance} primaryCollege={primaryCollege} />
            : <SvampDashboardEmployers colleges={colleges} stacked={employersSideBySide === false} instance={instance} />}
        </DashExpandContext.Provider>
        </ScopeAccentContext.Provider>
      </div>
    </div>
  );
}
