"use client";

/* ── Industry rail — the SWP-sector channel selector ───────────────────────
   First row of the dashboard's sticky stack, above the lens tabs: it holds the
   MEMBER (school/district/consortium) and region constant and swaps the industry
   — the axis you used to navigate *to* (separate URLs per sector) becomes the
   axis you navigate *through*. One row of platonic forms (see industryForms):
   the active industry wears the active LENS accent (the same color the tabs and
   chips show), so color reads as "the current view" and SHAPE reads as the
   industry — never an eleven-hue palette.

   Generalized across every member:
   - PINNED instances (smccd-*) source their sibling sectors from the
     landscapeInstances table (sync) and navigate the flat /smccd-<sector> URLs.
   - GENERATED instances (any college/district at /landscape/<member>/<sector>)
     source their sibling sectors from the backend landscape index (the member's
     live sectors) and navigate /landscape/<member>/<sector>.
   Either way the current surface (dashboard vs /report) and the selection params
   are preserved across the hop, so views stay deep-linkable. Renders only when a
   member has ≥2 sectors (a single-sector member / SVAMP gets no rail). */

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MONO } from "@/college-atlas/partnerships/reportChrome";
import { memberSectors, isLandscapeViewable, RAIL_ORDER } from "@/college-atlas/partnerships/landscapeInstances";
import { fetchLandscapeIndex, type LandscapeIndexEntry } from "@/college-atlas/partnerships/landscapeIndex";
import { INDUSTRY_FORMS } from "@/college-atlas/partnerships/industryForms";

type RailItem = { sectorId: string; label: string; href: string; active: boolean };

// Pinned (smccd-*): the SMCCD sector table, flat /smccd-<sector> URLs. Unchanged.
function pinnedItems(instance: string): RailItem[] {
  return memberSectors(instance)
    .filter((s) => isLandscapeViewable(s.instanceId))
    .map((s) => ({ sectorId: s.sectorId, label: s.label, href: `/${s.instanceId}`, active: s.instanceId === instance }));
}

// Generated (/landscape/<member>/<sector>): the member's ACTIVE sectors straight
// from the backend landscape index, in curatorial order, with /landscape/<member>/
// <sector> URLs. The index is active-aware — a sector enters it only when the member
// runs a program with recent completers or enrollment there (registry.live_catalog,
// the same active gate the Programs lens filters its rows by) — so no client filter
// is needed: every listed sector renders a populated dashboard. (Was Bay-only:
// filtered to cluster targets, which erased the rail for the ~90 non-Bay colleges.)
function generatedItems(instance: string, index: LandscapeIndexEntry[]): RailItem[] {
  const current = index.find((e) => e.id === instance);
  if (!current) return [];
  const bySector = new Map(index.filter((e) => e.member_id === current.member_id).map((e) => [e.sector_id, e]));
  return RAIL_ORDER
    .filter((sid) => bySector.has(sid))
    .map((sid) => {
      const e = bySector.get(sid)!;
      return { sectorId: sid, label: e.sector_label, href: `/landscape/${e.member_id}/${sid}`, active: e.id === instance };
    });
}

export default function IndustryRail({ instance, activeAccent }: { instance: string; activeAccent: string }) {
  const router = useRouter();
  const isPinned = instance.startsWith("smccd-") || instance.startsWith("baccc-");
  // Generated members read their sibling sectors from the index (async, cached).
  // The index is already active-filtered (registry.live_catalog), so the fetched
  // set IS the rail set — no client-side cluster filter.
  const [index, setIndex] = useState<LandscapeIndexEntry[] | null>(isPinned ? [] : null);
  useEffect(() => {
    if (isPinned) return;
    let alive = true;
    fetchLandscapeIndex().then((idx) => { if (alive) setIndex(idx); });
    return () => { alive = false; };
  }, [isPinned, instance]);

  // In-place college route (/[collegeId]/partnerships): the rail switches sector via
  // ?sector= on THIS url (a pre-rendered page) instead of navigating into /landscape/*.
  // Detect the collegeId post-mount — render-time window reads are hydration-unstable.
  const [collegeId, setCollegeId] = useState<string | null>(null);
  useEffect(() => {
    const m = window.location.pathname.replace(/\/$/, "").match(/^\/([^/]+)\/partnerships(?:\/report)?$/);
    setCollegeId(m ? m[1] : null);
  }, [instance]);
  const collegeHref = (sectorId: string) => {
    const isReport = window.location.pathname.replace(/\/$/, "").endsWith("/report");
    const sp = new URLSearchParams(window.location.search);
    sp.set("sector", sectorId);   // preserves lens/soc/etc.; swaps the sector
    return `/${collegeId}/partnerships${isReport ? "/report" : ""}?${sp.toString()}`;
  };

  const ready = isPinned || index !== null;
  const items = isPinned ? pinnedItems(instance) : index ? generatedItems(instance, index) : [];
  if (!ready || items.length < 2) return null;

  return (
    <div style={{ display: "flex", gap: 2, overflowX: "auto", paddingBottom: 10, marginBottom: 12, borderBottom: "1px solid rgba(255,255,255,.06)" }}>
      {items.map((it) => {
        const def = INDUSTRY_FORMS[it.sectorId];
        if (!def) return null;
        const { Form } = def;
        return (
          <a
            key={it.sectorId}
            href={collegeId ? collegeHref(it.sectorId) : it.href}
            title={it.label}
            aria-label={it.label}
            aria-current={it.active ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              if (it.active) return;
              // In-place college route: swap ?sector= on this pre-rendered page.
              if (collegeId) { window.location.href = collegeHref(it.sectorId); return; }
              // Preserve the current surface (dashboard vs /report) + selection.
              // Normalize the static-export trailing slash (the report is served
              // at .../report/, so a raw endsWith would miss and drop the report
              // surface when switching sectors).
              const isReport = window.location.pathname.replace(/\/$/, "").endsWith("/report");
              const href = `${it.href}${isReport ? "/report" : ""}${window.location.search}`;
              // Pinned routes are pre-rendered → fast client nav. Generated
              // /landscape/* routes are SPA-fallback-served (no per-instance RSC
              // payload), so router.push would 404 the prefetch and stall;
              // hard-navigate so the request re-enters through the _redirects shell.
              if (isPinned) router.push(href);
              else window.location.href = href;
            }}
            onMouseEnter={(e) => { if (!it.active) (e.currentTarget as HTMLElement).style.color = "#cdd5e4"; }}
            onMouseLeave={(e) => { if (!it.active) (e.currentTarget as HTMLElement).style.color = "#5e6a83"; }}
            style={{ position: "relative", flex: "1 1 0", minWidth: 60, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: "4px 6px 9px", textDecoration: "none", color: it.active ? "#e8ecf4" : "#5e6a83", cursor: it.active ? "default" : "pointer", transition: "color .16s", WebkitTapHighlightColor: "transparent" }}
          >
            <span style={{ width: 19, height: 19, display: "flex", color: it.active ? activeAccent : "#5e6a83", transition: "color .16s" }}><Form /></span>
            <span style={{ fontFamily: MONO, fontSize: 8.5, fontWeight: 600, letterSpacing: ".07em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{def.short}</span>
            {it.active && <span style={{ position: "absolute", left: "16%", right: "16%", bottom: -1, height: 2, background: activeAccent, borderRadius: 2 }} />}
          </a>
        );
      })}
    </div>
  );
}
