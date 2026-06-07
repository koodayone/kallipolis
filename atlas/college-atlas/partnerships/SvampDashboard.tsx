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
   /svamp and /svamp/dashboard with its selection intact. */

import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { LayoutLabContext } from "@/college-atlas/partnerships/LayoutLab";
import KallipolisBrand from "@/ui/KallipolisBrand";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import AtlasHeader from "@/ui/AtlasHeader";
import SvampDashboardPrograms, { type CollegeRef } from "@/college-atlas/partnerships/SvampDashboardPrograms";
import SvampDashboardOccupations from "@/college-atlas/partnerships/SvampDashboardOccupations";
import SvampDashboardEmployers from "@/college-atlas/partnerships/SvampDashboardEmployers";
import LensTabs, { type Lens, LENS_ACCENTS } from "@/college-atlas/partnerships/LensTabs";
import SurfaceNav from "@/college-atlas/partnerships/SurfaceNav";
import { Dot, hexA } from "@/college-atlas/partnerships/chartKit";
import { getSvampLandscape, getSvampPrograms } from "@/college-atlas/partnerships/api";

// The five member colleges, in display order (mirrors /svamp's ClientPage).
const SVAMP_COLLEGE_IDS = ["deanza", "evergreen", "foothill", "mission", "ohlone"];

const BG = "#060d1f";
const HAIR = "rgba(255,255,255,0.09)";

type DashLens = Lens;

/* ── Panel chrome — the dashboard's signature element ─────────────────────
   Every panel header carries its authority chip (· DataMart, · COE, · EDD):
   the report's prose attributions, transposed into chrome. */
export function DashPanel({ title, authority, accent, children, grow = 1 }: {
  title: string;
  authority: string;
  accent: string;
  children: React.ReactNode;
  grow?: number;
}) {
  return (
    <div style={{ flex: grow, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", border: `1px solid ${HAIR}`, borderRadius: 10, background: "rgba(255,255,255,0.022)", overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)", flex: "none" }}>
        <span style={{ width: 3, height: 12, borderRadius: 2, background: accent, flex: "none" }} />
        <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, letterSpacing: "0.04em", color: "rgba(255,255,255,0.88)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</span>
        <span style={{ marginLeft: "auto", fontFamily: MONO, fontSize: 9.5, color: "rgba(255,255,255,0.4)", whiteSpace: "nowrap", flex: "none" }}>· {authority}</span>
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
export type DashBandPanel = { id: string; weight?: number; node: React.ReactNode } | false | null | undefined;
type ConcretePanel = Exclude<DashBandPanel, false | null | undefined>;

const BAND_GAP = 8;       // production gap == lab handle width, so the two modes align
const PANEL_MIN_PX = 200; // a panel can't be dragged below readability

/* ── Band set — a lens's bands under one panel registry ────────────────────
   The set is what makes the lab's swap gesture lens-wide: every concrete
   panel in the lens registers here, and each band renders the panel ids the
   lab's arrangement assigns it (declared order when untouched), so a swap
   can move a panel into any band. Resolution is defensive against stale
   arrangements (a lab session outliving conditional panels): unknown ids
   drop, displaced panels return to their declared band, duplicate placement
   keeps the first. `before` renders interstitial chrome (the scope strip)
   between bands, outside the swap system. */
export type DashBandDef = { id: string; height?: number | "auto"; before?: React.ReactNode; panels: DashBandPanel[] };

export function DashBandSet({ bands }: { bands: DashBandDef[] }) {
  const lab = useContext(LayoutLabContext);
  const reg = new Map<string, ConcretePanel>(
    bands.flatMap((b) => b.panels.filter(Boolean) as ConcretePanel[]).map((p) => [p.id, p]),
  );
  const placed = new Set<string>();
  const rows = bands.map((b) => {
    const declared = (b.panels.filter(Boolean) as ConcretePanel[]).map((p) => p.id);
    const ids = (lab?.arrangement[b.id] ?? declared).filter((id) => reg.has(id) && !placed.has(id));
    ids.forEach((id) => placed.add(id));
    return { b, declared, ids };
  });
  // Leftovers — declared panels a stale arrangement displaced — return home.
  rows.forEach((r) => r.declared.forEach((id) => {
    if (!placed.has(id)) { r.ids.push(id); placed.add(id); }
  }));
  return (
    <>
      {rows.filter((r) => r.ids.length > 0 || r.b.before).map((r) => (
        <React.Fragment key={r.b.id}>
          {r.b.before}
          {r.ids.length > 0 && <DashBand id={r.b.id} height={r.b.height} panels={r.ids.map((id) => reg.get(id)!)} />}
        </React.Fragment>
      ))}
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
  const present = panels.filter(Boolean) as { id: string; weight?: number; node: React.ReactNode }[];

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
  const cols = lab
    ? effWeights.map((w) => `${w}fr`).join(` ${BAND_GAP}px `)
    : effWeights.map((w) => `${w}fr`).join(" ");

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
              {p.node}
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
const SCOPE_BANNER_TOP = 127; // AtlasHeader (72) + lens rail (55) — measured
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
    <div style={{ position: "sticky", top: SCOPE_BANNER_TOP, zIndex: 14, height: 48, background: "rgba(6,13,31,0.92)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", padding: "0 14px" }}>
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

/* ── Small-screen gate ──────────────────────────────────────────────────────
   The dashboard targets ≥1440px (projection, large monitors). Below that, the
   report is the better surface — route there with the selection intact. */
function useWideViewport(): boolean | null {
  const [wide, setWide] = useState<boolean | null>(null);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1440px)");
    const update = () => setWide(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return wide;
}

function NarrowGate() {
  // Preserve the view params across the hop — the report speaks the same URL
  // vocabulary, so the selection survives. (Safe to read render-time here:
  // the gate only renders post-mount, after the matchMedia effect.)
  const qs = typeof window === "undefined" ? "" : window.location.search;
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ maxWidth: 420, border: `1px solid ${HAIR}`, borderRadius: 12, padding: "26px 28px", background: "rgba(255,255,255,0.02)" }}>
        <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", color: "rgba(255,255,255,0.4)", marginBottom: 10 }}>SVAMP · DASHBOARD</div>
        <div style={{ fontFamily: FONT, fontSize: 16, fontWeight: 650, color: "#e8ecf4", marginBottom: 8 }}>This dashboard needs a wider screen.</div>
        <p style={{ fontFamily: FONT, fontSize: 13, lineHeight: 1.6, color: "#9aa6bd", margin: "0 0 18px" }}>
          It targets screens 1440px and up. On this screen, the report carries the same data — with the full
          narrative.
        </p>
        <a href={`/svamp${qs}`} style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "#e8ecf4", textDecoration: "none", border: `1px solid ${HAIR}`, borderRadius: 8, padding: "8px 14px", display: "inline-block" }}>
          Open the report →
        </a>
      </div>
    </div>
  );
}

/* ── Shell ────────────────────────────────────────────────────────────────── */
export default function SvampDashboard() {
  const [lens, setLens] = useState<DashLens>("programs");
  const wide = useWideViewport();
  const colleges = useMemo(
    () => SVAMP_COLLEGE_IDS
      .map((id) => ({ id, config: getCollegeAtlasConfig(id) }))
      .filter((c): c is CollegeRef => c.config !== null),
    [],
  );

  // Masthead stats — the same institutional counts the report's masthead
  // shows, from the same payloads ("—" until they resolve, the report's idiom).
  const [agg, setAgg] = useState<{ colleges: number; occupations: number; region: string } | null>(null);
  const [activePrograms, setActivePrograms] = useState<number | null>(null);
  useEffect(() => {
    getSvampLandscape()
      .then((x) => setAgg({ colleges: x.aggregate.n_colleges, occupations: x.aggregate.n_occupations, region: x.region_display }))
      .catch(() => {});
    getSvampPrograms()
      .then((x) => setActivePrograms(x.tops.filter((t) => t.enrollment_total > 0 || t.awards_total > 0).length))
      .catch(() => {});
  }, []);

  // Adopt the URL's lens after mount (post-hydration, mirroring the report's
  // static-export-safe pattern — no reactive useSearchParams).
  useEffect(() => {
    const p = readSvampParams();
    if (p.lens === "occupations" || p.lens === "employers") setLens(p.lens);
  }, []);

  const switchLens = (l: DashLens) => {
    setLens(l);
    // Absent lens param ⇒ programs default (the report's convention); clear
    // every cross-lens selection key on any switch.
    writeSvampParams({ lens: l === "programs" ? null : l, soc: null, top: null, college: null, emp: null });
  };

  const lensAccent = LENS_ACCENTS[lens];

  if (wide === false) return <NarrowGate />;

  // Employers is full-viewport (State-Atlas parity): the shell stops scrolling
  // and becomes a fixed flex column so the map fills the screen and only the
  // search rail scrolls. Programs/Occupations keep their stacked-band page scroll.
  const employersFull = lens === "employers";

  return (
    <div data-dash-scroll style={{ position: "fixed", inset: 0, zIndex: 10, background: BG, overscrollBehavior: "none", ...(employersFull ? { display: "flex", flexDirection: "column", overflow: "hidden" } : { overflowY: "auto" }) }}>
      {/* Nav (revised from H1): Kallipolis brand left (no cube — the
          dashboard's identity is the product's), consortium title + PREVIEW
          MODE center, the surface forms (dashboard · report) right in
          glowing white. No masthead below — the nav already carries the
          title, so the old eyebrow/title were pure duplication. */}
      <AtlasHeader title="Silicon Valley Advanced Manufacturing Partnership" leftSlot={<KallipolisBrand />} rightSlot={<SurfaceNav active="dashboard" />} position="sticky" showPreview titleSize="15px" />

      {/* Lens rail — first row under the nav: tabs left, the consortium's
          stats right on the same rail (the masthead's surviving content),
          pinned together on scroll. */}
      <div style={{ position: "sticky", top: 72, zIndex: 15, background: BG, padding: "14px 16px 0" }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 24 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <LensTabs lens={lens} setLens={switchLens} />
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, paddingBottom: 14, borderBottom: `1px solid rgba(255,255,255,.08)`, marginBottom: 4, fontFamily: FONT, fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
            <span style={{ color: lensAccent, opacity: 0.8 }}>{agg ? agg.colleges : "—"} Member Colleges</span>
            <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{activePrograms ?? "—"} Programs</span>
            <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{agg ? agg.occupations : "—"} Occupations</span>
            <Dot /><span style={{ color: lensAccent, opacity: 0.8 }}>{agg ? agg.region : "—"}</span>
          </div>
        </div>
      </div>

      {/* Lens body — Programs and Occupations share the dashboard grammar;
          Employers is its own state. */}
      <div style={{ display: "flex", flexDirection: "column", ...(employersFull ? { flex: 1, minHeight: 0, overflow: "hidden", padding: "12px 16px 16px" } : { padding: "12px 16px 24px" }) }}>
        {lens === "programs" ? <SvampDashboardPrograms colleges={colleges} />
          : lens === "occupations" ? <SvampDashboardOccupations colleges={colleges} />
          : <SvampDashboardEmployers colleges={colleges} />}
      </div>
    </div>
  );
}
