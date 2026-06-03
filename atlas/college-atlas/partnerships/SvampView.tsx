"use client";

import { useMemo, useState, useEffect } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import { FONT, MONO, ReportHeader, Section, Prose } from "@/college-atlas/partnerships/reportChrome";
import { OpportunityReportBody } from "@/college-atlas/partnerships/OpportunityReport";
import { getSvampLandscape } from "@/college-atlas/partnerships/api";
import type {
  ApiSvampLandscape,
  ApiSvampCell,
  ApiSvampCollege,
  ApiSvampProgram,
} from "@/college-atlas/partnerships/api";

const GAP = "#e0654f";
// SVAMP consortium accent (red) — cube, eyebrow, hairline, section bars.
const ACCENT = "#ff5a5a";

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

// Alignment level, grounded in the data: teaches it AND has projected
// completions = strong; teaches it only = partial; no curriculum = gap.
function level(cell: ApiSvampCell | undefined): "none" | "partial" | "strong" {
  if (!cell || cell.course_count === 0) return "none";
  return cell.supply > 0 ? "strong" : "partial";
}
const rank = (c: ApiSvampCell) => (c.course_count === 0 ? 0 : c.supply > 0 ? 2 : 1);
function sortCells(cells: ApiSvampCell[]): ApiSvampCell[] {
  return [...cells].sort((a, b) => {
    if (rank(b) !== rank(a)) return rank(b) - rank(a);
    if ((b.supply || 0) !== (a.supply || 0)) return (b.supply || 0) - (a.supply || 0);
    return (b.gap || 0) - (a.gap || 0);
  });
}
function topTaughtSoc(c: ApiSvampCollege | undefined): string | null {
  if (!c) return null;
  const first = sortCells(c.cells).find((x) => x.course_count > 0);
  return first ? first.soc_code : null;
}
const shortName = (name: string) => name.replace(/ Valley College$/, "").replace(/ College$/, "");
function hexA(hex: string, a: number) {
  const h = hex.replace("#", "");
  return `rgba(${parseInt(h.slice(0, 2), 16)},${parseInt(h.slice(2, 4), 16)},${parseInt(h.slice(4, 6), 16)},${a})`;
}
const Dot = () => <span style={{ color: "rgba(255,255,255,0.25)", margin: "0 8px" }}>·</span>;

// ── Enrollment trend chart ────────────────────────────────────────────────
// The 10-term enrollment array (SVAMP_TERMS) drops its null boundary terms
// (Fall 2023 / Winter 2026 — no data reported) to the 8 reported terms.
// Labels for the full SVAMP_TERMS series (10 terms). We no longer assume the
// boundary terms are empty — colleges differ by calendar (De Anza runs
// quarters with no Fall-2023 report; Ohlone runs Fall/Spring/Summer with no
// Winter), so leading/trailing empties are trimmed dynamically, not hardcoded.
const ENROLL_ABBR = ["Fall 23", "Win 24", "Spr 24", "Sum 24", "Fall 24", "Win 25", "Spr 25", "Sum 25", "Fall 25", "Win 26"];
// Distinct line colors per program (cycled). The enrollment overlay is a
// multi-series chart, so each TOP program gets its own hue, keyed by the
// legend; the section's brand accent stays the college's.
const OVERLAY_COLORS = ["#e85d8a", "#5ab0c4", "#c9a84c", "#7bd88f", "#b483f0", "#f0915a", "#67c2c9", "#e0654f", "#9aa6bd"];

// Edge-safe text anchor: the leftmost/rightmost slots anchor inward so their
// value/term labels never spill past the chart's plot area.
function edgeAnchor(i: number, n: number): "start" | "middle" | "end" {
  if (i === 0) return "start";
  if (i === n - 1) return "end";
  return "middle";
}

// Interactive enrollment overlay: all feeder TOP programs for the SOC on one
// shared y-axis. Gridlines give magnitude; relative size reads at a glance.
// Hover a legend program to focus it — it brightens, the rest fade, and its
// points get labeled with the actual term values; mouse out returns to the
// overview. Leading/trailing empty terms are trimmed dynamically across the
// whole set (colleges differ by calendar), with internal gaps spanned.
function EnrollmentOverlay({ programs }: { programs: ApiSvampProgram[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const anyAt = (i: number) => programs.some((p) => p.enrollment[i] != null);
  let first = 0; while (first < 10 && !anyAt(first)) first++;
  let lastT = 9; while (lastT >= 0 && !anyAt(lastT)) lastT--;
  const allVals = programs.flatMap((p) => p.enrollment.filter((v): v is number => v != null));
  if (lastT < first || !allVals.length) return null;
  const slots: number[] = [];
  for (let i = first; i <= lastT; i++) slots.push(i);
  const n = slots.length;
  const dataMax = Math.max(...allVals);
  const step = dataMax > 300 ? 100 : 50;
  // Round the axis up to the next gridline so the top line bounds the data
  // (peak 197 -> axis 200) and the highest value is always labeled.
  const axisMax = Math.ceil(dataMax / step) * step;
  const W = 760, H = 256, padL = 34, padR = 14, padT = 18, padB = 26, base = H - padB, top = padT;
  const X = (pos: number) => (n === 1 ? (padL + W - padR) / 2 : padL + (pos / (n - 1)) * (W - padL - padR));
  const Y = (v: number) => base - (v / axisMax) * (base - top);
  const posOf = (slot: number) => slots.indexOf(slot);
  const ticks: number[] = [];
  for (let t = step; t <= axisMax; t += step) ticks.push(t);

  return (
    <div style={{ marginTop: 16 }}>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke="rgba(255,255,255,.1)" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={padL} x2={W - padR} y1={Y(t)} y2={Y(t)} stroke="rgba(255,255,255,.05)" />
            <text x={padL - 6} y={Y(t) + 3} textAnchor="end" style={{ fontFamily: MONO, fontSize: 9, fill: "#5e6a83" }}>{t.toLocaleString("en-US")}</text>
          </g>
        ))}
        {programs.map((p, pi) => {
          const color = OVERLAY_COLORS[pi % OVERLAY_COLORS.length];
          const on = hover === pi, faded = hover != null && !on;
          const pts = slots.filter((i) => p.enrollment[i] != null)
            .map((i) => ({ x: X(posOf(i)), y: Y(p.enrollment[i] as number), v: p.enrollment[i] as number, i }));
          if (!pts.length) return null;
          const path = pts.map((q, k) => (k ? "L" : "M") + q.x.toFixed(1) + " " + q.y.toFixed(1)).join(" ");
          const lastPt = pts[pts.length - 1];
          return (
            <g key={p.top6}>
              <path d={path} fill="none" stroke={color} strokeWidth={on ? 3 : 2} strokeLinejoin="round" strokeLinecap="round" opacity={faded ? 0.12 : on ? 1 : 0.82} />
              {on
                ? pts.map((q) => (
                    <g key={q.i}>
                      <circle cx={q.x} cy={q.y} r={3} fill={color} />
                      <text x={q.x} y={q.y - 8} textAnchor={edgeAnchor(posOf(q.i), n)} style={{ fontFamily: MONO, fontSize: 9.5, fill: "#e8ecf4" }}>{q.v.toLocaleString("en-US")}</text>
                    </g>
                  ))
                : hover == null && <circle cx={lastPt.x} cy={lastPt.y} r={2.4} fill={color} />}
              {/* invisible wide hit area so the thin line itself is hoverable */}
              <path d={path} fill="none" stroke="transparent" strokeWidth={14} style={{ pointerEvents: "stroke", cursor: "pointer" }} onMouseEnter={() => setHover(pi)} onMouseLeave={() => setHover(null)} />
            </g>
          );
        })}
        {slots.map((i, k) => (
          <text key={i} x={X(k)} y={H - 8} textAnchor={edgeAnchor(k, n)} style={{ fontFamily: MONO, fontSize: 9.5, fill: "#5e6a83" }}>{ENROLL_ABBR[i]}</text>
        ))}
      </svg>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", marginTop: 12 }}>
        {programs.map((p, pi) => {
          const color = OVERLAY_COLORS[pi % OVERLAY_COLORS.length];
          const on = hover === pi, dim = hover != null && !on;
          return (
            <div
              key={p.top6}
              onMouseEnter={() => setHover(pi)}
              onMouseLeave={() => setHover(null)}
              style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, background: on ? "rgba(255,255,255,.07)" : "transparent", opacity: dim ? 0.45 : 1, transition: "background .12s, opacity .12s", minWidth: 0 }}
            >
              <span style={{ width: 16, height: 3, borderRadius: 2, background: color, flex: "none" }} />
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#9aa6bd" }}>{p.name}</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#5e6a83", flex: "none" }}>TOP {p.top6}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function SvampView({ colleges, onBack }: Props) {
  const [data, setData] = useState<ApiSvampLandscape | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>(colleges[0]?.id ?? "");
  const [selectedSoc, setSelectedSoc] = useState<string | null>(null);

  useEffect(() => {
    getSvampLandscape().then(setData).catch((e) => setError(e.message));
  }, []);

  const byName = useMemo(() => {
    const m = new Map<string, CollegeRef>();
    colleges.forEach((c) => m.set(c.config.name, c));
    return m;
  }, [colleges]);

  // Auto-select the default college's strongest occupation once data lands.
  useEffect(() => {
    if (!data) return;
    const def = data.colleges.find((c) => byName.get(c.name)?.id === selected) ?? data.colleges[0];
    setSelectedSoc(topTaughtSoc(def));
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
  const programOutcomesPanel =
    selectedCell && selectedCell.programs.length > 0 && selRef ? (
      <Section title="Program Enrollment" brandColor={selBrand}>
        <Prose>
          Term-by-term enrollment (DataMart) for the {shortName(selRef.config.name)} programs that prepare students for this occupation. Hover a program to read its trend.
        </Prose>
        <EnrollmentOverlay programs={selectedCell.programs} />
      </Section>
    ) : null;

  // Columns = member colleges (with a soc→cell map); rows = the 12 roles.
  const columns = colleges.map((ref) => {
    const c = data.colleges.find((x) => x.name === ref.config.name);
    return { ref, cellMap: new Map((c?.cells ?? []).map((cell) => [cell.soc_code, cell])) };
  });
  const socRows = data.colleges[0]?.cells ?? [];

  // Build the transposed coverage grid: roles (rows, English) × colleges (cols).
  const grid: React.ReactNode[] = [];
  grid.push(
    <div key="corner" style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: ".1em", textTransform: "uppercase", color: "#5e6a83", alignSelf: "end", paddingBottom: 6 }}>↓ role · → college</div>,
  );
  columns.forEach(({ ref }) => {
    const on = ref.id === selRef?.id;
    const cb = ref.config.brandColorLight;
    grid.push(
      <div key={"h-" + ref.id} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, fontSize: 11.5, fontWeight: 600, paddingBottom: 11, color: on ? cb : "#9aa6bd", boxShadow: on ? `inset 0 -2px 0 ${cb}` : "none", transition: "color .15s" }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: ref.config.brandColorLight, flex: "none" }} />
        {shortName(ref.config.name)}
      </div>,
    );
  });
  socRows.forEach((soc) => {
    const short = ROLE_LABEL[soc.soc_code] ?? soc.title;
    const rowSel = soc.soc_code === selectedSoc;
    // Stacked label: role name leads, SOC code rides beneath as provenance.
    grid.push(
      <div key={"r-" + soc.soc_code} title={soc.title} style={{ paddingRight: 14, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: rowSel ? 600 : 500, color: rowSel ? selBrand : "rgba(255,255,255,.82)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{rowSel ? "▸ " : ""}{short}</div>
        <div style={{ fontFamily: MONO, fontSize: 10, color: rowSel ? selBrand : "#5e6a83", letterSpacing: ".02em", marginTop: 1, opacity: rowSel ? 0.85 : 1, transition: "color .15s" }}>SOC {soc.soc_code}</div>
      </div>,
    );
    columns.forEach(({ ref, cellMap }) => {
      const cell = cellMap.get(soc.soc_code);
      const lv = level(cell);
      const key = ref.id + "-" + soc.soc_code;
      if (lv === "none") {
        grid.push(<div key={key} style={{ height: 32, borderRadius: 7, background: "rgba(255,255,255,.035)" }} />);
        return;
      }
      const brand = ref.config.brandColorLight;
      const isSel = ref.id === selRef?.id && soc.soc_code === selectedSoc;
      const base: React.CSSProperties = {
        height: 32, borderRadius: 7, cursor: "pointer",
        background: lv === "strong" ? hexA(brand, 0.9) : hexA(brand, 0.3),
        boxShadow: `inset 0 0 0 1px ${hexA(brand, 0.5)}`,
        transition: "transform .12s, box-shadow .12s",
      };
      const sel: React.CSSProperties = isSel
        ? { boxShadow: `0 0 0 2px rgba(255,255,255,.92), 0 0 12px ${hexA(brand, 0.6)}, 0 6px 16px rgba(0,0,0,.5)`, transform: "scale(1.08)", zIndex: 2 }
        : {};
      grid.push(
        <div
          key={key}
          title={`${shortName(ref.config.name)} · ${soc.title}`}
          onClick={() => { setSelected(ref.id); setSelectedSoc(soc.soc_code); }}
          onMouseEnter={(e) => { if (!isSel) (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { if (!isSel) (e.currentTarget as HTMLElement).style.transform = "none"; }}
          style={{ ...base, ...sel }}
        />,
      );
    });
  });

  return wrap(
    <>
      {/* Report header — same magazine idiom as the per-occupation report */}
      <ReportHeader eyebrow="Partnership Landscape Report" title="Silicon Valley Advanced Manufacturing Partnership" accent={ACCENT}>
        <span style={{ color: ACCENT, opacity: 0.7 }}>{agg.n_colleges} Member Colleges</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{agg.n_occupations} Occupations</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)", letterSpacing: "0.08em" }}>{data.sector}</span>
        <Dot /><span style={{ color: "rgba(255,255,255,0.80)" }}>{data.region_display}</span>
        {data.is_sector_priority && (
          <><Dot /><span style={{ color: ACCENT, letterSpacing: "0.1em", fontWeight: 600 }}>Regional Priority Sector</span></>
        )}
      </ReportHeader>

      {/* Executive summary — backend-composed thesis, then the coverage grid
          that selects what renders inline below it. */}
      <Section title="Executive Summary" brandColor={ACCENT}>
        <Prose>{data.executive_summary}</Prose>
        <div style={{ marginTop: 14 }}>
          <Prose>Select a college and role in the coverage grid below to examine how that institution aligns with the occupational pathway.</Prose>
        </div>

        {/* coverage grid */}
        <div style={{ marginTop: 20, border: "1px solid rgba(255,255,255,.09)", borderRadius: 12, background: "rgba(0,0,0,.18)", padding: "16px 18px", overflowX: "auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: `230px repeat(${columns.length}, minmax(58px,1fr))`, gap: 4, alignItems: "center", minWidth: 540 }}>
            {grid}
          </div>
        </div>
      </Section>

      {/* Inline detail — the selected occupation's report, exec summary
          suppressed so it opens on Occupational Demand. The Program Outcomes
          panel is injected between Curriculum Alignment and Student Impact via
          the programOutcomes slot. Uses the selected college's own brand color,
          distinct from the red consortium chrome. */}
      {selectedSoc && selRef && (
        <div style={{ marginTop: 36 }}>
          <OpportunityReportBody school={selRef.config} socCode={selectedSoc} sector={data.sector} hideExecutiveSummary hideStudentImpact embedded programOutcomes={programOutcomesPanel} />
        </div>
      )}
    </>,
  );
}
