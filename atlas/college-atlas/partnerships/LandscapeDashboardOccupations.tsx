"use client";

/* ── Dashboard · Occupations lens (Phase 4) ─────────────────────────────────
   The dashboard grammar over the SOC axis: coverage matrix (lead, 2:1) +
   demand treemap across the top, the single-scope band below (decided B2;
   proportions decided in the layout lab 2026-06-06).

   Scope semantics mirror the Programs lens with the axis flipped:
   - Consortium scope (treemap rect / matrix row): awards summed over feeding
     programs with the shortage-floor demand line (every feeding program
     counted in full vs the SOC's counted-once openings — the supply-vs-demand
     read lives there), enrollments, the crosswalk (which carries the TOP→SOC
     structure — no flat feeding-programs list), and the Occupation Summary
     glyph quartet (the four observed COE figures; the modeled supply/gap
     rows died with the old Demand & Gap panel).
   - College scope (matrix cell): that college's feeding programs' own series.
     Deliberately NO wage panel (statewide TOP6 data under a college brand
     asserts an outcome the data cannot support — same curation as the report)
     and NO demand line (one college vs regional demand is partial-vs-whole).

   URL: `soc` / `college` params via landscapeUrl — shared vocabulary with the
   report, so views hop surfaces with selection intact. */

import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { SchoolConfig } from "@/config/schoolConfig";
import DemandTreemap from "@/college-atlas/partnerships/DemandTreemap";
import CoverageMatrix from "@/college-atlas/partnerships/CoverageMatrix";
import TrendChart from "@/college-atlas/partnerships/TrendChart";
import CurriculumPathway from "@/college-atlas/partnerships/CurriculumPathway";
import { DashPanel, DashBandSet, ScopeBanner, LandscapeLoading, ScopeAccentContext, TotalStrip, type DashBandDef } from "@/college-atlas/partnerships/LandscapeDashboard";
import { shortName, leadOverlayColors, awardYearLabel } from "@/college-atlas/partnerships/chartKit";
import { getLandscape, getLandscapeOccupation } from "@/college-atlas/partnerships/api";
import type { ApiSvampLandscape, ApiSvampCell, ApiSvampOccupationReport } from "@/college-atlas/partnerships/api";
import { readLandscapeParams, writeLandscapeParams } from "@/college-atlas/partnerships/landscapeUrl";
import { OCC_MATRIX_CORNER, occupationMatrixRows } from "@/college-atlas/partnerships/landscapeLabels";

const ACCENT = "#ff5a5a";        // Occupations lens red (mirrors the report)
const DEMAND_ACCENT = "#c9a84c"; // demand reference gold

type CollegeRef = { id: string; config: SchoolConfig };

// Cell coverage level — a visibility read of the two signals (universal): both ⇒
// strong (full pipeline), exactly one ⇒ partial (one of awards/enrollment
// missing), neither ⇒ gap. Enrollment is visibility, not realized supply — supply
// stays awards-only, but an enrolled-yet-ungraduated cell is shown, never hidden.
function level(cell: ApiSvampCell | undefined): "none" | "partial" | "strong" {
  if (!cell) return "none";
  const enrolled = cell.enrolled, awarded = cell.feeding_awards > 0;
  if (enrolled && awarded) return "strong";
  return enrolled || awarded ? "partial" : "none";
}

/* ── Occupation Summary — the four observed COE figures as a glyph quartet
   (decided S1a at /svamp/concepts/stats, 2026-06-06). The modeled rows
   (consortium supply, gap) died with the old "Demand & Gap" panel — the
   supply-vs-demand read lives in the Awards chart's demand line. The glyphs
   are new members of the platonic-form family (32×32, stroke 1.8, reduced
   archetypes): doorway = an opening, banknote = the wage, rising line =
   growth, crew = the employed base. */
const FormDoorway: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M9 27V6h14v21" /><path d="M5 27h22" /><path d="M13 27V9.5l7 2.2V27" /><path d="M17.4 18.6v.01" />
  </svg>
);
const FormBanknote: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <rect x="4" y="9" width="24" height="14" rx="2" /><circle cx="16" cy="16" r="3.6" /><path d="M8 13v6M24 13v6" />
  </svg>
);
const FormRise: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M5 24l8-8 4 4 9-9" /><path d="M20.5 11H26v5.5" /><path d="M5 27.5h22" />
  </svg>
);
const FormCrew: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <circle cx="12" cy="11.5" r="3.8" /><path d="M5 25.5c0-4.2 3.1-6.8 7-6.8s7 2.6 7 6.8" />
    <circle cx="21.5" cy="13" r="3" /><path d="M21.5 19.4c3.2 0 5.4 2.1 5.7 5.4" />
  </svg>
);

function OccupationSummary({ report }: { report: ApiSvampOccupationReport | null }) {
  // All four figures render as peers — no accent (revised in build,
  // 2026-06-06): pre-ranking one number is editorial, and which figure
  // matters most is the reader's call (a negative growth projection can
  // outrank openings). The panel's header tick carries the lens color.
  const cells: { k: string; v: string; sub: string; Icon: React.FC }[] = [
    { k: "Annual Openings", v: report?.annual_openings != null ? report.annual_openings.toLocaleString("en-US") : "—", sub: "/yr · projected", Icon: FormDoorway },
    { k: "Median Wage", v: report?.annual_wage != null ? "$" + report.annual_wage.toLocaleString("en-US") : "—", sub: "annual", Icon: FormBanknote },
    { k: "Growth", v: report?.growth_rate != null ? (report.growth_rate * 100).toFixed(1) + "%" : "—", sub: "projection period", Icon: FormRise },
    { k: "Employment", v: report?.employment != null ? report.employment.toLocaleString("en-US") : "—", sub: "regional jobs", Icon: FormCrew },
  ];
  return (
    <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr" }}>
      {cells.map((s, i) => (
        <div key={s.k} style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 5, borderRight: i % 2 === 0 ? "1px solid rgba(255,255,255,0.05)" : "none", borderBottom: i < 2 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
          <span style={{ width: 22, height: 22, color: "#5e6a83", display: "flex" }}><s.Icon /></span>
          <div style={{ fontFamily: MONO, fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: "#5e6a83" }}>{s.k}</div>
          <div style={{ fontFamily: MONO, fontSize: 31, fontWeight: 600, color: "#e8ecf4", lineHeight: 1 }}>{s.v}</div>
          <div style={{ fontFamily: FONT, fontSize: 11, color: "#5e6a83" }}>{s.sub}</div>
        </div>
      ))}
    </div>
  );
}

export default function LandscapeDashboardOccupations({ colleges, instance = "svamp", primaryCollege = null }: { colleges: CollegeRef[]; instance?: string; primaryCollege?: string | null }) {
  const [land, setLand] = useState<ApiSvampLandscape | null>(null);
  const [soc, setSoc] = useState<string | null>(null);
  // null ⇒ consortium scope; a college id ⇒ that college's scope.
  const [collegeId, setCollegeId] = useState<string | null>(null);
  const [report, setReport] = useState<ApiSvampOccupationReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const urlRef = useRef(readLandscapeParams());

  const nameById = useMemo(() => new Map(colleges.map((c) => [c.id, c.config.name])), [colleges]);
  const brandByName = useMemo(() => new Map(colleges.map((c) => [c.config.name, c.config.brandColorLight])), [colleges]);
  const collegeName = collegeId ? nameById.get(collegeId) : undefined;
  // Report the scope accent to the shell (rail + tabs wear it); null at
  // consortium scope restores the lens hue.
  const scopeAccentCtx = useContext(ScopeAccentContext);
  useEffect(() => {
    scopeAccentCtx?.set(collegeName ? (brandByName.get(collegeName) ?? null) : null);
  }, [collegeName, brandByName, scopeAccentCtx]);

  useEffect(() => {
    getLandscape(instance)
      .then((d) => {
        setLand(d);
        const cells = d.colleges[0]?.cells ?? [];
        const u = urlRef.current;
        // Default among the central school's supported occupations (see possessedSocs).
        const primaryCells = primaryCollege ? (d.colleges.find((c) => c.name === primaryCollege)?.cells ?? []) : null;
        const poss = primaryCells ? new Set(primaryCells.filter((c) => c.feeding_awards > 0).map((c) => c.soc_code)) : null;
        const own = poss ? cells.filter((c) => poss.has(c.soc_code)) : cells;
        const urlSoc = u.soc && own.some((c) => c.soc_code === u.soc) ? u.soc : null;
        // Default: the highest-demand occupation (the report's landing too).
        const topSoc = [...own].sort((a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0))[0]?.soc_code ?? null;
        setSoc((cur) => cur ?? urlSoc ?? topSoc);
        if (u.college && colleges.some((c) => c.id === u.college)) setCollegeId(u.college);
      })
      .catch((e) => setErr(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Refetch on scope change so the SOC-anchored crosswalk lights only the
  // selected college's feeding TOPs in college scope (consortium union when
  // collegeName is undefined). Mirrors the Programs lens's per-college refetch;
  // every other field is scope-invariant, so the rest of the report is stable.
  useEffect(() => {
    if (!soc) return;
    let alive = true;
    // includeEmployers=false: this lens renders no Partnership Opportunities
    // list, so it skips the region-wide employer gather (~94% of the payload
    // and the report's dominant query cost).
    getLandscapeOccupation(soc, collegeName, instance, false).then((r) => { if (alive) setReport(r); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, [soc, collegeName, instance]);

  const selectConsortium = (s: string) => {
    setSoc(s); setCollegeId(null);
    writeLandscapeParams({ soc: s, college: null });
  };
  const selectCell = (s: string, cid: string) => {
    setSoc(s); setCollegeId(cid);
    writeLandscapeParams({ soc: s, college: cid });
  };

  if (err) return <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#e0654f", fontFamily: MONO, fontSize: 12 }}>Failed to load: {err}</div>;
  if (!land) return <LandscapeLoading />;

  const refCells = land.colleges[0]?.cells ?? [];
  // Occupations lens shows the CENTRAL school's supported occupations — the ones its
  // own programs feed. A school actor can't target an occupation it doesn't produce
  // for, so those rows drop; the cross-school coverage of the ones it DOES produce
  // for is what stays. Consortium instances (primaryCollege == null) keep every row.
  const possessedSocs = primaryCollege
    ? new Set((land.colleges.find((c) => c.name === primaryCollege)?.cells ?? []).filter((c) => c.feeding_awards > 0).map((c) => c.soc_code))
    : null;
  const shownDemandCells = possessedSocs ? refCells.filter((c) => possessedSocs.has(c.soc_code)) : refCells;
  const totalDemand = shownDemandCells.reduce((s, c) => s + (c.annual_openings ?? 0), 0);
  // Empty-column drop, scoped to the shown occupations: a college with NO activity
  // toward any of them — neither awards NOR enrollment — is an all-gap column, so
  // drop it. Enrollment counts as activity (a member enrolling toward an occupation
  // it hasn't yet graduated is a live opportunity), so it is never dropped.
  // Universal — coverage_awards_only governs supply QUANTITY, never visibility.
  const participating = new Set(
    land.colleges
      .filter((col) => col.cells.some((c) => (c.feeding_awards > 0 || c.enrolled) && (!possessedSocs || possessedSocs.has(c.soc_code))))
      .map((col) => col.name),
  );
  const shownColleges = colleges.filter((c) => participating.has(c.config.name));
  const cols = shownColleges.map((c) => ({ id: c.id, label: shortName(c.config.name), brand: c.config.brandColorLight }));
  // Consortium scale: matrix takes a full-width row, the demand treemap drops
  // below. Keyed off the full MEMBER count, not the displayed count, so every
  // BACCC view is full-width; the few-member curated instances (SVAMP/SMCCD)
  // keep the 2:1. (Header orientation still flips on displayed cols.)
  const wide = colleges.length >= 12;
  // Row set via the shared adapter (landscapeLabels.occupationMatrixRows): demand
  // sort + role vocabulary + SOC provenance sublabel, identical to the report
  // by construction.
  const rows = occupationMatrixRows(refCells).filter((r) => !possessedSocs || possessedSocs.has(r.id));
  // Priority-default: in-demand occupations lead, the rest collapse behind the
  // expander. in_demand is member-independent (it rides every cell), so the
  // reference cells carry the verdict; each group stays demand-sorted.
  const inDemand = new Set(refCells.filter((c) => c.in_demand).map((c) => c.soc_code));
  const priorityRows = rows.filter((r) => inDemand.has(r.id));
  const restRows = rows.filter((r) => !inDemand.has(r.id));
  const orderedRows = [...priorityRows, ...restRows];
  // Split only when the instance curates (criteria present) AND there's a real rest
  // to collapse — a consortium's effective set is entirely in-demand, so no split.
  const dc = land.demand_criteria;
  const occSplit = dc && priorityRows.length > 0 && restRows.length > 0
    ? {
        after: priorityRows.length,
        restLabel: "below the priority bar",
        criteria: [
          ...(dc.min_openings != null ? [`> ${dc.min_openings.toLocaleString("en-US")} openings`] : []),
          ...(dc.min_wage != null ? [`≥ $${Math.round(dc.min_wage / 1000)}k median`] : []),
        ],
      }
    : null;
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

  // Panels as manifest entries — author-qualified ids are the layout lab's
  // weight keys (a panel keeps its weight across scope recomposition).
  const demandPanel = {
    id: "occupations.demand",
    minWidth: 340,
    // Fill treemap, no intrinsic height — a solo row needs the target.
    height: 400,
    node: (
      <DashPanel title="Regional Demand" authority="COE" accent={scopeBrand}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <TotalStrip label="Total regional demand" value={totalDemand} accent={scopeBrand} />
          {/* Ring tracks the entity in BOTH scopes — the SOC's share of
              regional demand is scope-invariant (demand is regional). Scope is
              carried by hue (the ramp wears scopeBrand) and the banner. */}
          <DemandTreemap cells={shownDemandCells} total={land.aggregate.regional_demand_total} selected={soc} onSelect={selectConsortium} accent={scopeBrand} fill />
        </div>
      </DashPanel>
    ),
  };
  const coveragePanel = {
    id: "occupations.coverage",
    // Coverage leads the top band at 2:1 over the demand treemap — decided in
    // the layout lab (2026-06-06), mirroring the Programs lens.
    weight: 2,
    minWidth: 592, // matrix inner min (262 label + 5×62 cells) + panel chrome
    node: (
      <DashPanel title="Occupation Coverage" authority="DataMart" accent={scopeBrand}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <CoverageMatrix
            flush
            cols={cols}
            rows={orderedRows}
            split={occSplit}
            level={(r, c) => level(cellOf(r, c))}
            selectedRow={soc}
            selectedCol={collegeId}
            cornerLabel={OCC_MATRIX_CORNER}
            gapCellHint="no awards or enrollment here"
            legend={[
              { k: "Covered", sub: "awards + enrollment", bg: "rgba(148,168,201,.92)", ring: true },
              { k: "Partial", sub: "missing awards or enrollment", bg: "rgba(148,168,201,.3)", ring: true },
              { k: "Gap", sub: "no awards or enrollment", bg: "rgba(255,255,255,.035)", ring: false },
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
        name={socTitle}
        code={soc ? `SOC ${soc}` : ""}
      />
      {/* One band set per lens: top band (demand hero + coverage), then the
          scope bands — consortium: summary+gap · awards vs demand, then
          enrollments · crosswalk; college: awards · enrollments (no wages,
          no demand line — see header). The set is the layout lab's swap
          boundary. */}
      <DashBandSet bands={[
        ...(wide
          ? [{ id: "occupations.coverageRow", panels: [coveragePanel] }, { id: "occupations.demandRow", panels: [demandPanel] }]
          : [{ id: "occupations.top", panels: [coveragePanel, demandPanel] }]),
        ...buildScopeBands(),
      ]} />
    </div>
  );

  // Hoisted so the return stays a readable manifest; closes over the scope
  // state above.
  function buildScopeBands(): DashBandDef[] {
    const summaryPanel = {
      id: "occupations.summary",
      minWidth: 340,
      // Carries the old scopeA band height (regional facts quartet).
      height: 445,
      node: (
        // Scope-keyed chrome (the report's reportBrand behavior): lens red at
        // consortium, the college's brand in college scope.
        <DashPanel title="Occupation Summary" authority="COE" accent={scopeBrand}>
          <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
            <OccupationSummary report={report} />
          </div>
        </DashPanel>
      ),
    };
    const awardsPanel = {
      id: "occupations.awards",
      minWidth: 360,
      height: 508, // the old scopeB band height, kept when stacked solo
      node: (
        <DashPanel title="Awards" authority={collegeName ? "DataMart" : "DataMart · COE"} accent={scopeBrand}>
          <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
            {collegeName ? (
              cellPrograms.length > 0 ? (
                <TrendChart
                  key={collegeId + ":awards"}
                  series={cellPrograms.map((p) => ({ top6: p.top6, name: p.name, vals: p.awards ?? [] }))}
                  labels={land!.award_years.map(awardYearLabel)}
                  defaultMode="stacked"
                  colorOf={programColor}
                  empty={!cellPrograms.some((p) => (p.awards ?? []).some((v) => v > 0))}
                  fill
                />
              ) : (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 10.5 }}>no program activity here</div>
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
                  fill
                />
              )
            )}
          </div>
        </DashPanel>
      ),
    };
    const enrollPanel = {
      id: "occupations.enrollments",
      minWidth: 360,
      height: 508,
      node: (
        <DashPanel title="Enrollments" authority="DataMart" accent={scopeBrand}>
          <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
            {collegeName ? (
              cellPrograms.length > 0 ? (
                <TrendChart
                  key={collegeId + ":enroll"}
                  series={cellPrograms.map((p) => ({ top6: p.top6, name: p.name, vals: p.enrollment ?? [] }))}
                  labels={land!.enrollment_terms}
                  defaultMode="lines"
                  colorOf={programColor}
                  axisStyle="twoTier"
                  empty={!cellPrograms.some((p) => (p.enrollment ?? []).some((v) => v != null && v > 0))}
                  fill
                />
              ) : (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#5e6a83", fontFamily: MONO, fontSize: 10.5 }}>no program activity here</div>
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
                  fill
                />
              )
            )}
          </div>
        </DashPanel>
      ),
    };
    // Coverage drives the band set: with no feeding-program activity in
    // scope, the trend band would be two empty ghosts — the gap view IS the
    // content (summary + unlit crosswalk), mirroring the report's 0-of-N gap
    // view. While the report loads, hold the full layout steady.
    const hasActivity = report == null
      ? true
      : collegeName
        ? cellPrograms.length > 0
        : report.awards_by_college.length > 0 || report.enrollment_by_college.length > 0;
    const hasCrosswalk = !!(report?.crosswalk && report.crosswalk.tops.length > 0);
    // In the gap view the consortium-taught highlighting would mislead (a lit
    // TOP says "taught" — but not in this scope), so the pathway renders
    // unlit: the structural map of how curriculum COULD reach this SOC.
    const displayCrosswalk = !report?.crosswalk || hasActivity
      ? report?.crosswalk
      : {
          ...report.crosswalk,
          n_taught: 0,
          coverage_pct: 0,
          tops: report.crosswalk.tops.map((t) => ({ ...t, taught_at_college: false })),
          cips: report.crosswalk.cips.map((c) => ({ ...c, active: false })),
        };
    const crosswalkPanel = hasCrosswalk && report && displayCrosswalk
      ? {
          id: "occupations.crosswalk",
          minWidth: 520, // pathway diagram pans below dashLayout.PATHWAY_MIN_RENDER_W
          height: 445,
          node: (
            <DashPanel title="Crosswalk" authority="CCCCO · NCES" accent={scopeBrand}>
              {/* Centered: the diagram's height is width-driven, so in a fixed
                  row it floats — centering splits the slack symmetrically.
                  Scope-keyed brand, like the per-college report's pathway. */}
              <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", justifyContent: "center" }}>
                <CurriculumPathway crosswalk={displayCrosswalk} collegeName="SVAMP member colleges" socCode={report.soc_code} socTitle={report.title} brandColor={scopeBrand} embedded prose={false} />
              </div>
            </DashPanel>
          ),
        }
      : null;
    // No flat "Feeding Programs" list (removed 2026-06-06): the crosswalk
    // carries the TOP→SOC structure visually, and college scope decomposes
    // awards per feeding program — the list restated both, uglier.
    //
    // Rows decided in the layout lab (2026-06-06, rev 2) and IDENTICAL in
    // both scopes (decided rev 3): the summary quartet leads with the
    // crosswalk beside it at 445px — SOC-level regional facts that don't
    // change with scope — then the two trend charts pair beneath at 508px
    // (minmax clamps up if content runs tall). All panel chrome is
    // scope-keyed (scopeBrand), matching the report.
    const rows: DashBandDef[] = [
      { id: "occupations.scopeA", panels: [summaryPanel, crosswalkPanel] },
    ];
    // The trend band exists only where there is activity to chart.
    if (hasActivity) rows.push({ id: "occupations.scopeB", panels: [awardsPanel, enrollPanel] });
    return rows;
  }
}
