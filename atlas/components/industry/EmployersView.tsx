"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployers, getEmployerDetail, queryEmployers } from "@/lib/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const SUGGESTIONS = [
  "Healthcare employers",
  "Technology companies",
  "Employers with most skill alignment",
  "Who hires for Programming?",
  "Manufacturing sector",
];

const EMPLOYER_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "Sector", width: "180px" },
  { label: "Roles", width: "70px", align: "center" },
  { label: "Skills", width: "85px" },
];

function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function EmployersView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [employers, setEmployers] = useState<ApiEmployerMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<ApiEmployerMatch[]>([]);
  const [expandedNames, setExpandedNames] = useState<Set<string>>(new Set());
  const [employerDetails, setEmployerDetails] = useState<Record<string, ApiEmployerDetail>>({});
  const [loadingNames, setLoadingNames] = useState<Set<string>>(new Set());
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryMessage, setQueryMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const allEmployers = useMemo(
    () => [...employers].sort((a, b) => a.name.localeCompare(b.name)),
    [employers],
  );

  useEffect(() => {
    getEmployers(school.name)
      .then(setEmployers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!query.trim()) return;
    setSubmitted(true);
    setExpandedNames(new Set());
    setQueryLoading(true);
    setQueryMessage(null);
    try {
      const resp = await queryEmployers(query, school.name);
      setResults(resp.employers);
      setQueryMessage(resp.message);
    } catch (err: any) {
      setResults([]);
      setQueryMessage(err?.message || "Something went wrong. Try a different question.");
    } finally {
      setQueryLoading(false);
    }
  }, [query, school.name]);

  const handleChip = useCallback(async (text: string) => {
    setQuery(text);
    setSubmitted(true);
    setExpandedNames(new Set());
    setQueryLoading(true);
    setQueryMessage(null);
    try {
      const resp = await queryEmployers(text, school.name);
      setResults(resp.employers);
      setQueryMessage(resp.message);
    } catch (err: any) {
      setResults([]);
      setQueryMessage(err?.message || "Something went wrong. Try a different question.");
    } finally {
      setQueryLoading(false);
    }
  }, [school.name]);

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

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]); setQueryMessage(null);
    setExpandedNames(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const renderEmployerRow = useCallback((emp: ApiEmployerMatch, i: number) => (
    <EmployerRow emp={emp} i={i} school={school}
      expandedNames={expandedNames} employerDetails={employerDetails} loadingNames={loadingNames}
      onExpand={handleExpand} />
  ), [school, expandedNames, employerDetails, loadingNames, handleExpand]);

  const empKeyExtractor = useCallback((emp: ApiEmployerMatch) => emp.name, []);

  return (
    <div ref={rootRef}>
      <LeafHeader school={school} onBack={onBack} parentShape="tetrahedron" />
      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "32px 40px 80px" }}>
        {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {!submitted && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
              <RisingSun style={{ width: "90px", height: "auto" }} />
              <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center" }}>
                What&apos;s up{userName ? `, ${userName}` : ""}?
              </h1>
              <div style={{ width: "100%" }}>
                <input ref={inputRef} type="text" value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                  placeholder={`Ask me a question about employers near ${school.name}.`}
                  style={{
                    width: "100%", padding: "18px 24px", fontFamily: FONT, fontSize: "15px",
                    color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.10)", borderRadius: "16px",
                    outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
                />
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => handleChip(s)}
                    style={{
                      fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)",
                      background: "transparent", border: `1px solid ${school.brandColorLight}35`,
                      borderRadius: "100px", padding: "8px 18px", cursor: "pointer",
                      transition: "background 0.15s, color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = `${school.brandColorLight}15`; el.style.borderColor = `${school.brandColorLight}40`; el.style.color = school.brandColorLight; }}
                    onMouseLeave={(e) => { const el = e.currentTarget as HTMLElement; el.style.background = "transparent"; el.style.borderColor = `${school.brandColorLight}35`; el.style.color = "rgba(255,255,255,0.55)"; }}
                  >{s}</button>
                ))}
              </div>
            </div>

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
          </motion.div>
        )}

        {/* ── Results State ── */}
        {submitted && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input ref={inputRef} type="text" value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                placeholder={`Ask me a question about employers near ${school.name}.`}
                style={{
                  flex: 1, padding: "14px 20px", fontFamily: FONT, fontSize: "14px",
                  color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                  outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
              />
              <button onClick={handleReset}
                style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer", padding: "8px", transition: "color 0.15s" }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)"; }}
              >Clear</button>
            </div>

            {queryLoading && (
              <div style={{ display: "flex", justifyContent: "center", paddingTop: "40px" }}>
                <RisingSun style={{ width: "64px", height: "auto", opacity: 0.4 }} />
              </div>
            )}

            {!queryLoading && queryMessage && (
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
                {queryMessage}
              </p>
            )}

            {!queryLoading && (
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
            )}
          </motion.div>
        )}
      </div>
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
                  {detail.regions.length > 0 && (
                    <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
                      {detail.sector && <span style={{ color: "rgba(255,255,255,0.55)", fontWeight: 500 }}>{detail.sector}</span>}
                      {detail.sector && detail.regions.length > 0 && " · "}
                      {detail.regions.join(" · ")}
                    </div>
                  )}
                  {detail.description && (
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: 0 }}>
                      {detail.description}
                    </p>
                  )}
                  {detail.occupations.map((occ: any) => {
                    const aligned = (occ.skills || []).filter((s: any) => s.developed);
                    const gaps = (occ.skills || []).filter((s: any) => !s.developed);
                    return (
                      <div key={occ.soc_code} style={{
                        background: "rgba(255,255,255,0.03)", borderRadius: "8px", padding: "16px 18px",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: aligned.length > 0 || gaps.length > 0 ? "12px" : 0 }}>
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
                            {aligned.length}/{occ.skills?.length || 0} skills
                          </Badge>
                        </div>

                        {aligned.length > 0 && (
                          <div style={{ display: "flex", flexDirection: "column", gap: "5px", marginBottom: gaps.length > 0 ? "10px" : 0 }}>
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

                        {gaps.length > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
                            {gaps.map((skill: any) => (
                              <span key={skill.skill} style={{
                                fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)",
                                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                                borderRadius: "100px", padding: "3px 10px",
                              }}>{skill.skill}</span>
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

