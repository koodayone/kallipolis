"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { getEmployers, getEmployerDetail, queryEmployers } from "@/college-atlas/employers/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/college-atlas/employers/api";
import Badge from "@/ui/Badge";
import EntityScrollList from "@/ui/EntityScrollList";
import type { Column } from "@/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/ui/QueryShell";
import DataCitation from "@/ui/DataCitation";
import RequiredSkillsList from "@/ui/RequiredSkillsList";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const EXAMPLES = [
  "Employers with the strongest skill alignment",
  "Who hires for roles our students are prepared for?",
  "Largest employers in our region by sector",
];

const EMPLOYER_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "SWP Sector", width: "280px" },
  { label: "Roles", width: "70px", align: "center" },
  { label: "Skills", width: "85px" },
];

type Props = { school: SchoolConfig; onBack: () => void };

export default function EmployersView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [employers, setEmployers] = useState<ApiEmployerMatch[]>([]);
  const [expandedNames, setExpandedNames] = useState<Set<string>>(new Set());
  const [employerDetails, setEmployerDetails] = useState<Record<string, ApiEmployerDetail>>({});
  const [loadingNames, setLoadingNames] = useState<Set<string>>(new Set());

  const allEmployers = useMemo(
    () => [...employers].sort((a, b) => a.name.localeCompare(b.name)),
    [employers],
  );



  const loadInitialData = useCallback(async () => {
    const data = await getEmployers(school.name);
    setEmployers(data);
  }, [school.name]);

  const queryFn = useCallback(async (query: string, college: string) => {
    const resp = await queryEmployers(query, college);
    return { items: resp.employers, message: resp.message };
  }, []);

  const onQueryStart = useCallback(() => { setExpandedNames(new Set()); }, []);
  const onReset = useCallback(() => { setExpandedNames(new Set()); }, []);

  const handleExpand = useCallback(async (emp: ApiEmployerMatch) => {
    const scrollEl = findScrollParent(rootRef.current);
    const savedScroll = scrollEl?.scrollTop ?? 0;
    const restoreScroll = () => requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = savedScroll; });

    const name = emp.name;
    if (expandedNames.has(name)) {
      setExpandedNames((prev) => { const next = new Set(prev); next.delete(name); return next; });
      restoreScroll();
      return;
    }
    setExpandedNames((prev) => new Set(prev).add(name));
    restoreScroll();
    if (!employerDetails[name]) {
      setLoadingNames((prev) => new Set(prev).add(name));
      try {
        const d = await getEmployerDetail(name, school.name);
        setEmployerDetails((prev) => ({ ...prev, [name]: d }));
      } catch {}
      finally { setLoadingNames((prev) => { const next = new Set(prev); next.delete(name); return next; }); }
    }
  }, [expandedNames, employerDetails, school.name]);

  const renderEmployerRow = useCallback((emp: ApiEmployerMatch, i: number) => (
    <EmployerRow emp={emp} i={i} school={school}
      expandedNames={expandedNames} employerDetails={employerDetails} loadingNames={loadingNames}
      onExpand={handleExpand} />
  ), [school, expandedNames, employerDetails, loadingNames, handleExpand]);

  const empKeyExtractor = useCallback((emp: ApiEmployerMatch) => emp.name, []);

  const renderInitialContent = useCallback(() => (
    <div style={{ marginTop: "16px" }}>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {allEmployers.length} employers
      </p>
      <EntityScrollList
        items={allEmployers} initialCap={50} batchSize={50}
        columns={EMPLOYER_COLUMNS} renderRow={renderEmployerRow}
        keyExtractor={empKeyExtractor} entityName="employers" school={school}
      />
    </div>
  ), [allEmployers, renderEmployerRow, empKeyExtractor, school]);

  const renderResultsContent = useCallback((results: ApiEmployerMatch[]) => (
    <>
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
        {results.length} employer{results.length !== 1 ? "s" : ""} found
      </p>
      <EntityScrollList
        items={results} initialCap={50} batchSize={50}
        columns={EMPLOYER_COLUMNS} renderRow={renderEmployerRow}
        keyExtractor={empKeyExtractor} entityName="employers" school={school}
      />
    </>
  ), [renderEmployerRow, empKeyExtractor, school]);

  return (
    <QueryShell<ApiEmployerMatch>
      school={school} formName="Employers" onBack={onBack}
      placeholder={`Ask me a question about employers near ${school.name}.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

/* ── Sector Cell ──────────────────────────────────────────────────────── */

// Renders the employer's primary SWP sector. When the employer's swp_sectors
// intersects the college region's priority sectors, the cell shows a small
// brand-colored dot to mark it as a priority-aligned partnership candidate.
// Falls back to the NAICS-2 display label (emp.sector) when swp_sectors is
// empty — these are out-of-scope or name-drifted records that keep the
// older label until a re-scrape regenerates their canonical tags.
function SectorCell({ swpSectors, prioritySectorsMatched, fallback, brandColor }: {
  swpSectors: string[];
  prioritySectorsMatched: string[];
  fallback: string | null;
  brandColor: string;
}) {
  const primary = swpSectors[0];
  const isPriority = prioritySectorsMatched.length > 0;
  const label = primary || fallback || "—";
  return (
    <span style={{
      fontFamily: FONT, fontSize: "12px",
      color: primary ? "rgba(255,255,255,0.55)" : "rgba(255,255,255,0.3)",
      display: "flex", alignItems: "center", gap: "6px",
      overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis",
    }}>
      {isPriority && (
        <span
          title={`Regional priority: ${prioritySectorsMatched.join(", ")}`}
          style={{
            display: "inline-block", width: "6px", height: "6px",
            borderRadius: "50%", background: brandColor, flexShrink: 0,
          }}
        />
      )}
      <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{label}</span>
    </span>
  );
}


/* ── Employer Row ─────────────────────────────────────────────────────── */

const EmployerRow = memo(function EmployerRow({ emp, i, school, expandedNames, employerDetails, loadingNames, onExpand }: {
  emp: ApiEmployerMatch; i: number; school: SchoolConfig;
  expandedNames: Set<string>; employerDetails: Record<string, ApiEmployerDetail>;
  loadingNames: Set<string>; onExpand: (emp: ApiEmployerMatch) => void;
}) {
  const isOpen = expandedNames.has(emp.name);
  const detail = employerDetails[emp.name];
  const isLoading = loadingNames.has(emp.name);
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.015, 0.3) }}
        onClick={() => onExpand(emp)}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr 280px 70px 85px",
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
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
          {emp.name}
        </span>
        <SectorCell
          swpSectors={emp.swp_sectors}
          prioritySectorsMatched={emp.priority_sectors_matched}
          fallback={emp.sector}
          brandColor={school.brandColorLight}
        />
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", display: "flex", justifyContent: "center" }}>
          {emp.occupations.length}
        </span>
        <Badge style={{
          color: school.brandColorLight,
          background: `${school.brandColorLight}20`,
          border: `1px solid ${school.brandColorLight}30`,
          fontSize: "11px", whiteSpace: "nowrap",
        }}>
          {emp.matching_skills} skills
        </Badge>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px" }}>
              {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
              {detail && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {detail.description && (
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: 0 }}>
                      {detail.description}
                    </p>
                  )}
                  {detail.website && (
                    <a
                      href={detail.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "3px 10px", borderRadius: "100px", fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase" as const, color: "rgba(255,255,255,0.5)", background: "transparent", border: "1px solid rgba(255,255,255,0.12)", textDecoration: "none", transition: "border-color 0.15s, color 0.15s", width: "fit-content" }}
                      onMouseEnter={e => { const el = e.currentTarget; el.style.borderColor = `${school.brandColorLight}4d`; el.style.color = school.brandColorLight; el.querySelectorAll("svg").forEach(s => s.style.stroke = school.brandColorLight); }}
                      onMouseLeave={e => { const el = e.currentTarget; el.style.borderColor = "rgba(255,255,255,0.12)"; el.style.color = "rgba(255,255,255,0.5)"; el.querySelectorAll("svg").forEach(s => s.style.stroke = "rgba(255,255,255,0.4)"); }}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ stroke: "rgba(255,255,255,0.4)", transition: "stroke 0.15s", flexShrink: 0 }} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                      </svg>
                      Employer Home Page
                    </a>
                  )}
                  {detail.occupations.length > 0 && (
                    <div style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", marginTop: "4px" }}>
                      Employer Occupations ({detail.occupations.length})
                    </div>
                  )}
                  {detail.occupations.map((occ) => {
                    const aligned = (occ.skills || []).filter((s) => s.developed);
                    return (
                      <div key={occ.soc_code} style={{
                        background: "rgba(255,255,255,0.03)", borderRadius: "8px", padding: "16px 18px",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                          <div style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 500, color: "#f0eef4" }}>
                            {occ.title}
                          </div>
                          {occ.annual_wage && (
                            <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.55)", whiteSpace: "nowrap", marginLeft: "12px" }}>
                              ${occ.annual_wage.toLocaleString()} annual
                            </span>
                          )}
                        </div>

                        {occ.description && (
                          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", lineHeight: 1.5, margin: "8px 0 0" }}>
                            {occ.description}
                          </p>
                        )}

                        {aligned.length > 0 && (
                          <div style={{ marginTop: "12px" }}>
                            <RequiredSkillsList
                              skills={aligned}
                              brandColor={school.brandColorLight}
                              collegeName={school.name}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                  <DataCitation source="California Employment Development Department" />
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});
