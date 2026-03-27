"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployers, getEmployerDetail } from "@/lib/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const SUGGESTIONS = [
  "Healthcare employers",
  "Technology companies",
  "Highest skill alignment",
  "Manufacturing employers",
  "Who hires for Programming?",
];

function filterEmployers(query: string, employers: ApiEmployerMatch[]): ApiEmployerMatch[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];
  if (q.includes("highest") && (q.includes("alignment") || q.includes("skill")))
    return [...employers].sort((a, b) => b.matching_skills - a.matching_skills);
  // Sector filter
  const sectorMatch = employers.filter((e) => (e.sector || "").toLowerCase().includes(q));
  if (sectorMatch.length > 0 && sectorMatch.length < employers.length) return sectorMatch;
  // Skill filter ("who hires for X")
  const skillQ = q.replace("who hires for", "").replace("?", "").trim();
  if (skillQ !== q) {
    const skillMatch = employers.filter((e) => e.skills.some((s) => s.toLowerCase().includes(skillQ)));
    if (skillMatch.length > 0) return skillMatch;
  }
  // Name filter
  const nameMatch = employers.filter((e) => e.name.toLowerCase().includes(q));
  if (nameMatch.length > 0) return nameMatch;
  // Broad: name or sector or skills
  return employers.filter((e) =>
    e.name.toLowerCase().includes(q) ||
    (e.sector || "").toLowerCase().includes(q) ||
    e.skills.some((s) => s.toLowerCase().includes(q))
  );
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function EmployersView({ school, onBack }: Props) {
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
  const inputRef = useRef<HTMLInputElement>(null);

  const allEmployers = [...employers].sort((a, b) => a.name.localeCompare(b.name));

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

  const handleSubmit = useCallback(() => {
    if (!query.trim()) return;
    setResults(filterEmployers(query, allEmployers));
    setSubmitted(true);
    setExpandedNames(new Set());
  }, [query, allEmployers]);

  const handleChip = useCallback((text: string) => {
    setQuery(text);
    setResults(filterEmployers(text, allEmployers));
    setSubmitted(true);
    setExpandedNames(new Set());
  }, [allEmployers]);

  const handleExpand = useCallback(async (emp: ApiEmployerMatch) => {
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
  }, [expandedNames, employerDetails, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]);
    setExpandedNames(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="dodecahedron" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>
        {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "70px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {/* ── Initial State ── */}
        {!submitted && !loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
            style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
              <RisingSun style={{ width: "70px", height: "auto" }} />
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
              <EmployerList
                employers={allEmployers} initialCap={50} school={school}
                expandedNames={expandedNames} employerDetails={employerDetails} loadingNames={loadingNames}
                onExpand={handleExpand}
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

            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
              {results.length} employer{results.length !== 1 ? "s" : ""} found
            </p>

            <EmployerList
              employers={results} initialCap={50} school={school}
              expandedNames={expandedNames} employerDetails={employerDetails} loadingNames={loadingNames}
              onExpand={handleExpand}
            />
          </motion.div>
        )}
      </div>
    </>
  );
}

/* ── Employer List ─────────────────────────────────────────────────────── */

function EmployerList({
  employers, initialCap, school, expandedNames, employerDetails, loadingNames, onExpand,
}: {
  employers: ApiEmployerMatch[];
  initialCap: number;
  school: SchoolConfig;
  expandedNames: Set<string>;
  employerDetails: Record<string, ApiEmployerDetail>;
  loadingNames: Set<string>;
  onExpand: (emp: ApiEmployerMatch) => void;
}) {
  const [visibleCount, setVisibleCount] = useState(initialCap);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setVisibleCount(initialCap); }, [employers, initialCap]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && visibleCount < employers.length) {
        setVisibleCount((prev) => Math.min(prev + 50, employers.length));
      }
    }, { threshold: 0.1 });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [visibleCount, employers.length]);

  const visible = employers.slice(0, visibleCount);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr 120px 70px 85px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Sector</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "center" }}>Roles</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Skills</span>
      </div>

      {visible.map((emp, i) => {
        const isOpen = expandedNames.has(emp.name);
        const detail = employerDetails[emp.name];
        const isLoading = loadingNames.has(emp.name);
        return (
          <div key={emp.name}>
            <motion.button
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(i * 0.015, 0.3) }}
              onClick={() => onExpand(emp)}
              style={{
                width: "100%", textAlign: "left",
                display: "grid", gridTemplateColumns: "24px 1fr 120px 70px 85px",
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
                        {/* Regions */}
                        {detail.regions.length > 0 && (
                          <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
                            {detail.sector && <span style={{ color: "rgba(255,255,255,0.55)", fontWeight: 500 }}>{detail.sector}</span>}
                            {detail.sector && detail.regions.length > 0 && " · "}
                            {detail.regions.join(" · ")}
                          </div>
                        )}
                        {/* Description */}
                        {detail.description && (
                          <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: 0 }}>
                            {detail.description}
                          </p>
                        )}

                        {/* Occupations */}
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
      })}

      {visibleCount < employers.length && (
        <div ref={sentinelRef} style={{ padding: "14px", textAlign: "center" }}>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
            Showing {visibleCount} of {employers.length} employers...
          </p>
        </div>
      )}
      {employers.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No employers match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
