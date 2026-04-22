"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo, Fragment } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { getEmployers, getEmployerDetail, queryEmployers } from "@/college-atlas/employers/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/college-atlas/employers/api";
import Badge from "@/ui/Badge";
import QueryShell, { findScrollParent } from "@/ui/QueryShell";
import DataCitation from "@/ui/DataCitation";
import RequiredSkillsList from "@/ui/RequiredSkillsList";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const EXAMPLES = [
  "Employers with the strongest skill alignment",
  "Who hires for roles our students are prepared for?",
  "Largest employers in our region by sector",
];

const UNCLASSIFIED = "Unclassified";

type Props = { school: SchoolConfig; onBack: () => void };

export default function EmployersView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [employers, setEmployers] = useState<ApiEmployerMatch[]>([]);
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());
  const [expandedNames, setExpandedNames] = useState<Set<string>>(new Set());
  const [employerDetails, setEmployerDetails] = useState<Record<string, ApiEmployerDetail>>({});
  const [loadingNames, setLoadingNames] = useState<Set<string>>(new Set());

  const loadInitialData = useCallback(async () => {
    const data = await getEmployers(school.name);
    setEmployers(data);
  }, [school.name]);

  const queryFn = useCallback(async (query: string, college: string) => {
    const resp = await queryEmployers(query, college);
    return { items: resp.employers, message: resp.message };
  }, []);

  const onQueryStart = useCallback(() => {
    setExpandedNames(new Set());
    setExpandedSectors(new Set());
  }, []);
  const onReset = useCallback(() => {
    setExpandedNames(new Set());
    setExpandedSectors(new Set());
  }, []);

  const preserveScroll = useCallback(() => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  const handleSectorToggle = useCallback((sector: string) => {
    preserveScroll();
    setExpandedSectors((prev) => {
      const next = new Set(prev);
      if (next.has(sector)) next.delete(sector); else next.add(sector);
      return next;
    });
  }, [preserveScroll]);

  const handleExpand = useCallback(async (emp: ApiEmployerMatch) => {
    preserveScroll();
    const name = emp.name;
    if (expandedNames.has(name)) {
      setExpandedNames((prev) => { const next = new Set(prev); next.delete(name); return next; });
      return;
    }
    setExpandedNames((prev) => new Set(prev).add(name));
    if (!employerDetails[name]) {
      setLoadingNames((prev) => new Set(prev).add(name));
      try {
        const d = await getEmployerDetail(name, school.name);
        setEmployerDetails((prev) => ({ ...prev, [name]: d }));
      } catch {}
      finally { setLoadingNames((prev) => { const next = new Set(prev); next.delete(name); return next; }); }
    }
  }, [expandedNames, employerDetails, school.name, preserveScroll]);

  const renderEmployerRow = useCallback((emp: ApiEmployerMatch, i: number) => (
    <EmployerRow emp={emp} i={i} school={school}
      expandedNames={expandedNames} employerDetails={employerDetails} loadingNames={loadingNames}
      onExpand={handleExpand} />
  ), [school, expandedNames, employerDetails, loadingNames, handleExpand]);

  const renderInitialContent = useCallback(() => (
    <SectorGroupedList
      employers={employers}
      school={school}
      expandedSectors={expandedSectors}
      onSectorToggle={handleSectorToggle}
      renderEmployerRow={renderEmployerRow}
      summaryLine={`${employers.length} employers`}
    />
  ), [employers, school, expandedSectors, handleSectorToggle, renderEmployerRow]);

  const renderSearchContent = useCallback((q: string) => {
    const lower = q.toLowerCase();
    const filtered = employers.filter(e =>
      e.name.toLowerCase().includes(lower) ||
      e.swp_sectors.some(s => s.toLowerCase().includes(lower))
    );
    if (filtered.length === 0) {
      return (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No results found.
        </p>
      );
    }
    const allSectors = new Set(filtered.map(e => e.swp_sectors[0] ?? UNCLASSIFIED));
    return (
      <SectorGroupedList
        employers={filtered}
        school={school}
        expandedSectors={allSectors}
        onSectorToggle={handleSectorToggle}
        renderEmployerRow={renderEmployerRow}
        summaryLine={`${filtered.length} employer${filtered.length !== 1 ? "s" : ""}`}
      />
    );
  }, [employers, school, handleSectorToggle, renderEmployerRow]);

  const renderResultsContent = useCallback((results: ApiEmployerMatch[]) => (
    <div>
      <div style={{
        display: "grid", gridTemplateColumns: "20px 1fr 70px 85px",
        padding: "10px 16px 10px 44px", gap: "10px", alignItems: "center",
        borderBottom: "1px solid rgba(255,255,255,0.04)",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>
          Employer
        </span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "center" }}>
          Roles
        </span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>
          Skills
        </span>
      </div>
      {results.map((emp, i) => renderEmployerRow(emp, i))}
    </div>
  ), [school, renderEmployerRow]);

  return (
    <QueryShell<ApiEmployerMatch>
      school={school} formName="Employers" onBack={onBack}
      placeholder={`Ask me a question about employers near ${school.name}.`}
      examples={EXAMPLES} queryFn={queryFn} loadInitialData={loadInitialData}
      renderInitialContent={renderInitialContent} renderResultsContent={renderResultsContent}
      renderSearchContent={renderSearchContent}
      onQueryStart={onQueryStart} onReset={onReset} rootRef={rootRef}
    />
  );
}

/* ── Sector Grouped List ──────────────────────────────────────────────── */

// Priority set is derived from the union of every employer's
// priority_sectors_matched: a region's priority sector is only surfaced here
// if at least one employer in this response holds it. Priority sectors with
// zero employers would need a second API call to be identified, and every
// priority sector for the preview colleges has at least one member, so we
// accept the limitation rather than plumb a new endpoint.
function SectorGroupedList({
  employers, school, expandedSectors, onSectorToggle, renderEmployerRow, summaryLine,
}: {
  employers: ApiEmployerMatch[];
  school: SchoolConfig;
  expandedSectors: Set<string>;
  onSectorToggle: (sector: string) => void;
  renderEmployerRow: (emp: ApiEmployerMatch, i: number) => React.ReactNode;
  summaryLine: string;
}) {
  const { sectors, groups, prioritySet } = useMemo(() => {
    const groups: Record<string, ApiEmployerMatch[]> = {};
    const prioritySet = new Set<string>();
    for (const emp of employers) {
      const key = emp.swp_sectors[0] ?? UNCLASSIFIED;
      (groups[key] ??= []).push(emp);
      for (const p of emp.priority_sectors_matched) prioritySet.add(p);
    }
    for (const k of Object.keys(groups)) {
      groups[k].sort((a, b) => b.matching_skills - a.matching_skills);
    }
    const sectors = Object.keys(groups).sort((a, b) => {
      if (a === UNCLASSIFIED) return 1;
      if (b === UNCLASSIFIED) return -1;
      return a.localeCompare(b);
    });
    return { sectors, groups, prioritySet };
  }, [employers]);

  if (employers.length === 0) {
    return (
      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
        No employers match that query. Try a different question.
      </p>
    );
  }

  return (
    <div style={{ marginTop: "16px" }}>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {summaryLine}
      </p>
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr auto",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "10px", fontWeight: 600,
            letterSpacing: "0.1em", textTransform: "uppercase",
            color: school.brandColorLight, opacity: 0.6,
          }}>
            Sector
          </span>
          {prioritySet.size > 0 && (
            <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
              <span style={{
                width: "6px", height: "6px", borderRadius: "50%",
                background: school.brandColorLight, opacity: 0.7,
              }} />
              <span style={{
                fontFamily: FONT, fontSize: "9px", fontWeight: 500,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: school.brandColorLight, opacity: 0.4,
              }}>
                Regional priority
              </span>
            </span>
          )}
        </span>
        <span style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: school.brandColorLight, opacity: 0.6,
          textAlign: "right",
        }}>
          Employers
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {sectors.map((sector, idx) => (
          <SectorGroup
            key={sector}
            sector={sector}
            employers={groups[sector]}
            index={idx}
            isOpen={expandedSectors.has(sector)}
            isPriority={prioritySet.has(sector)}
            brandColor={school.brandColorLight}
            onToggle={() => onSectorToggle(sector)}
            renderEmployerRow={renderEmployerRow}
          />
        ))}
      </div>
    </div>
  );
}

/* ── Sector Group ─────────────────────────────────────────────────────── */

function SectorGroup({
  sector, employers, index, isOpen, isPriority, brandColor, onToggle, renderEmployerRow,
}: {
  sector: string;
  employers: ApiEmployerMatch[];
  index: number;
  isOpen: boolean;
  isPriority: boolean;
  brandColor: string;
  onToggle: () => void;
  renderEmployerRow: (emp: ApiEmployerMatch, i: number) => React.ReactNode;
}) {
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  const count = employers.length;
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={onToggle}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr auto",
          padding: "18px 16px", gap: "12px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.035)",
          border: "none", borderBottom: `1px solid ${isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.05)"}`,
          borderTop: isOpen ? `2px solid ${brandColor}80` : "2px solid transparent",
          cursor: "pointer", transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.055)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.035)"; }}
      >
        <svg width="14" height="14" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
          <span style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.98)",
            lineHeight: 1.4,
          }}>
            {sector}
          </span>
          {isPriority && (
            <span
              title="Regional priority sector"
              style={{
                display: "inline-block", width: "7px", height: "7px",
                borderRadius: "50%", background: brandColor, flexShrink: 0,
                boxShadow: `0 0 6px ${brandColor}80`,
              }}
            />
          )}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)" }}>
          {count} {count === 1 ? "employer" : "employers"}
        </span>
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
            <div>
              <div style={{
                display: "grid", gridTemplateColumns: "20px 1fr 70px 85px",
                padding: "10px 16px 10px 44px", gap: "10px", alignItems: "center",
                borderBottom: "1px solid rgba(255,255,255,0.04)",
              }}>
                <span />
                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>
                  Employer
                </span>
                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, textAlign: "center" }}>
                  Roles
                </span>
                <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>
                  Skills
                </span>
              </div>
              {employers.map((emp, i) => (
                <Fragment key={emp.name}>{renderEmployerRow(emp, i)}</Fragment>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
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
          display: "grid", gridTemplateColumns: "20px 1fr 70px 85px",
          padding: "10px 16px 10px 44px", gap: "10px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
          border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 400, color: "rgba(255,255,255,0.72)" }}>
          {emp.name}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.35)", display: "flex", justifyContent: "center" }}>
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
