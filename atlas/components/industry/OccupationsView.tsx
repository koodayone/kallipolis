"use client";

import { useState, useCallback, useRef, useMemo } from "react";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getLaborMarketOverview, getOccupationDetail, queryOccupations } from "@/lib/api";
import type { ApiOccupationMatch, ApiLaborMarketOverview, ApiOccupationDetail } from "@/lib/api";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";
import OccupationRow from "@/components/shared/OccupationRow";

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
    <OccupationRow
      key={occ.soc_code}
      occ={occ}
      index={i}
      brandColor={school.brandColorLight}
      isOpen={expandedSocs.has(occ.soc_code)}
      onToggle={() => handleExpand(occ)}
      detail={details[occ.soc_code] ?? null}
      isLoading={loadingSocs.has(occ.soc_code)}
      regionNames={regionNames}
      collegeName={school.name}
    />
  ), [school, expandedSocs, details, loadingSocs, handleExpand, regionNames]);

  const occKeyExtractor = useCallback((occ: ApiOccupationMatch) => occ.soc_code, []);

  const renderInitialContent = useCallback(() => (
    overview ? (
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {allOccupations.length.toLocaleString()} occupations
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
      school={school} onBack={onBack} parentShape="cube"
      placeholder={`Ask me a question about occupations near ${school.name}.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

