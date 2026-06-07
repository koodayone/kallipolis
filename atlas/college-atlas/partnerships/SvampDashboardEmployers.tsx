"use client";

/* ── Dashboard · Employers state (Phase 5) ──────────────────────────────────
   Its own state, entered by the tab — the dashboard grammar (treemap, matrix,
   scope band, selection model) deliberately does not apply here, and no
   selection crosses the lens boundary (decided fork 4). Full-bleed regional
   employer map at State-Atlas parity, with the searchable directory as a
   rail. shown/total stays — an ungeocoded remainder never reads as complete.
   URL: the `emp` param, same slice the report's employers lens writes.

   `stacked` (shell-decided, below ~760px viewport): the side-by-side row
   becomes a column — map above at a viewport fraction, directory below with
   its own internal scroll — and the page scrolls instead of the fixed
   full-bleed shell. Same panels, same selection model, compressed. */

import React, { useEffect, useMemo, useRef, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { SchoolConfig } from "@/config/schoolConfig";
import EmployerMap, { type MapCollege } from "@/college-atlas/partnerships/EmployerMap";
import { DashPanel, SvampLoading } from "@/college-atlas/partnerships/SvampDashboard";
import { getSvampEmployers } from "@/college-atlas/partnerships/api";
import type { ApiSvampEmployersResult } from "@/college-atlas/partnerships/api";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";
import EmployerListRow from "@/college-atlas/partnerships/EmployerListRow";

const ACCENT = "#5a9bd4"; // Employers lens blue (mirrors the report)

type CollegeRef = { id: string; config: SchoolConfig };

// Member-college coordinates for the map's context anchors (mirrors the
// report's SVAMP_COLLEGE_GEO — fixed, five colleges).
const COLLEGE_GEO: Record<string, [number, number]> = {
  "De Anza College": [37.31, -122.04],
  "Foothill College": [37.36, -122.05],
  "Evergreen Valley College": [37.34, -121.80],
  "Mission College": [37.39, -121.98],
  "Ohlone College": [37.53, -121.91],
};

export default function SvampDashboardEmployers({ colleges, stacked = false }: { colleges: CollegeRef[]; stacked?: boolean }) {
  const [data, setData] = useState<ApiSvampEmployersResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [ready, setReady] = useState(false);
  const rowRefs = useRef<Map<string, HTMLButtonElement | null>>(new Map());

  useEffect(() => {
    let alive = true;
    getSvampEmployers().then((d) => { if (alive) setData(d); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, []);

  // Restore the emp slice from the URL on mount, then sync emp → URL (the
  // report's pattern; `ready` gates writes until the restore has run).
  useEffect(() => {
    const p = readSvampParams();
    if (p.emp) setSelected(p.emp);
    setReady(true);
  }, []);
  useEffect(() => {
    if (!ready) return;
    writeSvampParams({ emp: selected ?? null });
  }, [ready, selected]);
  useEffect(() => {
    if (selected) rowRefs.current.get(selected)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selected]);

  const anchors: MapCollege[] = useMemo(
    () => colleges.flatMap((c) => {
      const geo = COLLEGE_GEO[c.config.name];
      return geo ? [{ name: c.config.name, lat: geo[0], lng: geo[1], brand: c.config.brandColorLight }] : [];
    }),
    [colleges],
  );

  if (err) return <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#e0654f", fontFamily: MONO, fontSize: 12 }}>Failed to load employers: {err}</div>;
  if (!data) return <SvampLoading />;

  const q = query.trim().toLowerCase();
  const filtered = (q ? data.employers.filter((e) => e.name.toLowerCase().includes(q)) : data.employers)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name));
  const toggle = (n: string | null) => setSelected((cur) => (n === null ? null : cur === n ? null : n));

  return (
    <div style={stacked
      ? { display: "flex", flexDirection: "column", gap: 8 }
      : { flex: 1, minHeight: 0, display: "flex", gap: 8 }}>
      {/* Full-bleed map — the surface-area parity the fork decided. Stacked:
          explicit viewport-fraction heights (flex grow has no basis once the
          page scrolls), directory keeps its internal list scroll. */}
      <DashPanel title="Regional Employer Map" authority="EDD" accent={ACCENT} grow={3} style={stacked ? { height: "55vh", flex: "none" } : undefined}>
        <div style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <EmployerMap
            employers={data.employers}
            colleges={anchors}
            selected={selected}
            hover={hover}
            onSelect={toggle}
            onHover={setHover}
          />
        </div>
      </DashPanel>

      {/* Directory rail — searchable, A→Z; map ↔ list selection synced. */}
      <DashPanel title="Employers" authority="EDD" accent={ACCENT} grow={1} style={stacked ? { height: "60vh", flex: "none" } : undefined}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="search…"
          style={{ flex: "none", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 7, color: "#e8ecf4", fontFamily: FONT, fontSize: 12, padding: "6px 10px", outline: "none", marginBottom: 8 }}
        />
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          {filtered.map((e) => (
            <EmployerListRow
              key={e.name}
              emp={e}
              selected={selected === e.name}
              hovered={hover === e.name}
              onSelect={() => toggle(e.name)}
              onHover={(on) => setHover(on ? e.name : null)}
              accent={ACCENT}
              rowRef={(el) => { rowRefs.current.set(e.name, el); }}
            />
          ))}
        </div>
      </DashPanel>
    </div>
  );
}
