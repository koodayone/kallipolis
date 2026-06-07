"use client";

/* ── Dashboard · Programs lens (Phase 3) ────────────────────────────────────
   The dashboard grammar's first instantiation: coverage matrix (lead, 2:1) +
   supply treemap across the top, the single-scope four-panel band below
   (decided B2; proportions decided in the layout lab 2026-06-06).
   Selection: treemap rect / matrix row ⇒ consortium scope; matrix cell ⇒ that
   college's scope, where the decompositions (credential types, credit
   families) live — the same semantics as the report's ProgramsLens, with the
   toggle transposed into the selection itself. URL: `top` / `college` params
   via svampUrl (shared vocabulary with the report, so views hop surfaces with
   selection intact). */

import React, { useEffect, useMemo, useRef, useState } from "react";
import { MONO } from "@/college-atlas/partnerships/reportChrome";
import { SchoolConfig } from "@/config/schoolConfig";
import SupplyTreemap from "@/college-atlas/partnerships/SupplyTreemap";
import CoverageMatrix from "@/college-atlas/partnerships/CoverageMatrix";
import TrendChart from "@/college-atlas/partnerships/TrendChart";
import WageOutcomes from "@/college-atlas/partnerships/WageOutcomes";
import OccupationDemandTable from "@/college-atlas/partnerships/OccupationDemandTable";
import ProgramPathway from "@/college-atlas/partnerships/ProgramPathway";
import { DashPanel, DashBandSet, ScopeBanner, SvampLoading, type DashBandDef } from "@/college-atlas/partnerships/SvampDashboard";
import {
  shortName, leadOverlayColors, awardYearLabel, shortAwardType, shortCreditType,
} from "@/college-atlas/partnerships/chartKit";
import { getSvampPrograms, getSvampProgram } from "@/college-atlas/partnerships/api";
import type { ApiSvampProgramsLandscape, ApiSvampProgramReport } from "@/college-atlas/partnerships/api";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";

const ACCENT = "#50c878";        // Programs lens green (mirrors the report)
const DEMAND_ACCENT = "#c9a84c"; // demand reference gold (mirrors the report)

export type CollegeRef = { id: string; config: SchoolConfig };

export default function SvampDashboardPrograms({ colleges }: { colleges: CollegeRef[] }) {
  const [land, setLand] = useState<ApiSvampProgramsLandscape | null>(null);
  const [top, setTop] = useState<string | null>(null);
  // null ⇒ consortium scope; a college id ⇒ that college's scope.
  const [collegeId, setCollegeId] = useState<string | null>(null);
  const [report, setReport] = useState<ApiSvampProgramReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  // URL params read once at mount; adopted when the landscape arrives.
  const urlRef = useRef(readSvampParams());

  const nameById = useMemo(() => new Map(colleges.map((c) => [c.id, c.config.name])), [colleges]);
  const brandByName = useMemo(() => new Map(colleges.map((c) => [c.config.name, c.config.brandColorLight])), [colleges]);
  const collegeName = collegeId ? nameById.get(collegeId) : undefined;

  useEffect(() => {
    getSvampPrograms()
      .then((d) => {
        setLand(d);
        const u = urlRef.current;
        const urlTop = u.top && d.tops.some((t) => t.top6 === u.top) ? u.top : null;
        setTop((cur) => cur ?? urlTop ?? d.tops[0]?.top6 ?? null);
        if (u.college && colleges.some((c) => c.id === u.college)) setCollegeId(u.college);
      })
      .catch((e) => setErr(e.message));
    // colleges is config-static for the SVAMP five.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!top) return;
    let alive = true;
    getSvampProgram(top, collegeName).then((r) => { if (alive) setReport(r); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, [top, collegeName]);

  // User-driven selection → state + URL (shared vocabulary with the report).
  const selectConsortium = (t: string) => {
    setTop(t); setCollegeId(null);
    writeSvampParams({ top: t, college: null });
  };
  const selectCell = (t: string, cid: string) => {
    setTop(t); setCollegeId(cid);
    writeSvampParams({ top: t, college: cid });
  };

  if (err) return <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#e0654f", fontFamily: MONO, fontSize: 12 }}>Failed to load: {err}</div>;
  if (!land) return <SvampLoading />;

  // Coverage matrix inputs — identical semantics to the report's ProgramsLens.
  const cols = colleges.map((c) => ({ id: c.id, label: shortName(c.config.name), brand: c.config.brandColorLight }));
  const cellByKey = new Map((land.matrix?.cells ?? []).map((c) => [c.college + "|" + c.top6, c]));
  const rows = land.tops
    .filter((t) => t.enrollment_total > 0 || t.awards_total > 0)
    .map((t) => ({ id: t.top6, label: t.name, sublabel: `TOP ${t.top6}`, title: t.name }));
  const level = (rowId: string, colId: string): "none" | "partial" | "strong" => {
    const name = nameById.get(colId);
    const cell = name ? cellByKey.get(name + "|" + rowId) : undefined;
    if (!cell) return "none";
    const enrolled = cell.enrolled, awarded = cell.awards > 0;
    if (enrolled && awarded) return "strong";
    return enrolled || awarded ? "partial" : "none";
  };

  const scopeBrand = collegeName ? (brandByName.get(collegeName) ?? ACCENT) : ACCENT;
  const topName = land.tops.find((t) => t.top6 === top)?.name ?? top ?? "";

  // College scope decompositions (the report's targeted view, transposed).
  const typeSeries = collegeName && report ? report.awards_by_type.filter((s) => s.college === collegeName) : [];
  const creditSeries = collegeName && report ? report.enrollment_by_credit.filter((s) => s.college === collegeName) : [];
  const typeColor = leadOverlayColors(typeSeries.map((s) => ({ key: s.award_type, vals: s.vals })), scopeBrand);
  const creditColor = leadOverlayColors(creditSeries.map((s) => ({ key: s.credit_type, vals: s.vals })), scopeBrand);
  const collegeColor = (name: string) => brandByName.get(name) ?? ACCENT;
  // Regional addressable demand — Σ openings across the SOCs this program
  // feeds (clean within one program; never summed across programs). The
  // "Occupations served" panel is this number's decomposition. Consortium only.
  const addressableDemand = (report?.occupations ?? []).reduce((t, o) => t + (o.annual_openings ?? 0), 0);

  // Panels as manifest entries — DashBand lays each row out as an fr-grid
  // driven by these author-qualified ids (the layout lab's weight keys).
  const supplyPanel = {
    id: "programs.supply",
    node: (
      <DashPanel title="Program Supply" authority="DataMart" accent={ACCENT}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <SupplyTreemap tops={land.tops} selectedTop={collegeId ? null : top} onSelect={selectConsortium} accent={ACCENT} fill />
        </div>
      </DashPanel>
    ),
  };
  const coveragePanel = {
    id: "programs.coverage",
    // Coverage leads the top band at 2:1 over the supply treemap — decided in
    // the layout lab (2026-06-06): the matrix is the read, the treemap the picker.
    weight: 2,
    node: (
      <DashPanel title="Program Coverage" authority="DataMart" accent={ACCENT}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <CoverageMatrix
            flush
            cols={cols}
            rows={rows}
            level={level}
            selectedRow={top}
            selectedCol={collegeId}
            cornerLabel="↓ program · → college"
            gapCellHint="no enrollment or awards here"
            legend={[
              { k: "Covered", sub: "enrollment & awards", bg: "rgba(148,168,201,.92)", ring: true },
              { k: "Partial", sub: "enrollment or awards", bg: "rgba(148,168,201,.3)", ring: true },
              { k: "Gap", sub: "neither", bg: "rgba(255,255,255,.035)", ring: false },
            ]}
            onSelect={selectCell}
            onSelectRow={selectConsortium}
          />
        </div>
      </DashPanel>
    ),
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Scope banner leads the lens (revised 2026-06-07): the sticky stack
          reads nav → rail → banner from the first pixel, and the aggregates'
          selection rings mark the named scope below. */}
      <ScopeBanner
        brand={scopeBrand}
        scope={collegeName ?? "Consortium"}
        name={topName}
        code={`TOP ${top}`}
      />
      {/* One band set per lens: top band (the lens's two aggregates), then the
          scope bands (four panels, one scope — decided B2), two per row at
          width-driven proportions, content-driven heights. The set is the
          layout lab's swap boundary — any panel can trade places with any
          other. Charts are scope-keyed so each scope entry lands on its
          default mode. */}
      <DashBandSet bands={[
        { id: "programs.top", panels: [coveragePanel, supplyPanel] },
        ...buildScopeBands(),
      ]} />
    </div>
  );

  // Hoisted so the return stays a readable manifest; closes over the scope
  // state above. Crosswalk present ⇒ it pairs with wages and occupations takes
  // its own full-width row; absent ⇒ occupations pairs with wages.
  function buildScopeBands(): DashBandDef[] {
        const awardsPanel = {
          id: "programs.awards",
          node: (
            <DashPanel title="Awards" authority={collegeName ? "DataMart" : "DataMart · COE"} accent={scopeBrand}>
              <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
                {report && (
                  <TrendChart
                    key={(collegeId ?? "consortium") + ":awards"}
                    series={typeSeries.length > 0
                      ? typeSeries.map((s) => ({ top6: s.award_type, name: shortAwardType(s.award_type), vals: s.vals }))
                      : report.awards_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
                    labels={report.award_years.map(awardYearLabel)}
                    defaultMode="stacked"
                    colorOf={typeSeries.length > 0 ? typeColor : collegeColor}
                    modeLabels={typeSeries.length > 0 ? { lines: "Per credential", stacked: "Stacked" } : { lines: "Per school", stacked: "Stacked", demand: "Demand" }}
                    hideSeriesTag
                    empty={report.awards_by_college.length === 0}
                    demandLine={!collegeName && addressableDemand > 0
                      ? { value: addressableDemand, label: "Regional Demand · COE", color: DEMAND_ACCENT }
                      : undefined}
                    fill
                  />
                )}
              </div>
            </DashPanel>
          ),
        };
        const enrollPanel = {
          id: "programs.enrollments",
          node: (
            <DashPanel title="Enrollments" authority="DataMart" accent={scopeBrand}>
              <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
                {report && (
                  <TrendChart
                    key={(collegeId ?? "consortium") + ":enroll"}
                    series={creditSeries.length > 0
                      ? creditSeries.map((s) => ({ top6: s.credit_type, name: shortCreditType(s.credit_type), vals: s.vals }))
                      : report.enrollment_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
                    labels={report.enrollment_terms}
                    defaultMode="lines"
                    colorOf={creditSeries.length > 0 ? creditColor : collegeColor}
                    axisStyle="twoTier"
                    modeLabels={creditSeries.length > 0 ? { lines: "Per credit family", stacked: "Stacked" } : { lines: "Per school", stacked: "Stacked" }}
                    hideSeriesTag
                    empty={report.enrollment_by_college.length === 0}
                    fill
                  />
                )}
              </div>
            </DashPanel>
          ),
        };
        const wagesPanel = {
          id: "programs.wages",
          node: (
            <DashPanel title="Wage Outcomes" authority="DataMart" accent={scopeBrand}>
              <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
                {/* Empty wages render WageOutcomes' own ghost scaffold (the
                    shared "No data reported" chart-frame grammar). */}
                {report && (
                  <WageOutcomes
                    programs={[{ top6: report.top6, name: report.name, awards_recent: 0, awards: [], enrollment: [], wages: report.wages }]}
                    brandColor={scopeBrand}
                    fill
                  />
                )}
              </div>
            </DashPanel>
          ),
        };
        const hasCrosswalk = !!(report?.crosswalk && report.crosswalk.socs.length > 0);
        const crosswalkPanel = hasCrosswalk && report?.crosswalk
          ? {
              id: "programs.crosswalk",
              node: (
                <DashPanel title="Crosswalk" authority="CCCCO · NCES" accent={scopeBrand}>
                  {/* Centered: the diagram's height is width-driven, so in a
                      taller row it floats — centering splits the slack. */}
                  <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", justifyContent: "center" }}>
                    <ProgramPathway crosswalk={report.crosswalk} accent={scopeBrand} prose={false} />
                  </div>
                </DashPanel>
              ),
            }
          : null;
        const occupationsPanel = {
          id: "programs.occupations",
          // Scope-keyed like the report's table (reportBrand): programs green
          // at consortium, the college's brand in college scope.
          node: (
            <DashPanel title="Occupations Served" authority="COE" accent={scopeBrand}>
              <div>
                {report && report.occupations.length > 0 ? (
                  <OccupationDemandTable rows={report.occupations} brandColor={scopeBrand} label={null} />
                ) : (
                  <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 10.5 }}>no demanded occupations in scope</div>
                )}
              </div>
            </DashPanel>
          ),
        };
        // scopeB carries an explicit height: both wages (height-fill) and the
        // crosswalk (fit-to-container) size to their row rather than prop it
        // up. 445 matches the occupations lens's crosswalk row.
        return [
          { id: "programs.scopeA", panels: [awardsPanel, enrollPanel] },
          { id: "programs.scopeB", height: 445, panels: [wagesPanel, crosswalkPanel ?? occupationsPanel] },
          ...(crosswalkPanel ? [{ id: "programs.scopeC", panels: [occupationsPanel] }] : []),
        ];
  }
}
