"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getLaborMarketOverview, getOccupationDetail, queryOccupations } from "@/lib/api";
import type { ApiOccupationMatch, ApiLaborMarketOverview, ApiOccupationDetail } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function deduplicateBySoc<T extends { soc_code: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  return items.filter((o) => { if (seen.has(o.soc_code)) return false; seen.add(o.soc_code); return true; });
}

function formatWage(wage: number | null): string {
  if (!wage) return "—";
  return `$${wage.toLocaleString()}`;
}

const EXAMPLES = [
  "Highest paying occupations in our region",
  "Roles that align most with our curriculum",
  "Fast-growing occupations with the most openings",
];

const OCCUPATION_COLUMNS: Column[] = [
  { label: "Occupation", width: "1fr" },
  { label: "Wage", width: "100px", align: "right" },
  { label: "Openings", width: "80px", align: "right" },
  { label: "5yr Growth", width: "110px", align: "right" },
];

type Props = { school: SchoolConfig; onBack: () => void };

export default function OccupationsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [overview, setOverview] = useState<ApiLaborMarketOverview | null>(null);
  const [expandedSocs, setExpandedSocs] = useState<Set<string>>(new Set());
  const [details, setDetails] = useState<Record<string, ApiOccupationDetail>>({});
  const [loadingSocs, setLoadingSocs] = useState<Set<string>>(new Set());

  const allOccupations = useMemo(
    () => deduplicateBySoc(overview?.regions?.flatMap((r) => r.occupations) ?? []).sort((a, b) => a.title.localeCompare(b.title)),
    [overview],
  );
  const regionNames = useMemo(() => overview?.regions?.map((r) => r.region) ?? [], [overview]);
  const regionLabel = regionNames.length <= 1 ? (regionNames[0] ?? "") : regionNames.join(" · ");
  const regionName = regionNames[0] ?? "";

  const loadInitialData = useCallback(async () => {
    const data = await getLaborMarketOverview(school.name);
    setOverview(data);
  }, [school.name]);

  const queryFn = useCallback(async (query: string, college: string) => {
    const resp = await queryOccupations(query, college);
    return { items: deduplicateBySoc(resp.occupations), message: resp.message };
  }, []);

  const onQueryStart = useCallback(() => { setExpandedSocs(new Set()); }, []);
  const onReset = useCallback(() => { setExpandedSocs(new Set()); }, []);

  const preserveScroll = useCallback(() => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  const handleExpand = useCallback(async (occ: ApiOccupationMatch) => {
    preserveScroll();
    const soc = occ.soc_code;
    if (expandedSocs.has(soc)) {
      setExpandedSocs((prev) => { const next = new Set(prev); next.delete(soc); return next; });
      return;
    }
    setExpandedSocs((prev) => new Set(prev).add(soc));
    if (!details[soc]) {
      setLoadingSocs((prev) => new Set(prev).add(soc));
      try {
        const d = await getOccupationDetail(soc, school.name);
        setDetails((prev) => ({ ...prev, [soc]: d }));
      } catch {}
      finally { setLoadingSocs((prev) => { const next = new Set(prev); next.delete(soc); return next; }); }
    }
  }, [expandedSocs, details, school.name, preserveScroll]);

  const renderOccupationRow = useCallback((occ: ApiOccupationMatch, i: number) => (
    <OccupationRow occ={occ} i={i} school={school}
      expandedSocs={expandedSocs} details={details} loadingSocs={loadingSocs}
      onExpand={handleExpand} regionName={regionName} regionNames={regionNames} />
  ), [school, expandedSocs, details, loadingSocs, handleExpand, regionName, regionNames]);

  const occKeyExtractor = useCallback((occ: ApiOccupationMatch) => occ.soc_code, []);

  const renderInitialContent = useCallback(() => (
    overview ? (
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {allOccupations.length.toLocaleString()} occupations in {regionLabel}
        </p>
        <EntityScrollList
          items={allOccupations} initialCap={100} batchSize={100}
          columns={OCCUPATION_COLUMNS} renderRow={renderOccupationRow}
          keyExtractor={occKeyExtractor} entityName="occupations" school={school}
        />
      </div>
    ) : null
  ), [overview, allOccupations, regionLabel, renderOccupationRow, occKeyExtractor, school]);

  const renderResultsContent = useCallback((results: ApiOccupationMatch[]) => (
    <>
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
        {results.length.toLocaleString()} occupation{results.length !== 1 ? "s" : ""} found
      </p>
      <EntityScrollList
        items={results} initialCap={200} batchSize={100}
        columns={OCCUPATION_COLUMNS} renderRow={renderOccupationRow}
        keyExtractor={occKeyExtractor} entityName="occupations" school={school}
      />
    </>
  ), [renderOccupationRow, occKeyExtractor, school]);

  return (
    <QueryShell<ApiOccupationMatch>
      school={school} onBack={onBack} parentShape="tetrahedron"
      placeholder={`Ask me a question about occupations near ${school.name}.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

/* ── Occupation Row ────────────────────────────────────────────────────── */

const OccupationRow = memo(function OccupationRow({ occ, i, school, expandedSocs, details, loadingSocs, onExpand, regionName, regionNames }: {
  occ: ApiOccupationMatch; i: number; school: SchoolConfig;
  expandedSocs: Set<string>; details: Record<string, ApiOccupationDetail>;
  loadingSocs: Set<string>; onExpand: (occ: ApiOccupationMatch) => void; regionName: string; regionNames: string[];
}) {
  const isOpen = expandedSocs.has(occ.soc_code);
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.01, 0.2) }}
        onClick={() => onExpand(occ)}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr 100px 80px 110px",
          padding: "12px 16px", gap: "10px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
          border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4 }}>
          {occ.title}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "right" }}>
          {formatWage(occ.annual_wage)}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>
          {occ.annual_openings != null ? `${occ.annual_openings.toLocaleString()}/yr` : "\u2014"}
        </span>
        <span style={{
          fontFamily: FONT, fontSize: "12px", fontWeight: 500, textAlign: "right",
          color: occ.growth_rate != null ? (occ.growth_rate >= 0 ? "#4ade80" : "#f87171") : "rgba(255,255,255,0.25)",
        }}>
          {occ.growth_rate != null ? `${occ.growth_rate >= 0 ? "+" : ""}${(occ.growth_rate * 100).toFixed(1)}%` : "\u2014"}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px" }}>
              {loadingSocs.has(occ.soc_code) && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
              {details[occ.soc_code] && (() => { const detail = details[occ.soc_code]; return (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {detail.description && (
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: 0 }}>
                      {detail.description}
                    </p>
                  )}
                  {(() => {
                    const aligned = detail.skills.filter((s) => s.developed);
                    if (aligned.length === 0) return null;
                    return (
                      <div>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "4px" }}>
                          Aligned Skills ({aligned.length})
                        </span>
                        <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "10px" }}>
                          Skills this occupation requires that {school.name} courses develop.
                        </span>
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {aligned.map((skill) => (
                            <div key={skill.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                <circle cx="6" cy="6" r="5" stroke={school.brandColorLight} strokeWidth="1" />
                                <path d="M4 6l1.5 1.5L8 5" stroke={school.brandColorLight} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                              <span style={{ fontFamily: FONT, fontSize: "13px", color: school.brandColorLight }}>{skill.skill}</span>
                              {skill.courses.length > 0 && (
                                <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                                  — {skill.courses.slice(0, 3).map((c: any) => c.code).join(", ")}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                  {detail.regions.length > 0 && (() => {
                    const localRegions = detail.regions.filter((r: any) => regionNames.includes(r.region));
                    if (localRegions.length === 0) return null;
                    return (
                    <div>
                      <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "8px" }}>
                        Regional Employment
                      </span>
                      <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", lineHeight: 1.8 }}>
                        {localRegions.map((r: any) => (
                          <div key={r.region}>{r.region}: <span style={{ color: "rgba(255,255,255,0.65)", fontWeight: 500 }}>{r.employment.toLocaleString()}</span> currently employed</div>
                        ))}
                      </div>
                      <p style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)", marginTop: "8px", lineHeight: 1.5 }}>
                        Employment figures from the Centers of Excellence for Labor Market Research.
                      </p>
                    </div>
                    );
                  })()}
                </div>
              ); })()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});
