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
          suppressed so it opens on Occupational Demand. Uses the selected
          college's own brand color, distinct from the red consortium chrome. */}
      {selectedSoc && selRef && (
        <div style={{ marginTop: 36 }}>
          <OpportunityReportBody school={selRef.config} socCode={selectedSoc} sector={data.sector} hideExecutiveSummary embedded />
        </div>
      )}
    </>,
  );
}
