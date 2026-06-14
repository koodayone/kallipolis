"use client";

/**
 * ClusterMap — the consortium's occupational-cluster landscape.
 *
 * Renders the connected-component clusters from /partnerships/{member}/clusters:
 * each card is one cluster (occupations bound by shared feeder programs), with a
 * coverage bar (supply filling regional demand) as the hero metric and the full
 * per-occupation numbers. Expanding a card lazily pulls the school×TOP supply
 * detail from the SEPARATE /cluster-supply endpoint.
 */

import { useEffect, useMemo, useState } from "react";
import {
  getConsortiumClusters,
  getConsortiumClusterSupply,
  type ApiCluster,
  type ApiClusterMap,
  type ApiClusterSupplyMap,
} from "./api";

const BG = "#060d1f";
const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";
const HAIR = "rgba(255,255,255,0.09)";
const PANEL = "rgba(255,255,255,0.025)";
const TEXT = "rgba(255,255,255,0.90)";
const DIM = "rgba(255,255,255,0.52)";
const FAINT = "rgba(255,255,255,0.34)";
const TRACK = "rgba(255,255,255,0.07)";
const POS = "#4cb98a";
const NEG = "#e0625a";

const n = (x: number) => x.toLocaleString("en-US");
const money = (x: number) => "$" + x.toLocaleString("en-US");
const growth = (g: number) => (g >= 0 ? "+" : "") + (g * 100).toFixed(1) + "%";

type SortKey = "gap" | "coverage" | "demand" | "wage";
const SORTS: { key: SortKey; label: string }[] = [
  { key: "gap", label: "Largest gap" },
  { key: "coverage", label: "Least covered" },
  { key: "demand", label: "Most demand" },
  { key: "wage", label: "Highest wage" },
];

export default function ClusterMap() {
  const [data, setData] = useState<ApiClusterMap | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [supply, setSupply] = useState<ApiClusterSupplyMap | null>(null);
  const [supplyLoading, setSupplyLoading] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [sort, setSort] = useState<SortKey>("gap");
  const [sector, setSector] = useState<string | null>(null);

  useEffect(() => {
    getConsortiumClusters("baccc").then(setData).catch((e) => setErr(String(e)));
  }, []);

  function ensureSupply() {
    if (supply || supplyLoading) return;
    setSupplyLoading(true);
    getConsortiumClusterSupply("baccc")
      .then(setSupply)
      .catch(() => {})
      .finally(() => setSupplyLoading(false));
  }

  function toggle(id: string) {
    ensureSupply();
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const supplyById = useMemo(() => {
    const m = new Map<string, ApiClusterSupplyMap["clusters"][number]>();
    supply?.clusters.forEach((c) => m.set(c.id, c));
    return m;
  }, [supply]);

  const sectors = useMemo(() => {
    if (!data) return [];
    const seen = new Map<string, { id: string; label: string; accent: string }>();
    data.clusters.forEach((c) =>
      seen.set(c.sector_id, { id: c.sector_id, label: c.sector_label, accent: c.accent }),
    );
    return [...seen.values()].sort((a, b) => a.label.localeCompare(b.label));
  }, [data]);

  const shown = useMemo(() => {
    if (!data) return [];
    let cs = data.clusters.filter((c) => !sector || c.sector_id === sector);
    const by: Record<SortKey, (c: ApiCluster) => number> = {
      gap: (c) => -c.gap,
      coverage: (c) => c.coverage,
      demand: (c) => -c.demand,
      wage: (c) => -c.wage_high,
    };
    return [...cs].sort((a, b) => by[sort](a) - by[sort](b));
  }, [data, sort, sector]);

  const wrap: React.CSSProperties = {
    position: "fixed",
    inset: 0,
    zIndex: 10,
    background: BG,
    overflowY: "auto",
    overscrollBehavior: "none",
    scrollbarGutter: "stable",
    fontFamily: FONT,
    color: TEXT,
  };

  if (err) {
    return (
      <div style={{ ...wrap, display: "grid", placeItems: "center" }}>
        <div style={{ color: NEG, fontSize: 13 }}>Failed to load clusters — {err}</div>
      </div>
    );
  }
  if (!data) {
    return (
      <div style={{ ...wrap, display: "grid", placeItems: "center" }}>
        <div style={{ color: DIM, fontSize: 13, letterSpacing: "0.04em" }}>
          Building the cluster landscape…
        </div>
      </div>
    );
  }

  const overall = data.total_demand ? data.total_supply / data.total_demand : 0;

  return (
    <div style={wrap}>
      <div style={{ maxWidth: 1360, margin: "0 auto", padding: "40px 28px 80px" }}>
        {/* ── Masthead ─────────────────────────────────────────── */}
        <div style={{ marginBottom: 26 }}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: "#c9a84c",
            }}
          >
            Bay Area Community College Consortium
          </div>
          <h1
            style={{
              fontSize: 30,
              fontWeight: 600,
              letterSpacing: "-0.01em",
              margin: "10px 0 8px",
              color: TEXT,
            }}
          >
            Occupational Target Clusters
          </h1>
          <p style={{ fontSize: 13.5, lineHeight: 1.55, color: DIM, maxWidth: 760, margin: 0 }}>
            {data.n_clusters} connected-component clusters across {sectors.length} sectors and{" "}
            {data.n_occupations} target occupations. A cluster groups occupations trained by
            shared programs; its supply is the summed awards of those programs, so the gap is
            counted once — never split or double-counted across the crosswalk.
          </p>
        </div>

        {/* ── Totals strip ─────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 0,
            border: `1px solid ${HAIR}`,
            borderRadius: 12,
            background: PANEL,
            padding: "16px 4px",
            marginBottom: 26,
          }}
        >
          <Stat label="Occupations" value={n(data.n_occupations)} />
          <Stat label="Clusters" value={n(data.n_clusters)} />
          <Stat label="Regional demand" value={n(data.total_demand)} sub="annual openings" />
          <Stat label="Consortium supply" value={n(data.total_supply)} sub="annual awards" />
          <Stat label="Supply gap" value={n(data.total_gap)} accent={NEG} />
          <div style={{ flex: 1, minWidth: 200, padding: "0 18px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 10.5, letterSpacing: "0.14em", textTransform: "uppercase", color: FAINT }}>
                Overall coverage
              </span>
              <span style={{ fontFamily: MONO, fontSize: 12, color: TEXT }}>
                {Math.round(overall * 100)}%
              </span>
            </div>
            <Bar coverage={overall} accent="#c9a84c" />
          </div>
        </div>

        {/* ── Controls ─────────────────────────────────────────── */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center", marginBottom: 20 }}>
          <div style={{ display: "flex", gap: 6 }}>
            {SORTS.map((s) => (
              <Chip key={s.key} active={sort === s.key} onClick={() => setSort(s.key)}>
                {s.label}
              </Chip>
            ))}
          </div>
          <div style={{ width: 1, height: 18, background: HAIR }} />
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <Chip active={sector === null} onClick={() => setSector(null)}>
              All sectors
            </Chip>
            {sectors.map((s) => (
              <Chip
                key={s.id}
                active={sector === s.id}
                onClick={() => setSector(sector === s.id ? null : s.id)}
                dot={s.accent}
              >
                {s.label}
              </Chip>
            ))}
          </div>
        </div>

        {/* ── Cluster grid ─────────────────────────────────────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(404px, 1fr))",
            gap: 16,
            alignItems: "start",
          }}
        >
          {shown.map((c) => (
            <ClusterCard
              key={c.id}
              c={c}
              open={expanded.has(c.id)}
              onToggle={() => toggle(c.id)}
              supply={supplyById.get(c.id) ?? null}
              supplyLoading={supplyLoading}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div style={{ padding: "0 18px", borderRight: `1px solid ${HAIR}`, minWidth: 120 }}>
      <div style={{ fontSize: 10.5, letterSpacing: "0.14em", textTransform: "uppercase", color: FAINT, marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 21, fontWeight: 600, color: accent ?? TEXT, lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10.5, color: FAINT, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Bar({ coverage, accent }: { coverage: number; accent: string }) {
  const pct = Math.max(0, Math.min(1, coverage)) * 100;
  return (
    <div style={{ height: 9, borderRadius: 5, background: TRACK, overflow: "hidden" }}>
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          borderRadius: 5,
          background: `linear-gradient(90deg, ${accent}cc, ${accent})`,
          transition: "width 0.5s ease",
        }}
      />
    </div>
  );
}

function Chip({
  children,
  active,
  onClick,
  dot,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
  dot?: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        border: `1px solid ${active ? "rgba(201,168,76,0.5)" : HAIR}`,
        background: active ? "rgba(201,168,76,0.12)" : "transparent",
        color: active ? "#e8d49a" : DIM,
        fontFamily: FONT,
        fontSize: 11.5,
        letterSpacing: "0.02em",
        padding: "5px 11px",
        borderRadius: 7,
        cursor: "pointer",
        transition: "all 0.15s",
      }}
    >
      {dot && <span style={{ width: 7, height: 7, borderRadius: 99, background: dot, flex: "none" }} />}
      {children}
    </button>
  );
}

function ClusterCard({
  c,
  open,
  onToggle,
  supply,
  supplyLoading,
}: {
  c: ApiCluster;
  open: boolean;
  onToggle: () => void;
  supply: ApiClusterSupplyMap["clusters"][number] | null;
  supplyLoading: boolean;
}) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        border: `1px solid ${hover ? "rgba(255,255,255,0.16)" : HAIR}`,
        borderRadius: 12,
        background: open ? "rgba(255,255,255,0.035)" : PANEL,
        overflow: "hidden",
        transition: "border-color 0.15s, background 0.15s",
      }}
    >
      {/* accent rail + header */}
      <div style={{ display: "flex" }}>
        <div style={{ width: 3, background: c.accent, flex: "none" }} />
        <div style={{ flex: 1, minWidth: 0, padding: "14px 16px 0" }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              color: c.accent,
              marginBottom: 7,
              display: "flex",
              justifyContent: "space-between",
              gap: 8,
            }}
          >
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {c.sector_label}
            </span>
            <span style={{ color: FAINT, fontWeight: 600 }}>
              {c.occupations.length} {c.occupations.length === 1 ? "occ" : "occs"}
            </span>
          </div>
          <div style={{ fontSize: 14.5, fontWeight: 600, color: TEXT, lineHeight: 1.3, marginBottom: 14 }}>
            {c.label}
          </div>

          {/* coverage bar — the hero */}
          <Bar coverage={c.coverage} accent={c.accent} />
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, marginBottom: 14 }}>
            <Metric label="Demand" value={n(c.demand)} />
            <Metric label="Supply" value={n(c.supply)} accent={c.accent} />
            <Metric label="Gap" value={n(c.gap)} accent={NEG} />
            <Metric label="Coverage" value={Math.round(c.coverage * 100) + "%"} align="right" />
          </div>
        </div>
      </div>

      {/* occupations */}
      <div style={{ padding: "0 16px" }}>
        {c.occupations.map((o, i) => (
          <div
            key={o.soc}
            style={{
              padding: "9px 0",
              borderTop: i === 0 ? `1px solid ${HAIR}` : `1px solid rgba(255,255,255,0.045)`,
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 3 }}>
              <span style={{ fontSize: 13, color: TEXT, fontWeight: 500, lineHeight: 1.25 }}>{o.title}</span>
              {o.admitted && (
                <span
                  style={{
                    fontSize: 8.5,
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    color: "#c9a84c",
                    border: "1px solid rgba(201,168,76,0.4)",
                    borderRadius: 4,
                    padding: "1px 4px",
                    flex: "none",
                  }}
                >
                  ADDED
                </span>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: MONO, fontSize: 11.5 }}>
              <span style={{ color: FAINT, minWidth: 56 }}>{o.soc}</span>
              <span style={{ color: DIM }}>{money(o.annual_wage)}</span>
              <span style={{ color: DIM }}>{n(o.annual_openings)} open</span>
              <span style={{ color: o.growth_rate >= 0 ? POS : NEG }}>{growth(o.growth_rate)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* footer */}
      <button
        onClick={onToggle}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          marginTop: 4,
          padding: "10px 16px",
          background: "transparent",
          border: "none",
          borderTop: `1px solid ${HAIR}`,
          cursor: "pointer",
          fontFamily: FONT,
        }}
      >
        <span style={{ fontSize: 11, color: DIM }}>
          {c.n_colleges} colleges · {c.n_programs} {c.n_programs === 1 ? "program" : "programs"} ·{" "}
          {money(c.wage_low)}–{money(c.wage_high)}
        </span>
        <span style={{ fontSize: 11, color: hover ? "#c9a84c" : FAINT, display: "flex", alignItems: "center", gap: 5 }}>
          {open ? "Hide supply" : "Schools × programs"}
          <span style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s", fontSize: 9 }}>
            ▾
          </span>
        </span>
      </button>

      {/* expanded school×TOP supply */}
      {open && (
        <div style={{ padding: "4px 16px 16px", borderTop: `1px solid rgba(255,255,255,0.045)`, background: "rgba(0,0,0,0.18)" }}>
          {!supply && supplyLoading && (
            <div style={{ fontSize: 11.5, color: FAINT, padding: "10px 0" }}>Loading supply detail…</div>
          )}
          {supply && <SupplyDetail supply={supply} accent={c.accent} />}
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  accent,
  align,
}: {
  label: string;
  value: string;
  accent?: string;
  align?: "right";
}) {
  return (
    <div style={{ textAlign: align ?? "left" }}>
      <div style={{ fontSize: 9.5, letterSpacing: "0.1em", textTransform: "uppercase", color: FAINT, marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 13.5, fontWeight: 600, color: accent ?? TEXT }}>{value}</div>
    </div>
  );
}

function SupplyDetail({
  supply,
  accent,
}: {
  supply: ApiClusterSupplyMap["clusters"][number];
  accent: string;
}) {
  // group tuples by program, programs sorted by total awards desc
  const groups = useMemo(() => {
    const byProgram = new Map<string, { program: string; total: number; rows: { college: string; awards: number }[] }>();
    supply.tuples.forEach((t) => {
      const g = byProgram.get(t.top6) ?? { program: t.program, total: 0, rows: [] };
      g.total += t.awards;
      g.rows.push({ college: t.college, awards: t.awards });
      byProgram.set(t.top6, g);
    });
    return [...byProgram.values()].sort((a, b) => b.total - a.total);
  }, [supply]);

  return (
    <div style={{ paddingTop: 8 }}>
      <div style={{ fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: FAINT, marginBottom: 10 }}>
        Supply — {supply.tuples.length} school × program tuples
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {groups.map((g) => (
          <div key={g.program}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 6 }}>
              <span style={{ width: 5, height: 5, borderRadius: 99, background: accent, flex: "none" }} />
              <span style={{ fontSize: 12, color: TEXT, fontWeight: 500 }}>{g.program}</span>
              <span style={{ fontFamily: MONO, fontSize: 11, color: FAINT }}>{g.total} awards</span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, paddingLeft: 13 }}>
              {g.rows.map((r) => (
                <span
                  key={r.college}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    border: `1px solid ${HAIR}`,
                    borderRadius: 6,
                    padding: "3px 8px",
                    fontSize: 11,
                    color: DIM,
                    background: "rgba(255,255,255,0.02)",
                  }}
                >
                  {r.college}
                  <span style={{ fontFamily: MONO, color: TEXT, fontSize: 10.5 }}>{r.awards}</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
