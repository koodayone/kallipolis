"use client";

import { useMemo, useState, useEffect, useRef } from "react";
import { squarify } from "@/college-atlas/partnerships/treemap";
import { SchoolConfig } from "@/config/schoolConfig";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import { FONT, MONO, ReportHeader, Section, Prose } from "@/college-atlas/partnerships/reportChrome";
import { OpportunityReportBody, PartnerEmployerRow } from "@/college-atlas/partnerships/OpportunityReport";
import { readSvampParams, writeSvampParams } from "@/college-atlas/partnerships/svampUrl";
import OccupationDemandTable from "@/college-atlas/partnerships/OccupationDemandTable";
import SupplyTreemap from "@/college-atlas/partnerships/SupplyTreemap";
import DepartmentRow from "@/college-atlas/courses/DepartmentRow";
import ProgramPathway from "@/college-atlas/partnerships/ProgramPathway";
import CoverageMatrix from "@/college-atlas/partnerships/CoverageMatrix";
import CurriculumPathway from "@/college-atlas/partnerships/CurriculumPathway";
import OccupationRow, { type OccupationData, type OccupationDetail } from "@/college-atlas/occupations/OccupationRow";
import EmployerMap, { type MapCollege } from "@/college-atlas/partnerships/EmployerMap";
import { getSvampLandscape, getSvampPrograms, getSvampProgram, getSvampOccupation, getSvampEmployers } from "@/college-atlas/partnerships/api";
import type {
  ApiSvampLandscape,
  ApiSvampCell,
  ApiSvampCollege,
  ApiSvampProgram,
  ApiSvampProgramsLandscape,
  ApiSvampProgramReport,
  ApiSvampOccupationReport,
  ApiSvampEmployersResult,
} from "@/college-atlas/partnerships/api";
import TrendChart from "@/college-atlas/partnerships/TrendChart";
import WageOutcomes from "@/college-atlas/partnerships/WageOutcomes";
import DemandTreemap from "@/college-atlas/partnerships/DemandTreemap";
import {
  Dot, shortName, hexA, hexToHsl, hueDist, OVERLAY_COLORS, leadOverlayColors,
  awardYearLabel, shortAwardType, shortCreditType,
} from "@/college-atlas/partnerships/chartKit";

const GAP = "#e0654f";
// SVAMP consortium accent (red) — cube, eyebrow, hairline, section bars.
const ACCENT = "#ff5a5a";
// Demand reference-line hue — gold (OVERLAY_COLORS' lead hue), distinct from
// every member-college brand and calmer than the occupations-lens red, which
// read as an alarm rather than a benchmark on the awards chart.
const DEMAND_ACCENT = "#c9a84c";
const PROGRAM_ACCENT = "#50c878"; // Programs lens primary — green (vs occupations red)
const EMPLOYER_ACCENT = "#5a9bd4"; // Employers lens primary — blue
// SVAMP scopes its program/supply universe to TOP division 09 (Engineering &
// Industrial Technologies) — the consortium's domain. The backend enforces it
// for the grid + Programs lens; this scopes the occupation drill report's
// curriculum pathway to match (mirrors backend svamp.SVAMP_TOP_DIVISION).
const SVAMP_TOP_DIVISION = "09";
// Programs the SVAMP director's AM mandate excludes despite sitting in
// division 09 — their employment flows run to other industry verticals
// (automotive → dealerships/fleets; HVAC → building trades). Mirrors backend
// svamp.SVAMP_MANDATE_EXCLUDED_TOPS; threaded to the embedded cell report so
// its curriculum pathway scopes identically to the rest of the lens.
const SVAMP_MANDATE_EXCLUDED_TOPS = ["094600", "094800"];

type CollegeRef = { id: string; config: SchoolConfig };

type Props = {
  colleges: CollegeRef[]; // member colleges, in display order
  onBack: () => void;
};

// Plain-English role labels for the 12 SVAMP occupations. The role name leads;
// the SOC code rides beneath as provenance. No invented grouping — the twelve
// roles list in SOC order.
const ROLE_LABEL: Record<string, string> = {
  "17-3023": "Electrical & Electronic Eng. Techs",
  "17-3024": "Electro-Mech. & Mechatronics Techs",
  "17-3026": "Industrial Eng. Techs",
  "17-3027": "Mechanical Eng. Techs",
  "17-3028": "Calibration Techs",
  "17-3029": "Eng. Technologists, other",
  "49-9041": "Industrial Machinery Mechanics",
  "49-9043": "Machinery Maintenance Workers",
  "51-4041": "Machinists",
  "51-9141": "Semiconductor Processing",
  "51-9161": "CNC Tool Operators",
  "51-9162": "CNC Tool Programmers",
};

// Coverage keys on activity over the crosswalking programs — the identical
// predicate to the Programs grid, just aggregated over the feeding set: covered
// = enrolled & awarded; partial = one signal but not both; gap = neither.
// course_count (catalog) no longer gates — a SOC fed by a program that awards
// credentials without a tagged course (095630 → Machinists) reads partial, not
// gap, so the missing-enrollment seam stays visible rather than masked covered.
function level(cell: ApiSvampCell | undefined): "none" | "partial" | "strong" {
  if (!cell) return "none";
  const enrolled = cell.enrolled;
  const awarded = cell.feeding_awards > 0;
  if (enrolled && awarded) return "strong";
  return enrolled || awarded ? "partial" : "none";
}

// ── Lens navigation ────────────────────────────────────────────────────────
// Three Platonic forms of the partnership landscape: the worker (occupations ·
// hard hat), the curriculum (programs · book), the firm (employers · skyscraper).
// One geometric family of reduced archetypes; the per-lens accent doubles as
// wayfinding once the Programs/Employers views ship. Eyebrow-tab treatment —
// active underline echoes the coverage grid's selected-column underline.
type Lens = "occupations" | "programs" | "employers";
const FormHardHat: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M6 18a10 10 0 0 1 20 0" /><path d="M11.4 18C11.4 12.4 13 9.4 16 8" /><path d="M20.6 18C20.6 12.4 19 9.4 16 8" /><path d="M3 18h26" /><path d="M5.4 18c2.4 3.1 18.8 3.1 21.2 0" />
  </svg>
);
const FormBook: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M16 9.6C12.4 7.8 7.6 8.1 4.6 9.6V22.6C7.6 21.1 12.4 20.8 16 22.6" /><path d="M16 9.6C19.6 7.8 24.4 8.1 27.4 9.6V22.6C24.4 21.1 19.6 20.8 16 22.6" /><path d="M16 9.6V22.6" />
  </svg>
);
const FormTower: React.FC = () => (
  <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" style={{ width: "100%", height: "100%" }}>
    <path d="M10.5 28V11h11v17" /><path d="M13.6 11V6h4.8v5" /><path d="M16 6V3" /><path d="M13.2 15.5h5.6M13.2 19.5h5.6M13.2 23.5h5.6" /><path d="M7.5 28h17" />
  </svg>
);
// Programs first — workforce practitioners own and act on programs (supply is
// their lever; SWP funds programs), and it matches the institution-primary atlas.
// Occupations (regional demand) follows as the justification; employers, the map.
const LENS_DEFS: { key: Lens; label: string; accent: string; Icon: React.FC }[] = [
  { key: "programs", label: "Programs", accent: PROGRAM_ACCENT, Icon: FormBook },
  { key: "occupations", label: "Occupations", accent: "#ff5a5a", Icon: FormHardHat },
  { key: "employers", label: "Employers", accent: EMPLOYER_ACCENT, Icon: FormTower },
];
function LensTabs({ lens, setLens }: { lens: Lens; setLens: (l: Lens) => void }) {
  return (
    <div style={{ display: "flex", gap: 38, borderBottom: "1px solid rgba(255,255,255,.08)", marginBottom: 4 }}>
      {LENS_DEFS.map(({ key, label, accent, Icon }) => {
        const on = lens === key;
        return (
          <button
            key={key}
            onClick={() => setLens(key)}
            onMouseEnter={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#e8ecf4"; }}
            onMouseLeave={(e) => { if (!on) (e.currentTarget as HTMLElement).style.color = "#9aa6bd"; }}
            style={{ display: "flex", alignItems: "center", gap: 9, border: 0, background: "transparent", cursor: "pointer", padding: "6px 0 13px", color: on ? "#e8ecf4" : "#9aa6bd", fontFamily: MONO, fontSize: 11.5, fontWeight: 500, letterSpacing: ".12em", textTransform: "uppercase", position: "relative", transition: "color .16s" }}
          >
            <span style={{ width: 17, height: 17, display: "flex", color: on ? accent : "#5e6a83", transition: "color .16s" }}><Icon /></span>
            {label}
            {on && <span style={{ position: "absolute", left: 0, right: 0, bottom: -1, height: 2, background: accent, borderRadius: 2 }} />}
          </button>
        );
      })}
    </div>
  );
}
// Member-college coordinates (fixed; the five SVAMP colleges) for the map's
// context anchors. Hardcoded rather than imported from the State Atlas to keep
// college-atlas free of a cross-feature dependency on state-atlas.
const SVAMP_COLLEGE_GEO: Record<string, [number, number]> = {
  "De Anza College": [37.31, -122.04],
  "Foothill College": [37.36, -122.05],
  "Evergreen Valley College": [37.34, -121.80],
  "Mission College": [37.39, -121.98],
  "Ohlone College": [37.53, -121.91],
};

// ── Employers lens — the regional employer map: Bay-Area advanced manufacturing
// employers hiring for the SVAMP occupations, in the State Atlas's map language,
// with the member colleges anchored for context. Click an employer for detail.
function EmployersLens({ colleges }: { colleges: CollegeRef[] }) {
  const [data, setData] = useState<ApiSvampEmployersResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);   // synced map ↔ list
  const [query, setQuery] = useState("");
  const [narrow, setNarrow] = useState(false);
  // URL anchoring (employers slice: emp); eReady gates writes until restore.
  const [eReady, setEReady] = useState(false);
  const rowRefs = useRef<Map<string, HTMLButtonElement | null>>(new Map());

  useEffect(() => {
    let alive = true;
    getSvampEmployers().then((d) => { if (alive) setData(d); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, []);

  // Restore the employers slice from the URL on mount, then sync emp → URL.
  useEffect(() => {
    const p = readSvampParams();
    if (p.emp) setSelected(p.emp);
    setEReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (!eReady) return;
    writeSvampParams({ emp: selected ?? null });
  }, [eReady, selected]);
  useEffect(() => {
    const f = () => setNarrow(window.innerWidth < 760);
    f(); window.addEventListener("resize", f);
    return () => window.removeEventListener("resize", f);
  }, []);
  // Scroll the selected row into view — matters when the selection arrives from
  // a map-marker click (the row may be off the list's current scroll).
  useEffect(() => {
    if (selected) rowRefs.current.get(selected)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selected]);

  const anchors: MapCollege[] = useMemo(
    () => colleges.flatMap((c) => {
      const geo = SVAMP_COLLEGE_GEO[c.config.name];
      // Full "… College" name on the map label, matching the State Atlas.
      return geo ? [{ name: c.config.name, lat: geo[0], lng: geo[1], brand: c.config.brandColorLight }] : [];
    }),
    [colleges],
  );

  if (err) return <div style={{ padding: "60px 0", color: GAP, fontFamily: MONO, fontSize: 13 }}>Failed to load employers: {err}</div>;
  if (!data) return <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}><RisingSun style={{ width: 90, height: "auto", opacity: 0.4 }} /></div>;

  const q = query.trim().toLowerCase();
  // Display the list alphabetically — a searchable directory reads A→Z; the
  // backend's breadth ranking ("top employer") drives the map, not list order.
  const filtered = (q ? data.employers.filter((e) => e.name.toLowerCase().includes(q)) : data.employers)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name));
  const toggle = (n: string | null) => setSelected((cur) => (n === null ? null : cur === n ? null : n));

  return (
    <Section title="Regional Employer Map" brandColor={EMPLOYER_ACCENT}>
      <Prose>
        Top {data.region_display} advanced manufacturing employers hiring for the twelve SVAMP target occupations. Member colleges are marked to show geographic context; select an employer for detail.
      </Prose>
      <div style={{ display: "flex", flexDirection: narrow ? "column" : "row", gap: 16, marginTop: 16, height: narrow ? "auto" : 560 }}>
        {/* LEFT — map */}
        <div style={{ flex: "1 1 0", minWidth: 0, minHeight: 0, height: narrow ? 420 : "100%" }}>
          <EmployerMap
            employers={data.employers}
            colleges={anchors}
            selected={selected}
            hover={hover}
            onSelect={toggle}
            onHover={setHover}
          />
        </div>

        {/* RIGHT — search + employer list (inline-expand detail) */}
        <div style={{ flex: "1 1 0", minWidth: 0, minHeight: 0, height: narrow ? 420 : "100%", display: "flex", flexDirection: "column", border: "1px solid rgba(255,255,255,0.09)", borderRadius: 12, background: "rgba(0,0,0,0.18)", overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderBottom: "1px solid rgba(255,255,255,0.07)", flexShrink: 0 }}>
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
              <circle cx="7" cy="7" r="5" stroke="rgba(255,255,255,0.8)" strokeWidth="1.3" />
              <path d="M11 11l3.5 3.5" stroke="rgba(255,255,255,0.8)" strokeWidth="1.3" strokeLinecap="round" />
            </svg>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search employers…"
              style={{ flex: 1, background: "none", border: "none", outline: "none", color: "#e8ecf4", fontFamily: FONT, fontSize: 13.5 }}
            />
          </div>
          <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
            {filtered.map((e) => {
              const isSel = selected === e.name, isHov = hover === e.name;
              return (
                <button
                  key={e.name}
                  ref={(el) => { rowRefs.current.set(e.name, el); }}
                  onClick={() => toggle(e.name)}
                  onMouseEnter={() => setHover(e.name)}
                  onMouseLeave={() => setHover(null)}
                  style={{ display: "flex", alignItems: "stretch", gap: 12, width: "100%", textAlign: "left", padding: "12px 14px", border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)", cursor: "pointer", background: isSel ? hexA(EMPLOYER_ACCENT, 0.1) : isHov ? "rgba(255,255,255,0.04)" : "transparent", transition: "background .12s" }}
                >
                  <div style={{ width: 3, borderRadius: 2, background: EMPLOYER_ACCENT, opacity: isSel ? 1 : 0.7, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: FONT, fontSize: 13.5, fontWeight: 600, color: "#ffffff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{e.name}</div>
                    {/* NAICS code (formal identifier, mono) → industry title
                        (the concept, brighter sans). The pairing teaches the
                        crosswalk; truncates collapsed, wraps full when selected. */}
                    <div style={{ fontSize: 11, marginTop: 3, lineHeight: 1.45, whiteSpace: isSel ? "normal" : "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {e.naics4 && <span style={{ fontFamily: MONO, color: "rgba(255,255,255,0.4)" }}>NAICS {e.naics4}</span>}
                      {e.naics4 && e.naics_title && <span style={{ color: "rgba(255,255,255,0.28)" }}> · </span>}
                      {e.naics_title && <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.62)" }}>{e.naics_title}</span>}
                    </div>
                    {isSel && (
                      <div style={{ marginTop: 10 }}>
                        {e.website && (
                          <a href={e.website} target="_blank" rel="noreferrer" onClick={(ev) => ev.stopPropagation()} style={{ fontFamily: MONO, fontSize: 11, color: EMPLOYER_ACCENT }}>
                            {e.website.replace(/^https?:\/\//, "").replace(/\/$/, "")} ↗
                          </a>
                        )}
                        {e.description && (
                          <div style={{ fontFamily: FONT, fontSize: 12.5, color: "rgba(255,255,255,0.7)", lineHeight: 1.55, marginTop: e.website ? 7 : 0, whiteSpace: "normal" }}>{e.description}</div>
                        )}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 9 }}>
                          {e.socs.map((s) => (
                            <span key={s} style={{ fontFamily: FONT, fontSize: 11, color: "#cfe0f0", background: hexA(EMPLOYER_ACCENT, 0.14), border: `1px solid ${hexA(EMPLOYER_ACCENT, 0.3)}`, borderRadius: 6, padding: "2px 8px" }}>
                              {ROLE_LABEL[s] ?? s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
            {filtered.length === 0 && (
              <div style={{ padding: "24px 16px", fontFamily: FONT, fontSize: 13, color: "#9aa6bd" }}>No employers match “{query}”.</div>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}

// ── Programs lens — supply-side, TOP6-centric (the dual of the occupation
// lens). Supply treemap (picker) → TOP report. Lives here so it can reuse the
// in-module TrendChart / WageOutcomes; series are keyed on colleges (brand-
// colored) rather than programs. Demand is shown per SOC, never summed.
function ProgramsLens({ colleges }: { colleges: CollegeRef[] }) {
  // Programs lens is green; shadow the module red within this view so every
  // section bar / header / treemap usage flips at once.
  const ACCENT = PROGRAM_ACCENT;
  const [land, setLand] = useState<ApiSvampProgramsLandscape | null>(null);
  const [top, setTop] = useState<string | null>(null);
  // null ⇒ aggregated (consortium) view; a college id ⇒ targeted (college, TOP).
  const [matrixCollegeId, setMatrixCollegeId] = useState<string | null>(null);
  const [report, setReport] = useState<ApiSvampProgramReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  // URL anchoring (programs slice: top + pc); pReady gates writes until restore.
  const [pReady, setPReady] = useState(false);

  const nameById = useMemo(() => new Map(colleges.map((c) => [c.id, c.config.name])), [colleges]);
  const matrixCollegeName = matrixCollegeId ? nameById.get(matrixCollegeId) : undefined;

  useEffect(() => {
    getSvampPrograms()
      .then((d) => { setLand(d); setTop((cur) => cur ?? d.tops[0]?.top6 ?? null); })
      .catch((e) => setErr(e.message));
  }, []);
  useEffect(() => {
    if (!top) return;
    let alive = true;
    getSvampProgram(top, matrixCollegeName).then((r) => { if (alive) setReport(r); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, [top, matrixCollegeName]);

  // Restore the programs slice from the URL on mount; the data-load default
  // (setTop's `cur ?? …`) defers to a URL-pinned TOP. Then sync top + college →
  // URL. `college` is shared with the occupations lens but only ever written by
  // the active lens, so there's no cross-lens clobber (see svampUrl.ts).
  useEffect(() => {
    const p = readSvampParams();
    if (p.top) setTop(p.top);
    if (p.college) setMatrixCollegeId(p.college);
    setPReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (!pReady) return;
    writeSvampParams({ top: top ?? null, college: matrixCollegeId ?? null });
  }, [pReady, top, matrixCollegeId]);

  const brandByName = useMemo(
    () => new Map(colleges.map((c) => [c.config.name, c.config.brandColorLight])),
    [colleges],
  );
  const colorOf = (name: string) => brandByName.get(name) ?? ACCENT;

  // Sticky context banner — pinned under the nav once the program report scrolls
  // away (mirrors the occupations lens). Observer keyed on `report` so it
  // re-attaches to the sentinel whenever a new program loads.
  const [ctxShow, setCtxShow] = useState(false);
  const ctxSentinel = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = ctxSentinel.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => setCtxShow(e.boundingClientRect.top < 72),
      { rootMargin: "-72px 0px 0px 0px", threshold: 0 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [report]);

  if (err) return <div style={{ padding: "60px 0", color: GAP, fontFamily: MONO, fontSize: 13 }}>Failed to load programs: {err}</div>;
  if (!land) return <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}><RisingSun style={{ width: 90, height: "auto", opacity: 0.4 }} /></div>;

  const awardingPrograms = land.tops.filter((t) => t.awards_total > 0).length;
  const totalAwards = land.tops.reduce((s, t) => s + t.awards_total, 0);
  const wageWindow = report?.wages.find((w) => w.window)?.window ?? "";

  // Coverage-matrix inputs (dual of the occupations grid): cols = member
  // colleges, rows = the active programs (enrollment OR awards somewhere),
  // ranked by awards. A program earns a row by activity, not by having a course
  // tagged to its own code — so 095630 (confers, parent-code courses) and 095200
  // (enrolls, no awards yet) appear. level() reads the coverage payload.
  const progCols = colleges.map((c) => ({ id: c.id, label: shortName(c.config.name), brand: c.config.brandColorLight }));
  const matrixCellByKey = new Map((land.matrix?.cells ?? []).map((c) => [c.college + "|" + c.top6, c]));
  const progRows = land.tops
    .filter((t) => t.enrollment_total > 0 || t.awards_total > 0)
    .map((t) => ({ id: t.top6, label: t.name, sublabel: `TOP ${t.top6}`, title: t.name }));
  // Coverage keys on activity: covered = enrolled & awarded (full pipeline);
  // partial = one signal but not both; gap = this college does neither here.
  const progLevel = (rowId: string, colId: string): "none" | "partial" | "strong" => {
    const name = nameById.get(colId);
    const cell = name ? matrixCellByKey.get(name + "|" + rowId) : undefined;
    if (!cell) return "none";
    const enrolled = cell.enrolled;
    const awarded = cell.awards > 0;
    if (enrolled && awarded) return "strong";
    return enrolled || awarded ? "partial" : "none";
  };
  const targetedCollege = report?.college ?? null;
  // Option A: the per-program report re-brands to the targeted college; the
  // aggregate (consortium) view keeps the green lens accent.
  const reportBrand = targetedCollege ? colorOf(targetedCollege) : ACCENT;
  // Targeted view: decompose that college's awards by credential type (the
  // "what kind of credential does this school confer" read). The consortium
  // view keeps the by-college stack — five schools × N types is too many bands.
  const typeSeries = targetedCollege
    ? (report?.awards_by_type ?? []).filter((s) => s.college === targetedCollege)
    : [];
  // Both decompositions color by the lead/overlay idiom: dominant series takes
  // the school brand, the rest stay hue-distinct (leadOverlayColors).
  const typeColor = leadOverlayColors(typeSeries.map((s) => ({ key: s.award_type, vals: s.vals })), reportBrand);
  // Targeted view: decompose that college's enrollment by credit family — the
  // flat line is ALL instructional activity (credit + noncredit), so the split
  // is the integrity guarantee that the blend is always one click from its
  // parts (credit and noncredit headcounts are different kinds of number).
  const creditSeries = targetedCollege
    ? (report?.enrollment_by_credit ?? []).filter((s) => s.college === targetedCollege)
    : [];
  const creditColor = leadOverlayColors(creditSeries.map((s) => ({ key: s.credit_type, vals: s.vals })), reportBrand);
  // Regional addressable demand — Σ annual openings across the SOCs this
  // program feeds (COE), the per-completer opportunity set. A clean sum
  // WITHIN a program (its fed SOCs are distinct); NEVER summed across
  // programs (SOCs are shared — that would double-count). Consortium view
  // only: one college's awards against the whole regional pool would be a
  // partial-vs-whole mismatch, and no label survives that misreading. The
  // "Occupations Served" table above the chart is this number's decomposition.
  const addressableDemand = (report?.occupations ?? []).reduce((t, o) => t + (o.annual_openings ?? 0), 0);

  return (
    <>
      {/* Sticky context banner — scope · program name · TOP code, pinned under
          the nav once the report scrolls away. Mirrors the occupations banner:
          scope leads (Consortium, or the targeted college in its brand). */}
      {report && (
        <div
          style={{
            position: "fixed", top: 72, left: 0, right: 0, zIndex: 25, height: 46,
            background: "rgba(6,13,31,0.92)", backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            display: "flex", alignItems: "center",
            opacity: ctxShow ? 1 : 0,
            transform: ctxShow ? "translateY(0)" : "translateY(-8px)",
            pointerEvents: ctxShow ? "auto" : "none",
            transition: "opacity .22s ease, transform .22s ease",
          }}
        >
          <div style={{ maxWidth: 900, width: "100%", margin: "0 auto", padding: "0 28px", display: "flex", alignItems: "baseline", gap: 10, minWidth: 0 }}>
            <span style={{ fontFamily: FONT, fontSize: 11.5, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase", color: reportBrand, flex: "none", whiteSpace: "nowrap" }}>
              {targetedCollege ?? "Consortium"}
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)", flex: "none" }}>·</span>
            <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.9)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {report.name}
            </span>
            <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.05em", color: hexA(reportBrand, 0.65), flex: "none", whiteSpace: "nowrap" }}>
              TOP {report.top6}
            </span>
          </div>
        </div>
      )}
      <Section title="Consortium Program Supply" brandColor={ACCENT}>
        <Prose>
          This view examines the consortium supply landscape across advanced manufacturing programs in TOP division 09 supporting the Silicon Valley Advanced Manufacturing Partnership. In the latest reported year{land.latest_award_year ? ` (${land.latest_award_year})` : ""}, {awardingPrograms} of them awarded {totalAwards.toLocaleString()} credentials, preparing students for the 12 advanced manufacturing occupations via the TOP-CIP-SOC crosswalk.
        </Prose>
        <SupplyTreemap tops={land.tops} selectedTop={matrixCollegeId ? null : top} onSelect={(t) => { setTop(t); setMatrixCollegeId(null); }} accent={ACCENT} caption="Area is latest-year credentials awarded — click a program for the consortium view." />
        <CoverageMatrix
          cols={progCols}
          rows={progRows}
          level={progLevel}
          selectedRow={top}
          selectedCol={matrixCollegeId}
          cornerLabel="↓ program (by awards) · → college"
          gapCellHint="no enrollment or awards here"
          legend={[
            { k: "Covered", sub: "enrollment & awards", bg: "rgba(148,168,201,.92)", ring: true },
            { k: "Partial", sub: "enrollment or awards", bg: "rgba(148,168,201,.3)", ring: true },
            { k: "Gap", sub: "neither", bg: "rgba(255,255,255,.035)", ring: false },
          ]}
          caption="Each cell is one college’s coverage — click for that college’s report."
          onSelect={(t, collegeId) => { setTop(t); setMatrixCollegeId(collegeId); }}
          onSelectRow={(t) => { setTop(t); setMatrixCollegeId(null); }}
        />
      </Section>

      {report && (
        <div style={{ marginTop: 30 }}>
          <div ref={ctxSentinel} style={{ height: 1 }} />
          <ReportHeader eyebrow={targetedCollege ?? "Consortium"} title={report.name} accent={reportBrand}>
            <span style={{ color: reportBrand, opacity: 0.7 }}>TOP {report.top6}</span>
            <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{report.occupations.length} Occupations</span>
            <Dot /><span style={{ color: reportBrand, opacity: 0.7, letterSpacing: "0.08em" }}>{report.sector}</span>
          </ReportHeader>

          <Section title="Occupations Served" brandColor={reportBrand}>
            <Prose>
              The occupations this program prepares for, with their regional demand. A program can support several occupations through the crosswalk; demand is shown per occupation.
            </Prose>
            {report.crosswalk && report.crosswalk.socs.length > 0 && (
              <ProgramPathway crosswalk={report.crosswalk} accent={reportBrand} />
            )}
            <div style={{ marginTop: 28 }}>
              <OccupationDemandTable rows={report.occupations} brandColor={reportBrand} label="Occupations this program supports · regional annual openings" />
            </div>
          </Section>

          <Section title="Program Awards" brandColor={reportBrand}>
            <Prose>
              {report.awards_by_college.length === 0
                ? "No awards are reported for this program via CCCCO DataMart."
                : typeSeries.length > 0
                  ? `Credentials awarded per year at ${shortName(targetedCollege ?? "")}, broken out by credential type. Toggle between the stacked total and per-credential trends.`
                  : "Credentials awarded per year across the member colleges. Toggle between the stacked consortium total, per-school trends, or set consortium total against regional addressable demand — the sum of annual openings across occupations this program prepares students for."}
            </Prose>
            <TrendChart
              // Keyed by scope: crossing targeted <-> consortium remounts the
              // chart at its default. Stacked leads (the schools stay the
              // subject; some programs' demand scale flattens the stack to
              // illegibility) — the visible Demand toggle is the invitation
              // to the market-scale read, not the landing.
              key={targetedCollege ?? "consortium"}
              series={typeSeries.length > 0
                ? typeSeries.map((s) => ({ top6: s.award_type, name: shortAwardType(s.award_type), vals: s.vals }))
                : report.awards_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
              labels={report.award_years.map(awardYearLabel)}
              defaultMode="stacked"
              colorOf={typeSeries.length > 0 ? typeColor : colorOf}
              modeLabels={typeSeries.length > 0 ? { lines: "Per credential", stacked: "Stacked" } : { lines: "Per school", stacked: "Stacked", demand: "Demand" }}
              hideSeriesTag
              empty={report.awards_by_college.length === 0}
              demandLine={!targetedCollege && addressableDemand > 0
                ? { value: addressableDemand, label: "Regional Demand · COE", color: DEMAND_ACCENT }
                : undefined}
            />
          </Section>

          <Section title="Program Enrollments" brandColor={reportBrand}>
            <Prose>
              {report.enrollment_by_college.length === 0
                ? "No enrollment is reported for this program via CCCCO DataMart."
                : creditSeries.length > 0
                  ? `Term-by-term enrollment at ${shortName(targetedCollege ?? "")}, broken out by credit family — credit vs. noncredit instruction — excluding the structurally-low summer terms. Toggle between per-family trends and the stacked total; hover a family to focus it.`
                  : "Term-by-term enrollment across the member colleges that run this program, excluding the structurally-low summer terms. Toggle between per-school trends and the combined consortium total; hover a school to focus it."}
            </Prose>
            <TrendChart
              series={creditSeries.length > 0
                ? creditSeries.map((s) => ({ top6: s.credit_type, name: shortCreditType(s.credit_type), vals: s.vals }))
                : report.enrollment_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
              labels={report.enrollment_terms}
              defaultMode="lines"
              colorOf={creditSeries.length > 0 ? creditColor : colorOf}
              axisStyle="twoTier"
              modeLabels={creditSeries.length > 0 ? { lines: "Per credit family", stacked: "Stacked" } : { lines: "Per school", stacked: "Stacked" }}
              hideSeriesTag
              empty={report.enrollment_by_college.length === 0}
            />
          </Section>

          {report.wages.length > 0 && (
            <Section title="Program Wage Outcomes" brandColor={reportBrand}>
              <Prose>
                Median annual earnings for completers of this program at three points relative to award completion — 2 years before, 2 years after, and 5 years after. Derived from statewide data at the program (TOP6) level by credential type{wageWindow ? ` for award years ${wageWindow}` : ""}.
              </Prose>
              <WageOutcomes
                programs={[{ top6: report.top6, name: report.name, awards_recent: 0, awards: [], enrollment: [], wages: report.wages }]}
                brandColor={reportBrand}
              />
            </Section>
          )}

          <Section title="Curriculum Alignment" brandColor={reportBrand}>
            <Prose>
              Explore the courses each member college teaches under TOP {report.top6} · {report.name}.
            </Prose>
            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 2 }}>
              {report.curriculum_by_college.filter((cc) => cc.courses.length > 0).map((cc, i) => (
                <DepartmentRow
                  key={cc.college}
                  department={shortName(cc.college)}
                  courseCount={cc.courses.length}
                  index={i}
                  brandColor={colorOf(cc.college)}
                  courses={cc.courses.map((c) => ({ code: c.code, name: c.name, description: c.description, learningOutcomes: c.learning_outcomes, topCode: c.top_code }))}
                  schoolName={cc.college}
                  hideOccupationPathways
                  socFilter=""
                />
              ))}
            </div>
          </Section>
        </div>
      )}
    </>
  );
}

// ── Occupations lens — aggregated SOC view (the dual of ProgramsLens). One
// occupation read consortium-wide: demand + supply + gap, the SOC-anchored
// crosswalk (taught by any member college), the feeding programs sized by
// awards, and per-college award/enrollment series + curriculum.
function OccupationAggregateReport({ soc, colleges, isSectorPriority }: { soc: string; colleges: CollegeRef[]; isSectorPriority: boolean }) {
  const [report, setReport] = useState<ApiSvampOccupationReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [demandOpen, setDemandOpen] = useState(true);
  useEffect(() => {
    let alive = true;
    setReport(null);
    getSvampOccupation(soc).then((r) => { if (alive) setReport(r); }).catch((e) => setErr(e.message));
    return () => { alive = false; };
  }, [soc]);

  const brandByName = useMemo(() => new Map(colleges.map((c) => [c.config.name, c.config.brandColorLight])), [colleges]);
  const colorOf = (name: string) => brandByName.get(name) ?? ACCENT;

  if (err) return <div style={{ padding: "60px 0", color: GAP, fontFamily: MONO, fontSize: 13 }}>Failed to load occupation: {err}</div>;
  if (!report) return <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}><RisingSun style={{ width: 90, height: "auto", opacity: 0.4 }} /></div>;

  const r = report;
  const cw = r.crosswalk;
  const curriculumColleges = r.curriculum_by_college.filter((c) => c.courses.length > 0);

  // Project the consortium demand into the shared OccupationRow shape — demand
  // is regional, so this is the same occupation record the school-specific view
  // shows. employment/description aren't carried at the consortium grain.
  const occData: OccupationData = {
    title: r.title,
    soc_code: r.soc_code,
    annual_wage: r.annual_wage,
    employment: r.employment,
    growth_rate: r.growth_rate,
    annual_openings: r.annual_openings,
    description: r.description,
  };
  const occDetail: OccupationDetail = {
    soc_code: r.soc_code,
    title: r.title,
    description: r.description,
    aligned_top_groups: [],
    aligned_course_count: 0,
    aligned_program_area_count: 0,
    regions: [{
      region: r.region_display,
      employment: r.employment ?? 0,
      annual_wage: r.annual_wage,
      growth_rate: r.growth_rate,
      annual_openings: r.annual_openings,
    }],
  };

  return (
    <>
      {/* Report header — mirrors the per-college occupation report's idiom, but
          scoped to the consortium (eyebrow "Consortium" rather than a college). */}
      <ReportHeader eyebrow="Consortium" title={r.title} accent={ACCENT}>
        <span style={{ color: ACCENT, opacity: 0.7, fontFamily: MONO }}>SOC {r.soc_code}</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)", letterSpacing: "0.08em" }}>{r.sector}</span>
        {isSectorPriority && (
          <><Dot /><span style={{ color: ACCENT, letterSpacing: "0.1em", fontWeight: 600 }}>Regional Priority Sector</span></>
        )}
      </ReportHeader>
      {/* Occupation Summary — mirrors the school-specific view: framing prose,
          the open occupation demand accordion (the same OccupationRow), then the
          consortium crosswalk pathway. */}
      <Section title="Occupation Summary" brandColor={ACCENT}>
        <Prose>{r.occupational_demand}</Prose>
        <div style={{ marginTop: 16 }}>
          <OccupationRow
            occ={occData}
            index={0}
            brandColor={ACCENT}
            isOpen={demandOpen}
            onToggle={() => setDemandOpen((o) => !o)}
            detail={occDetail}
            regionNames={[r.region_display]}
            collegeName="SVAMP member colleges"
            hideCurriculumAlignment
          />
        </div>
        {cw && cw.tops.length > 0 && (
          <CurriculumPathway crosswalk={cw} collegeName="SVAMP member colleges" socCode={r.soc_code} socTitle={r.title} brandColor={ACCENT} embedded />
        )}
      </Section>

      {/* No supply treemap here by design — one treemap per lens, as its hero
          (demand heads this lens; supply heads the Programs lens). The feeding
          TOPs are named by the crosswalk pathway above; their combined supply
          trend is the charts below. */}

      {/* Awards + enrollment hold a chart panel whenever the occupation has
          supporting programs — populated trend, or the ghost scaffold when a
          metric is unreported (e.g. machining: awards but no enrollment). */}
      {r.feeding_tops.length > 0 && (
        <Section title="Program Awards" brandColor={ACCENT}>
          <Prose>
            {r.awards_by_college.length > 0
              ? "Credentials awarded per year by the supporting programs, each counted in full, across the member colleges. Toggle between the stacked consortium total, per-school trends, or set consortium total against regional demand — the annual openings for this occupation."
              : "No awards are reported for the supporting programs via CCCCO DataMart."}
          </Prose>
          {/* Demand here is the dual of the Programs-lens demand view: there,
              honest supply (one program) vs aggregated (addressable) demand —
              the opportunity ceiling; here, aggregated supply (every feeding
              program counted in full toward this SOC) vs the single occupation's
              counted-once openings — the shortage floor. A gap that survives
              this most generous supply accounting is a fortiori. */}
          <TrendChart
            series={r.awards_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
            labels={r.award_years.map(awardYearLabel)}
            defaultMode="stacked"
            colorOf={colorOf}
            modeLabels={{ lines: "Per school", stacked: "Stacked", demand: "Demand" }}
            hideSeriesTag
            empty={r.awards_by_college.length === 0}
            demandLine={(r.annual_openings ?? 0) > 0
              ? { value: r.annual_openings as number, label: "Regional Demand · COE", color: DEMAND_ACCENT }
              : undefined}
          />
        </Section>
      )}

      {r.feeding_tops.length > 0 && (
        <Section title="Program Enrollments" brandColor={ACCENT}>
          <Prose>
            {r.enrollment_by_college.length > 0
              ? "Term-by-term enrollment in the supporting programs across the member colleges, excluding the structurally-low summer terms."
              : "No enrollment is reported for the supporting programs via CCCCO DataMart."}
          </Prose>
          <TrendChart
            series={r.enrollment_by_college.map((s) => ({ top6: s.college, name: shortName(s.college), vals: s.vals }))}
            labels={r.enrollment_terms}
            defaultMode="lines"
            colorOf={colorOf}
            axisStyle="twoTier"
            modeLabels={{ lines: "Per school", stacked: "Stacked" }}
            hideSeriesTag
            empty={r.enrollment_by_college.length === 0}
          />
        </Section>
      )}

      {curriculumColleges.length > 0 && (
        <Section title="Curriculum Alignment" brandColor={ACCENT}>
          <Prose>The courses supporting this occupation at each member college that teaches them.</Prose>
          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 2 }}>
            {curriculumColleges.map((cc, i) => (
              <DepartmentRow
                key={cc.college}
                department={shortName(cc.college)}
                courseCount={cc.courses.length}
                index={i}
                brandColor={colorOf(cc.college)}
                courses={cc.courses.map((c) => ({ code: c.code, name: c.name, description: c.description, learningOutcomes: c.learning_outcomes, topCode: c.top_code }))}
                schoolName={cc.college}
                hideOccupationPathways
                socFilter=""
              />
            ))}
          </div>
        </Section>
      )}

      {/* Partnership Opportunities — regional employers hiring for this SOC at
          the consortium grain. Same employer set + row rendering as the
          per-college targeted report (employers are regional, so the set is
          identical regardless of college). */}
      {r.partnership_opportunities.length > 0 && (
        <Section title="Partnership Opportunities" brandColor={ACCENT}>
          <Prose>{r.partnership_opportunities_narrative}</Prose>
          <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 2 }}>
            {r.partnership_opportunities.map((emp, i) => (
              <PartnerEmployerRow key={emp.name} emp={emp} index={i} brandColor={ACCENT} />
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

export default function SvampView({ colleges, onBack }: Props) {
  const [data, setData] = useState<ApiSvampLandscape | null>(null);
  // Programs landscape fetched here too, only so the header can show the
  // active-program count from the SAME source the Programs lens uses — keeping
  // the subhead count and the coverage-matrix rows in lockstep.
  const [programs, setPrograms] = useState<ApiSvampProgramsLandscape | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>(colleges[0]?.id ?? "");
  const [selectedSoc, setSelectedSoc] = useState<string | null>(null);
  // Occupations lens drill mode: "aggregated" (treemap → consortium SOC view)
  // vs "targeted" (matrix cell → per-college OpportunityReport).
  const [occView, setOccView] = useState<"aggregated" | "targeted">("aggregated");
  const [lens, setLens] = useState<Lens>("programs");
  // URL anchoring: `ready` gates view→URL writes until the initial restore from
  // the URL has run (so a shared/refreshed link isn't clobbered by default
  // state); `urlHadSoc` suppresses the highest-demand default when the URL
  // pinned a SOC. Contract in svampUrl.ts.
  const [ready, setReady] = useState(false);
  const urlHadSoc = useRef(false);
  // Sticky context banner: shown once the report header scrolls under the nav.
  const [ctxShow, setCtxShow] = useState(false);
  const ctxSentinel = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getSvampLandscape().then(setData).catch((e) => setError(e.message));
    getSvampPrograms().then(setPrograms).catch(() => {});  // header count only — a failure just omits the facet
  }, []);

  // Restore the view from the URL once on mount (client-only). The child lenses
  // (ProgramsLens, EmployersLens) restore their own slice on their own mount.
  useEffect(() => {
    const p = readSvampParams();
    if (p.lens === "programs" || p.lens === "occupations" || p.lens === "employers") setLens(p.lens);
    if (p.soc) {
      setSelectedSoc(p.soc);
      setOccView(p.college ? "targeted" : "aggregated");
      if (p.college) setSelected(p.college);
    }
    urlHadSoc.current = !!p.soc;
    setReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Switch lens (user action) — clear every selection param; the now-active
  // lens's own sync re-adds what it owns. `lens` omitted for the programs default.
  const switchLens = (l: Lens) => {
    setLens(l);
    writeSvampParams({ lens: l === "programs" ? null : l, soc: null, college: null, top: null, emp: null });
  };

  // Sync the occupations selection → URL (parent owns soc + the occupations
  // college). Gated on `ready` and the active lens.
  useEffect(() => {
    if (!ready || lens !== "occupations") return;
    writeSvampParams({ soc: selectedSoc, college: occView === "targeted" ? selected : null });
  }, [ready, lens, selectedSoc, occView, selected]);

  // Reveal the context banner when the sentinel (at the report's top) passes
  // under the 72px nav, hide it again on scroll back up.
  useEffect(() => {
    const el = ctxSentinel.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => setCtxShow(e.boundingClientRect.top < 72),
      { rootMargin: "-72px 0px 0px 0px", threshold: 0 },
    );
    obs.observe(el);
    return () => obs.disconnect();
    // `lens` is a dep: the sentinel lives only inside the occupations block, so
    // toggling lenses unmounts/remounts it — re-run to observe the live node
    // rather than a detached one (otherwise the banner never reappears).
  }, [selectedSoc, lens]);

  const byName = useMemo(() => {
    const m = new Map<string, CollegeRef>();
    colleges.forEach((c) => m.set(c.config.name, c));
    return m;
  }, [colleges]);

  // Land on the aggregated consortium view of the highest-demand occupation —
  // unless the URL pinned a SOC (shared/refreshed link), which takes precedence.
  useEffect(() => {
    if (!data || urlHadSoc.current) return;
    const cells = data.colleges[0]?.cells ?? [];
    const top = [...cells].sort((a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0))[0];
    setSelectedSoc(top?.soc_code ?? null);
    setOccView("aggregated");
  }, [data]);

  const wrap = (children: React.ReactNode) => (
    <div style={{ minHeight: "100vh", background: "#060d1f", color: "#e8ecf4", fontFamily: FONT }}>
      <AtlasHeader title="Silicon Valley Advanced Manufacturing Partnership" onBack={onBack} rightSlot={<KallipolisBrand />} position="sticky" cubeTint={ACCENT} showPreview titleSize="15px" />
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 28px 90px" }}>{children}</div>
    </div>
  );

  if (error) {
    return wrap(<div style={{ padding: "80px 0", color: GAP, fontFamily: MONO, fontSize: 13 }}>Failed to load: {error}</div>);
  }
  if (!data) {
    return wrap(
      <div style={{ display: "flex", justifyContent: "center", padding: "120px 0" }}>
        <RisingSun style={{ width: 64, height: "auto" }} />
      </div>,
    );
  }

  const agg = data.aggregate;
  // Active programs = SVAMP TOPs with enrollment or awards — the exact filter the
  // Programs lens applies to its coverage-matrix rows, so this count matches what
  // that lens shows. null until the programs landscape resolves.
  const activePrograms = programs
    ? programs.tops.filter((t) => t.enrollment_total > 0 || t.awards_total > 0).length
    : null;
  const selCollege: ApiSvampCollege | undefined =
    data.colleges.find((c) => byName.get(c.name)?.id === selected) ?? data.colleges[0];
  const selRef = selCollege ? byName.get(selCollege.name) : undefined;
  const selBrand = selRef?.config.brandColorLight ?? ACCENT;
  const selectedCell = selCollege?.cells.find((c) => c.soc_code === selectedSoc);

  // SVAMP-owned Program Outcomes panel — injected into the embedded report
  // between Curriculum Alignment and Student Impact via OpportunityReportBody's
  // `programOutcomes` slot (so it reads as a peer report section without
  // touching the shared per-college report). Null when the selection has no
  // DataMart program data.
  const hasAwards =
    !!selectedCell &&
    data.award_years.length > 0 &&
    selectedCell.programs.some((p) => (p.awards ?? []).some((v) => v > 0));
  const hasEnrollment =
    !!selectedCell &&
    data.enrollment_terms.length > 0 &&
    selectedCell.programs.some((p) => (p.enrollment ?? []).some((v) => v != null && v > 0));
  const awardsWindow = data.award_years.length
    ? `${data.award_years[0]} to ${data.award_years[data.award_years.length - 1]}`
    : "";

  // One shared color per program for the whole cell, so a program reads as the
  // same color in BOTH the enrollment and award charts. One program is the
  // "lead" and takes the school brand in both — chosen, where possible, among
  // programs present in both charts (so the brand is guaranteed to appear in
  // each) and the most prominent across them; every other program keeps a
  // stable palette hue by its position in the cell.
  const cellPrograms = selectedCell?.programs ?? [];
  const enrollTotal = (p: ApiSvampProgram) => (p.enrollment ?? []).reduce((s: number, v) => s + (v ?? 0), 0);
  const awardTotal = (p: ApiSvampProgram) => (p.awards ?? []).reduce((s: number, v) => s + (v ?? 0), 0);
  const sumE = cellPrograms.reduce((s, p) => s + enrollTotal(p), 0) || 1;
  const sumA = cellPrograms.reduce((s, p) => s + awardTotal(p), 0) || 1;
  const prominence = (p: ApiSvampProgram) => enrollTotal(p) / sumE + awardTotal(p) / sumA;
  const inBoth = cellPrograms.filter((p) => enrollTotal(p) > 0 && awardTotal(p) > 0);
  const leadPool = inBoth.length ? inBoth : cellPrograms;
  const lead = leadPool.reduce<ApiSvampProgram | null>(
    (best, p) => (best && prominence(best) >= prominence(p) ? best : p), null);
  // Non-lead programs draw from the palette filtered to hues clearly distinct
  // from the brand (so none mimics it), assigned in cell order.
  const [bh, bs] = hexToHsl(selBrand);
  const distinct = bs < 25
    ? OVERLAY_COLORS
    : OVERLAY_COLORS.filter((c) => { const [ch, cs] = hexToHsl(c); return cs < 25 || hueDist(ch, bh) >= 40; });
  const palette = distinct.length ? distinct : OVERLAY_COLORS;
  const programColor = new Map<string, string>();
  let pi = 0;
  cellPrograms.forEach((p) => {
    programColor.set(p.top6, p.top6 === lead?.top6 ? selBrand : palette[pi++ % palette.length]);
  });
  const colorOf = (top6: string) => programColor.get(top6) ?? palette[0];
  const programOutcomesPanel =
    selectedCell && selectedCell.programs.length > 0 && selRef ? (
      <>
        {/* Awards + enrollment always hold a chart-shaped panel — the populated
            trend, or the ghost scaffold (no-data state) keyed off has* — so the
            footprint never collapses and a no-data panel reads as a known state. */}
        <Section title="Program Awards" brandColor={selBrand}>
          <Prose>
            {hasAwards
              ? "Credentials awarded per year by those same programs. Toggle between the stacked total and per-program trends; hover a program to focus it."
              : `No awards are reported for these programs${awardsWindow ? ` over ${awardsWindow}` : ""} via CCCCO DataMart.`}
          </Prose>
          <TrendChart
            series={selectedCell.programs.map((p) => ({ top6: p.top6, name: p.name, vals: p.awards ?? [] }))}
            labels={data.award_years.map(awardYearLabel)}
            defaultMode="stacked"
            colorOf={colorOf}
            empty={!hasAwards}
          />
        </Section>
        <Section title="Program Enrollments" brandColor={selBrand}>
          <Prose>
            {hasEnrollment
              ? `Term-by-term enrollment for the ${selRef.config.name} programs that prepare students for this occupation, excluding the structurally-low summer terms. Toggle between per-program trends and the combined total; hover a program to focus it.`
              : "No enrollment is reported for these programs via CCCCO DataMart."}
          </Prose>
          <TrendChart
            series={selectedCell.programs.map((p) => ({ top6: p.top6, name: p.name, vals: p.enrollment }))}
            labels={data.enrollment_terms}
            defaultMode="lines"
            colorOf={colorOf}
            axisStyle="twoTier"
            empty={!hasEnrollment}
          />
        </Section>
        {/* No wage outcomes in the (college, SOC) cell by design: the wage
            data is statewide pooled TOP6-grain (no college dimension), and
            rendering it under a single college's brand asserts a per-college
            outcome the data cannot support. Wages live at their home axis —
            the Programs lens program report. */}
      </>
    ) : null;

  // Columns = member colleges (with a soc→cell map); rows = the 12 roles.
  const columns = colleges.map((ref) => {
    const c = data.colleges.find((x) => x.name === ref.config.name);
    return { ref, cellMap: new Map((c?.cells ?? []).map((cell) => [cell.soc_code, cell])) };
  });
  // Rows ranked by regional demand (descending) — one well-defined order since
  // demand is regional, and it matches the demand-sorted treemap above so the
  // highest-opportunity roles surface at the top of both views.
  const socRows = [...(data.colleges[0]?.cells ?? [])].sort(
    (a, b) => (b.annual_openings ?? 0) - (a.annual_openings ?? 0),
  );

  // Shared CoverageMatrix inputs: cols = member colleges, rows = roles ranked by
  // regional demand. level() reads the OCCUPATION_PIPELINE-backed cell — gap
  // cells stay selectable (they open the crosswalk-only view).
  const occCols = columns.map(({ ref }) => ({ id: ref.id, label: shortName(ref.config.name), brand: ref.config.brandColorLight }));
  const occCellByKey = new Map<string, ApiSvampCell | undefined>();
  columns.forEach(({ ref, cellMap }) => socRows.forEach((soc) => occCellByKey.set(ref.id + "|" + soc.soc_code, cellMap.get(soc.soc_code))));
  const occRows = socRows.map((soc) => ({ id: soc.soc_code, label: ROLE_LABEL[soc.soc_code] ?? soc.title, sublabel: `SOC ${soc.soc_code}`, title: soc.title }));
  const occLevel = (rowId: string, colId: string) => level(occCellByKey.get(colId + "|" + rowId));

  // Report chrome adopts the active lens's color (occupations red / programs
  // green), so the whole report wears the selected mode.
  const lensAccent = lens === "programs" ? PROGRAM_ACCENT : lens === "employers" ? EMPLOYER_ACCENT : ACCENT;
  return wrap(
    <>
      {/* Sticky context banner — College · Occupation · SOC, pinned under the
          nav once the report header scrolls away, so the (college, occupation)
          identity stays visible deep in the report. Echoes the report eyebrow
          (accent college name) and meta (mono SOC code). */}
      {lens === "occupations" && selectedSoc && selectedCell && (() => {
        const targeted = occView === "targeted";
        const lead = targeted ? (selRef?.config.name ?? "") : "Consortium";
        const leadColor = targeted ? selBrand : ACCENT;
        return (
        <div
          style={{
            position: "fixed", top: 72, left: 0, right: 0, zIndex: 25, height: 46,
            background: "rgba(6,13,31,0.92)", backdropFilter: "blur(8px)",
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            display: "flex", alignItems: "center",
            opacity: ctxShow ? 1 : 0,
            transform: ctxShow ? "translateY(0)" : "translateY(-8px)",
            pointerEvents: ctxShow ? "auto" : "none",
            transition: "opacity .22s ease, transform .22s ease",
          }}
        >
          <div style={{ maxWidth: 900, width: "100%", margin: "0 auto", padding: "0 28px", display: "flex", alignItems: "baseline", gap: 10, minWidth: 0 }}>
            <span style={{ fontFamily: FONT, fontSize: 11.5, fontWeight: 700, letterSpacing: "0.18em", textTransform: "uppercase", color: leadColor, flex: "none", whiteSpace: "nowrap" }}>
              {lead}
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)", flex: "none" }}>·</span>
            <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.9)", flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {selectedCell.title}
            </span>
            <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.05em", color: hexA(leadColor, 0.65), flex: "none", whiteSpace: "nowrap" }}>
              SOC {selectedSoc}
            </span>
          </div>
        </div>
        );
      })()}
      {/* Report header — same magazine idiom as the per-occupation report */}
      <ReportHeader eyebrow="Partnership Landscape Report" title="Silicon Valley Advanced Manufacturing Partnership" accent={lensAccent}>
        {/* Colored bookends — the consortium (who) and the region (where) take
            the lens accent; the supply/demand counts sit neutral between them. */}
        <span style={{ color: lensAccent, opacity: 0.7 }}>{agg.n_colleges} Member Colleges</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{activePrograms ?? "—"} Programs</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{agg.n_occupations} Occupations</span>
        <Dot /><span style={{ color: lensAccent, opacity: 0.7 }}>{data.region_display}</span>
      </ReportHeader>

      {/* Lens switcher — Occupations (built) · Programs (built) · Employers
          (placeholder until that view ships). Three Platonic forms. */}
      <LensTabs lens={lens} setLens={switchLens} />

      {lens === "occupations" ? (
      <>
      {/* Executive summary — backend-composed thesis, then the coverage grid
          that selects what renders inline below it. */}
      <Section title="Regional Labor Demand" brandColor={ACCENT}>
        <Prose>{data.executive_summary}</Prose>
        <DemandTreemap cells={data.colleges[0]?.cells ?? []} total={agg.regional_demand_total} selected={occView === "aggregated" ? selectedSoc : null} onSelect={(soc) => { setSelectedSoc(soc); setOccView("aggregated"); }} />

        {/* coverage grid (shared CoverageMatrix) */}
        <CoverageMatrix
          cols={occCols}
          rows={occRows}
          level={occLevel}
          selectedRow={selectedSoc}
          selectedCol={occView === "targeted" ? (selRef?.id ?? null) : null}
          cornerLabel="↓ role (by demand) · → college"
          gapCellHint="no enrollment or awards (view crosswalk)"
          legend={[
            { k: "Covered", sub: "enrollment & awards", bg: "rgba(148,168,201,.92)", ring: true },
            { k: "Partial", sub: "enrollment or awards", bg: "rgba(148,168,201,.3)", ring: true },
            { k: "Gap", sub: "neither", bg: "rgba(255,255,255,.035)", ring: false },
          ]}
          caption="Each cell is one college’s coverage — click for that college’s report."
          onSelect={(soc, collegeId) => { setSelected(collegeId); setSelectedSoc(soc); setOccView("targeted"); }}
          onSelectRow={(soc) => { setSelectedSoc(soc); setOccView("aggregated"); }}
        />
      </Section>

      {/* Inline detail — the selected occupation's report, exec summary
          suppressed so it opens on Occupational Demand. The Program Outcomes
          panel is injected between Curriculum Alignment and Student Impact via
          the programOutcomes slot. Uses the selected college's own brand color,
          distinct from the red consortium chrome. */}
      {selectedSoc && (
        <div style={{ marginTop: 36 }}>
          <div ref={ctxSentinel} style={{ height: 1 }} />
          {occView === "aggregated" ? (
            <OccupationAggregateReport soc={selectedSoc} colleges={colleges} isSectorPriority={data.is_sector_priority} />
          ) : selRef ? (
            // hideLaborMarket: the COE supply/demand projections are hidden by
            // design in the SVAMP embedding — supply's authority here is
            // DataMart actuals (the Program Outcomes panel), and one college's
            // supply against full regional demand is a partial-vs-whole
            // mismatch; the market-scale comparison lives at the consortium
            // grain (occupation summary, Programs-lens Demand toggle).
            // Per-college standalone reports keep the section.
            <OpportunityReportBody school={selRef.config} socCode={selectedSoc} sector={data.sector} hideExecutiveSummary hideStudentImpact embedded programOutcomes={programOutcomesPanel} hideLaborMarket topPrefix={SVAMP_TOP_DIVISION} cteOnly excludeTops={SVAMP_MANDATE_EXCLUDED_TOPS} />
          ) : null}
        </div>
      )}
      </>
      ) : lens === "programs" ? (
        <ProgramsLens colleges={colleges} />
      ) : (
        <EmployersLens colleges={colleges} />
      )}
    </>,
  );
}
