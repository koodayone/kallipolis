"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { getEmployers, getEmployerDetail, queryEmployers } from "@/college-atlas/employers/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/college-atlas/employers/api";
import { TopGroupBlock } from "@/college-atlas/occupations/OccupationRow";
import QueryShell, { findScrollParent } from "@/ui/QueryShell";
import EntityScrollList, { type Column } from "@/ui/EntityScrollList";
import DataCitation from "@/ui/DataCitation";

// Visible cap on TOP-groups within a single occupation's curriculum
// alignment block. Mirrors the OccupationRow cap so the surfaces share
// the same show-all triggering behavior.
const GROUP_CAP = 4;

// Visible cap on the per-employer occupation list. Occupations are
// sorted by industry-share (BLS OEWS PCT_TOTAL for the employer's
// NAICS-4) so the top N captures the roles that matter most to the
// industry. The long tail — including unaligned roles that signal
// program-development opportunities — is one click away.
const OCCUPATION_CAP = 5;

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

// Three-column layout matching OccupationsView's pattern: structural
// label + two right-aligned integer counts. Width tuning mirrors the
// numeric columns in OCCUPATION_COLUMNS so both single-level data
// views read at the same density.
const EMPLOYER_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "Roles", width: "80px", align: "right" },
  { label: "Courses", width: "80px", align: "right" },
];

// Example queries shown as suggestions. Each demonstrates one supported
// query shape — substitution-on-sector, substitution-on-role, fixed
// flag, default-sort — teaching the grammar by example. Quoted slots
// are substitutable; unquoted phrases are fixed institutional concepts.
const EXAMPLES = [
  "Employers in 'healthcare'",
  "Employers hiring for 'software developers'",
  "Employers in regional priority sectors",
  "Employers with the strongest curriculum alignment",
];

type Props = { school: SchoolConfig; onBack: () => void };

export default function EmployersView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [employers, setEmployers] = useState<ApiEmployerMatch[]>([]);
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
  }, []);
  const onReset = useCallback(() => {
    setExpandedNames(new Set());
  }, []);

  const preserveScroll = useCallback(() => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

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

  // Sort the API response alphabetically. The backend returns employers
  // ordered by `aligned_course_count DESC, name`, but the Employers node
  // is a vanilla data-shape view (mirroring the Occupations node) — the
  // user comes here to look up specific employers, not to consume an
  // editorial ranking. Alphabetical sort keeps the index browsable
  // regardless of any one column's value.
  const employersAlpha = useMemo(
    () => [...employers].sort((a, b) => a.name.localeCompare(b.name)),
    [employers],
  );

  const empKeyExtractor = useCallback((emp: ApiEmployerMatch) => emp.name, []);

  const renderInitialContent = useCallback(() => (
    <div style={{ marginTop: "16px" }}>
      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
        {employersAlpha.length.toLocaleString()} employers
      </p>
      <EntityScrollList
        items={employersAlpha} initialCap={100} batchSize={100}
        columns={EMPLOYER_COLUMNS} renderRow={renderEmployerRow}
        keyExtractor={empKeyExtractor} entityName="employers" school={school}
      />
    </div>
  ), [employersAlpha, school, renderEmployerRow, empKeyExtractor]);

  const renderSearchContent = useCallback((q: string) => {
    const lower = q.toLowerCase();
    const filtered = employersAlpha.filter(e =>
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
    return (
      <div style={{ marginTop: "16px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)", marginBottom: "12px" }}>
          {filtered.length.toLocaleString()} employer{filtered.length !== 1 ? "s" : ""}
        </p>
        <EntityScrollList
          items={filtered} initialCap={100} batchSize={100}
          columns={EMPLOYER_COLUMNS} renderRow={renderEmployerRow}
          keyExtractor={empKeyExtractor} entityName="employers" school={school}
        />
      </div>
    );
  }, [employersAlpha, school, renderEmployerRow, empKeyExtractor]);

  const renderResultsContent = useCallback((results: ApiEmployerMatch[]) => (
    <EntityScrollList
      items={results} initialCap={200} batchSize={100}
      columns={EMPLOYER_COLUMNS} renderRow={renderEmployerRow}
      keyExtractor={empKeyExtractor} entityName="employers" school={school}
    />
  ), [renderEmployerRow, empKeyExtractor, school]);

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

/* (FlatEmployerList removed — the Employers view now uses EntityScrollList,
    the same shared list component the Occupations view uses. Both views
    are vanilla data-shape surfaces; sharing the list primitive keeps
    them visually consistent and removes a duplicate header definition.) */

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
          display: "grid", gridTemplateColumns: "24px 1fr 80px 80px",
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
          {emp.name}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          {emp.occupations.length.toLocaleString()}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          {emp.aligned_course_count.toLocaleString()}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.045)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}
          >
            <div style={{ padding: "16px 20px 24px 50px" }}>
              {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
              {detail && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {detail.naics4 && (
                    <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
                      <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 500, letterSpacing: "0.05em", color: "rgba(255,255,255,0.4)", fontVariantNumeric: "tabular-nums" }}>
                        NAICS {detail.naics4}
                      </span>
                      {detail.naics_title && (
                        <>
                          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>·</span>
                          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.7)" }}>
                            {detail.naics_title}
                          </span>
                        </>
                      )}
                    </div>
                  )}
                  {detail.description && (
                    <div>
                      <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.7, display: "block", marginBottom: "10px" }}>
                        Description
                      </span>
                      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: 0 }}>
                        {detail.description}
                      </p>
                    </div>
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
                    <EmployerOccupationsList
                      occupations={detail.occupations}
                      naics4={detail.naics4}
                      brandColor={school.brandColorLight}
                    />
                  )}
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

/* ── Employer Occupations List ────────────────────────────────────────── */

type ApiEmployerOccupation = ApiEmployerDetail["occupations"][number];

function EmployerOccupationsList({ occupations, naics4, brandColor }: {
  occupations: ApiEmployerOccupation[]; naics4: string | null; brandColor: string;
}) {
  // Filter to roles where the college actually has at least one course
  // that PREPARES_FOR the SOC. The Employers node is a data-shape view
  // for browsing employer-curriculum alignment at this college; rows
  // with `aligned_course_count === 0` carry no signal for that purpose
  // (one side of the join is empty). Surfacing alignment gaps is a
  // separate domain space the ontology can support later, but it
  // doesn't belong in this view at the preview/pilot stage.
  const aligned = occupations.filter(o => o.aligned_course_count > 0);
  const visible = aligned.slice(0, OCCUPATION_CAP);
  const isCapped = aligned.length > OCCUPATION_CAP;
  const shownCount = visible.length;

  // Empty case — no aligned roles for this employer at this college.
  // Hiding the panel entirely is itself the signal; an empty
  // "Employer Occupations (0)" header would just be visual noise.
  if (aligned.length === 0) return null;

  return (
    <div style={{ marginTop: "4px" }}>
      <div style={{ marginBottom: "12px" }}>
        <div style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: brandColor, opacity: 0.7,
        }}>
          Employer Occupations ({aligned.length})
        </div>
        {naics4 && (
          <div style={{
            fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)",
            marginTop: "4px", lineHeight: 1.5,
          }}>
            {isCapped ? `Top ${shownCount} occupations` : `${shownCount} occupation${shownCount === 1 ? "" : "s"}`} sorted by share of employment in NAICS sector {naics4}.
          </div>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        {visible.map((occ) => (
          <EmployerOccupationRow key={occ.soc_code} occ={occ} brandColor={brandColor} />
        ))}
      </div>
    </div>
  );
}

/* ── Employer Occupation Row (collapsible, editorial) ─────────────────── */

function EmployerOccupationRow({ occ, brandColor }: { occ: ApiEmployerOccupation; brandColor: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [showAllGroups, setShowAllGroups] = useState(false);
  const groups = occ.aligned_top_groups ?? [];
  const visibleGroups = showAllGroups ? groups : groups.slice(0, GROUP_CAP);
  const hiddenGroups = showAllGroups ? [] : groups.slice(GROUP_CAP);
  const isCapped = hiddenGroups.length > 0;
  const courseCount = occ.aligned_course_count;

  return (
    <div>
      <button
        onClick={() => setIsOpen(o => !o)}
        style={{
          width: "100%", textAlign: "left",
          display: "flex", alignItems: "baseline", gap: "12px",
          padding: "11px 4px 11px 4px",
          background: isOpen ? "rgba(255,255,255,0.04)" : "transparent",
          border: "none",
          cursor: "pointer", transition: "background 0.15s",
          borderRadius: "4px",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.025)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none"
          style={{
            transform: isOpen ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            flexShrink: 0, marginLeft: "4px",
            position: "relative", top: "1px",
          }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.82)", flex: 1, lineHeight: 1.45 }}>
          {occ.title}
        </span>
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: "8px", flexShrink: 0, paddingRight: "4px" }}>
          <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", whiteSpace: "nowrap", minWidth: "84px", textAlign: "right" }}>
            {occ.annual_wage ? `$${occ.annual_wage.toLocaleString()}/yr` : "—"}
          </span>
          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>·</span>
          <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.55)", whiteSpace: "nowrap", minWidth: "68px", textAlign: "right" }}>
            {courseCount} course{courseCount === 1 ? "" : "s"}
          </span>
        </span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "14px 20px 18px 38px" }}>
              {occ.soc_code && (
                <div style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 500, letterSpacing: "0.05em", color: "rgba(255,255,255,0.4)", fontVariantNumeric: "tabular-nums", marginBottom: "10px" }}>
                  SOC {occ.soc_code}
                </div>
              )}
              {occ.description && (
                <div style={{ marginBottom: "14px" }}>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.7, display: "block", marginBottom: "10px" }}>
                    Description
                  </span>
                  <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: 0 }}>
                    {occ.description}
                  </p>
                </div>
              )}
              {groups.length > 0 ? (
                <div>
                  <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.7, display: "block", marginBottom: "10px" }}>
                    Curriculum Alignment
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {visibleGroups.map((group) => (
                      <TopGroupBlock key={group.top_code || "unknown"} group={group} brandColor={brandColor} />
                    ))}
                    {showAllGroups && hiddenGroups.map((group, i) => (
                      <motion.div
                        key={group.top_code || `hidden-${i}`}
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.18, delay: Math.min(i * 0.04, 0.2) }}
                      >
                        <TopGroupBlock group={group} brandColor={brandColor} />
                      </motion.div>
                    ))}
                  </div>
                  {isCapped && (
                    <button
                      onClick={() => setShowAllGroups(true)}
                      style={{
                        fontFamily: FONT, fontSize: "11px", fontWeight: 500,
                        color: brandColor, opacity: 0.65,
                        background: "transparent", border: "none",
                        padding: "10px 8px 0 0",
                        cursor: "pointer", textAlign: "left",
                        transition: "opacity 0.15s",
                      }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.65"; }}
                    >
                      Show all {occ.aligned_program_area_count} program areas
                    </button>
                  )}
                </div>
              ) : (
                <div style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", fontStyle: "italic" }}>
                  No curriculum alignment at this college.
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
