"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployers, getEmployerDetail, queryEmployers } from "@/lib/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/lib/api";
import Badge from "@/components/ui/Badge";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import QueryShell, { findScrollParent } from "@/components/ui/QueryShell";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const EXAMPLES = [
  "Employers with the strongest skill alignment",
  "Who hires for roles our students are prepared for?",
  "Largest employers in our region by sector",
];

const EMPLOYER_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "Sector", width: "180px" },
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
      school={school} onBack={onBack} parentShape="tetrahedron"
      placeholder={`Ask me a question about employers near ${school.name}.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
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
          display: "grid", gridTemplateColumns: "24px 1fr 180px 70px 85px",
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
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
          {emp.sector || "—"}
        </span>
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
                  {detail.occupations.map((occ: any) => {
                    const aligned = (occ.skills || []).filter((s: any) => s.developed);
                    return (
                      <div key={occ.soc_code} style={{
                        background: "rgba(255,255,255,0.03)", borderRadius: "8px", padding: "16px 18px",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: aligned.length > 0 ? "12px" : 0 }}>
                          <div>
                            <div style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 500, color: "#f0eef4" }}>
                              {occ.title}
                            </div>
                            {occ.annual_wage && (
                              <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", marginTop: "2px" }}>
                                ${occ.annual_wage.toLocaleString()} annual
                              </div>
                            )}
                          </div>
                          <Badge style={{
                            color: school.brandColorLight,
                            background: `${school.brandColorLight}20`,
                            border: `1px solid ${school.brandColorLight}30`,
                            fontSize: "11px",
                          }}>
                            {aligned.length} skills
                          </Badge>
                        </div>

                        {aligned.length > 0 && (
                          <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                            {aligned.map((skill: any) => (
                              <div key={skill.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                  <circle cx="6" cy="6" r="5" stroke={school.brandColorLight} strokeWidth="1" />
                                  <path d="M4 6l1.5 1.5L8 5" stroke={school.brandColorLight} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                                <span style={{ fontFamily: FONT, fontSize: "12px", color: school.brandColorLight }}>{skill.skill}</span>
                                {skill.courses?.length > 0 && (
                                  <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                                    — {skill.courses.slice(0, 3).map((c: any) => c.code).join(", ")}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});
