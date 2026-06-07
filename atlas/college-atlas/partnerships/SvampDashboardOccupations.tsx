"use client";

/* ── Dashboard · Occupations lens (Phase 4) ─────────────────────────────────
   The dashboard grammar over the SOC axis: demand treemap + coverage matrix
   across the top, the single-scope band below (decided B2).

   Scope semantics mirror the Programs lens with the axis flipped:
   - Consortium scope (treemap rect / matrix row): demand summary (openings,
     wage, growth, employment, COE-projected supply and the GAP — the
     occupation axis owns the gap), awards summed over feeding programs with
     the shortage-floor demand line (every feeding program counted in full vs
     the SOC's counted-once openings), enrollments, and the feeding programs.
   - College scope (matrix cell): that college's feeding programs' own series.
     Deliberately NO wage panel (statewide TOP6 data under a college brand
     asserts an outcome the data cannot support — same curation as the report)
     and NO demand line (one college vs regional demand is partial-vs-whole).

   URL: `soc` / `college` params via svampUrl — shared vocabulary with the
   report, so views hop surfaces with selection intact. */

import React, { useEffect, useMemo, useRef, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { SchoolConfig } from "@/config/schoolConfig";
import DemandTreemap from "@/college-atlas/partnerships/DemandTreemap";
import CoverageMatrix from "@/college-atlas/partnerships/CoverageMatrix";
import TrendChart from "@/college-atlas/partnerships/TrendChart";
import { DashPanel } from "@/college-atlas/partnerships/SvampDashboard";
import { shortName, hexA, leadOverlayColors, awardYearLabel } from "@/college-atlas/partnerships/chartKit";
import { getSvampLandscape, getSvampOccupation } from "@/college-atlas/partnerships/api";
import type { ApiSvampLandscape, ApiSvampCell, ApiSvampOccupationReport } from "@/college-atlas/partnerships/api";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";

const ACCENT = "#ff5a5a";        // Occupations lens red (mirrors the report)
const DEMAND_ACCENT = "#c9a84c"; // demand reference gold

type CollegeRef = { id: string; config: SchoolConfig };

// Cell coverage level — activity-keyed, identical to the report's level().
function level(cell: ApiSvampCell | undefined): "none" | "partial" | "strong" {
  if (!cell) return "none";
  const enrolled = cell.enrolled, awarded = cell.feeding_awards > 0;
  if (enrolled && awarded) return "strong";
  return enrolled || awarded ? "partial" : "none";
}

function StatRow({ k, v, accent }: { k: string; v: string; accent?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 8, padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      <span style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.08em", color: "#5e6a83", flex: 1, textTransform: "uppercase" }}>{k}</span>
      <span style={{ fontFamily: MONO, fontSize: 12.5, fontWeight: 600, color: accent ?? "rgba(255,255,255,0.88)" }}>{v}</span>
    </div>
  );
}

export default function SvampDashboardOccupations({ colleges }: { colleges: CollegeRef[] }) {
  const [land, setLand] = useState<ApiSvampLandscape | null>(null);
  const [soc, setSoc] = useState<string | null>(null);
  // null ⇒ consortium scope; a college id ⇒ that college's scope.
  const [collegeId, setCollegeId] = useState<string | null>(null);
  const [report, setReport] = useState<ApiSvampOccupationReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const urlRef = useRef(readSvampParams());

  const nameById = useMemo(() => new Map(colleges.map((c) => [c.id, c.config.name])), [colleges]);
  const brandByName = useMemo(() => new Map(colleges.map((c) => [c.config.name, c.config.brandColorLight])), [colleges]);
  const collegeName = collegeId ? nameById.get(collegeId) : undefined;

  useEffect(() => {
    getSvampLandscape()
      .then((d) => {
        setLand(d);
        const cells = d.colleges[0]?.cells ?? [];
        const u = urlRef.current;
        const urlSoc = u.soc && cells.some((c) => c.soc_code === u.soc) ? u.soc : null;
        // Default: the highest-demand occupation (the report's landing too).
        const topSoc = [...cells].sort((a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0))[0]?.soc_code ?? null;
        setSoc((cur) => cur ?? urlSoc ?? topSoc);
        if (u.college && colleges.some((c) => c.id === u.college)) setCollegeId(u.college);
      })
      .catch((e) => setErr(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!soc) return;
    let alive = true;
    getSvampOccupation(soc).then((r) => { if (alive) setReport(r); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, [soc]);

  const selectConsortium = (s: string) => {
    setSoc(s); setCollegeId(null);
    writeSvampParams({ soc: s, college: null });
  };
  const selectCell = (s: string, cid: string) => {
    setSoc(s); setCollegeId(cid);
    writeSvampParams({ soc: s, college: cid });
  };

  if (err) return <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#e0654f", fontFamily: MONO, fontSize: 12 }}>Failed to load: {err}</div>;
  if (!land) return <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 11 }}>loading…</div>;

  const refCells = land.colleges[0]?.cells ?? [];
  const cols = colleges.map((c) => ({ id: c.id, label: shortName(c.config.name), brand: c.config.brandColorLight }));
  const rows = refCells.map((c) => ({ id: c.soc_code, label: c.title, sublabel: c.soc_code, title: c.title }));
  const cellOf = (rowId: string, colId: string): ApiSvampCell | undefined => {
    const name = nameById.get(colId);
    return land.colleges.find((c) => c.name === name)?.cells.find((c) => c.soc_code === rowId);
  };

  const scopeBrand = collegeName ? (brandByName.get(collegeName) ?? ACCENT) : ACCENT;
  const socTitle = refCells.find((c) => c.soc_code === soc)?.title ?? soc ?? "";
  const collegeColor = (name: string) => brandByName.get(name) ?? ACCENT;

  // College scope: that college's feeding programs (the landscape cell carries
  // them), charted per program with lead/overlay colors in the college brand.
  const cell = collegeName && soc
    ? land.colleges.find((c) => c.name === collegeName)?.cells.find((c) => c.soc_code === soc)
    : undefined;
  const cellPrograms = cell?.programs ?? [];
  const programColor = leadOverlayColors(
    cellPrograms.map((p) => ({ key: p.top6, vals: (p.awards ?? []).map((v) => v ?? 0) })),
    scopeBrand,
  );

  const fmt = (v: number | null | undefined, suffix = "") => (v == null ? "—" : v.toLocaleString("en-US") + suffix);

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Top band — regional demand hero + coverage. */}
      <div style={{ flex: 5, minHeight: 0, display: "flex", gap: 8 }}>
        <DashPanel title="Regional demand" authority="COE" accent={ACCENT}>
          <div style={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
            <DemandTreemap cells={refCells} total={land.aggregate.regional_demand_total} selected={collegeId ? null : soc} onSelect={selectConsortium} />
          </div>
        </DashPanel>
        <DashPanel title="Coverage — college × occupation" authority="DataMart" accent={ACCENT}>
          <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
            <CoverageMatrix
              cols={cols}
              rows={rows}
              level={(r, c) => level(cellOf(r, c))}
              selectedRow={soc}
              selectedCol={collegeId}
              cornerLabel="↓ occupation · → college"
              gapCellHint="no feeding-program activity here"
              legend={[
                { k: "Covered", sub: "enrollment & awards", bg: "rgba(148,168,201,.92)", ring: true },
                { k: "Partial", sub: "enrollment or awards", bg: "rgba(148,168,201,.3)", ring: true },
                { k: "Gap", sub: "neither", bg: "rgba(255,255,255,.035)", ring: false },
              ]}
              caption="A row is the consortium scope — a cell is that college's scope."
              onSelect={selectCell}
              onSelectRow={selectConsortium}
            />
          </div>
        </DashPanel>
      </div>

      {/* Scope row. */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flex: "none" }}>
        <span style={{ fontFamily: FONT, fontSize: 11, fontWeight: 700, letterSpacing: "0.16em", color: scopeBrand, whiteSpace: "nowrap" }}>
          {collegeName ? shortName(collegeName).toUpperCase() : "CONSORTIUM"}
        </span>
        <span style={{ fontFamily: FONT, fontSize: 12.5, color: "rgba(255,255,255,0.85)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{socTitle}</span>
        <span style={{ fontFamily: MONO, fontSize: 10, color: hexA(scopeBrand, 0.65), whiteSpace: "nowrap" }}>{soc}</span>
        {collegeName && (
          <button onClick={() => soc && selectConsortium(soc)} style={{ appearance: "none", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#9aa6bd", fontFamily: MONO, fontSize: 9.5, borderRadius: 6, padding: "2px 8px", cursor: "pointer" }}>
            ← consortium
          </button>
        )}
      </div>

      {/* Scope band. Consortium: summary+gap · awards vs demand · enrollments ·
          feeding programs. College: that college's per-program series + its
          feeding-program facts (no wages, no demand line — see header). */}
      <div style={{ flex: 4, minHeight: 0, display: "flex", gap: 8 }}>
        {!collegeName && (
          <DashPanel title="Demand & gap" authority="COE" accent={ACCENT} grow={0.7}>
            <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
              <StatRow k="Annual openings" v={fmt(report?.annual_openings)} />
              <StatRow k="Median wage" v={report?.annual_wage != null ? "$" + report.annual_wage.toLocaleString("en-US") : "—"} />
              <StatRow k="Growth" v={report?.growth_rate != null ? (report.growth_rate * 100).toFixed(1) + "%" : "—"} />
              <StatRow k="Employment" v={fmt(report?.employment)} />
              <StatRow k="Consortium supply · projected" v={fmt(report?.consortium_supply)} />
              <StatRow k="Gap" v={fmt(report?.gap, "/yr")} accent={DEMAND_ACCENT} />
            </div>
          </DashPanel>
        )}
        <DashPanel title="Awards · feeding programs" authority={collegeName ? "DataMart" : "DataMart · COE"} accent={scopeBrand}>
          <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
            {collegeName ? (
              cellPrograms.length > 0 ? (
                <TrendChart
                  key={collegeId + ":awards"}
                  series={cellPrograms.map((p) => ({ top6: p.top6, name: p.name, vals: p.awards ?? [] }))}
                  labels={land.award_years.map(awardYearLabel)}
                  defaultMode="stacked"
                  colorOf={programColor}
                  empty={!cellPrograms.some((p) => (p.awards ?? []).some((v) => v > 0))}
                />
              ) : (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 10.5 }}>no feeding-program activity here</div>
              )
            ) : (
              report && (
                <TrendChart
                  key="consortium:awards"
                  series={report.awards_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
                  labels={report.award_years.map(awardYearLabel)}
                  defaultMode="stacked"
                  colorOf={collegeColor}
                  modeLabels={{ lines: "Per school", stacked: "Stacked", demand: "Demand" }}
                  hideSeriesTag
                  empty={report.awards_by_college.length === 0}
                  demandLine={(report.annual_openings ?? 0) > 0
                    ? { value: report.annual_openings as number, label: "Regional Demand · COE", color: DEMAND_ACCENT }
                    : undefined}
                />
              )
            )}
          </div>
        </DashPanel>
        <DashPanel title="Enrollments · feeding programs" authority="DataMart" accent={scopeBrand}>
          <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
            {collegeName ? (
              cellPrograms.length > 0 ? (
                <TrendChart
                  key={collegeId + ":enroll"}
                  series={cellPrograms.map((p) => ({ top6: p.top6, name: p.name, vals: p.enrollment ?? [] }))}
                  labels={land.enrollment_terms}
                  defaultMode="lines"
                  colorOf={programColor}
                  axisStyle="twoTier"
                  empty={!cellPrograms.some((p) => (p.enrollment ?? []).some((v) => v != null && v > 0))}
                />
              ) : (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 10.5 }}>no feeding-program activity here</div>
              )
            ) : (
              report && (
                <TrendChart
                  key="consortium:enroll"
                  series={report.enrollment_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
                  labels={report.enrollment_terms}
                  defaultMode="lines"
                  colorOf={collegeColor}
                  axisStyle="twoTier"
                  modeLabels={{ lines: "Per school", stacked: "Stacked" }}
                  hideSeriesTag
                  empty={report.enrollment_by_college.length === 0}
                />
              )
            )}
          </div>
        </DashPanel>
        <DashPanel title="Feeding programs" authority="DataMart" accent="#50c878" grow={0.8}>
          <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
            {(collegeName ? cellPrograms.map((p) => ({ top6: p.top6, name: p.name, n: p.awards_recent })) : (report?.feeding_tops ?? []).map((t) => ({ top6: t.top6, name: t.name, n: t.awards_total })))
              .map((p) => (
                <div key={p.top6} style={{ display: "flex", alignItems: "baseline", gap: 8, padding: "5px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                  <span style={{ fontFamily: MONO, fontSize: 9.5, color: "#5e6a83", flex: "none" }}>{p.top6}</span>
                  <span style={{ fontFamily: FONT, fontSize: 11.5, color: "rgba(255,255,255,0.82)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</span>
                  <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#9aa6bd", flex: "none" }}>{p.n.toLocaleString("en-US")}</span>
                </div>
              ))}
            <div style={{ fontFamily: MONO, fontSize: 8.5, color: "#5e6a83", paddingTop: 6 }}>
              {collegeName ? "latest-year awards at this college" : "latest-year awards · consortium · counted in full per SOC"}
            </div>
          </div>
        </DashPanel>
      </div>
    </div>
  );
}
