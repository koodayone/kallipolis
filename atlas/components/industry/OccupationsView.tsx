"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getLaborMarketOverview, getOccupationDetail, queryOccupations } from "@/lib/api";
import type { ApiOccupationMatch, ApiLaborMarketOverview, ApiOccupationDetail } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function formatWage(wage: number | null): string {
  if (!wage) return "—";
  return `$${wage.toLocaleString()}`;
}

function formatJobs(n: number | null): string {
  if (!n) return "—";
  return n.toLocaleString();
}

const SUGGESTIONS = [
  "Highest paying occupations",
  "Most jobs available",
  "Software development roles",
  "Healthcare occupations",
  "Occupations requiring Data Analysis",
];

function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function OccupationsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [overview, setOverview] = useState<ApiLaborMarketOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<ApiOccupationMatch[]>([]);
  const [expandedSocs, setExpandedSocs] = useState<Set<string>>(new Set());
  const [details, setDetails] = useState<Record<string, ApiOccupationDetail>>({});
  const [loadingSocs, setLoadingSocs] = useState<Set<string>>(new Set());
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryMessage, setQueryMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const allOccupations = (overview?.regions?.flatMap((r) => r.occupations) ?? []).sort((a, b) => a.title.localeCompare(b.title));
  const regionName = overview?.regions?.[0]?.region ?? "";

  useEffect(() => {
    getLaborMarketOverview(school.name)
      .then(setOverview)
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
    setExpandedSocs(new Set());
    setQueryLoading(true);
    try {
      const resp = await queryOccupations(query, school.name);
      setResults(resp.occupations);
      setQueryMessage(resp.message);
    } catch (e: any) {
      setResults([]);
      setQueryMessage(e?.message ?? "Something went wrong. Please try again.");
    } finally {
      setQueryLoading(false);
    }
  }, [query, school.name]);

  const handleChip = useCallback(async (text: string) => {
    setQuery(text);
    setSubmitted(true);
    setExpandedSocs(new Set());
    setQueryLoading(true);
    try {
      const resp = await queryOccupations(text, school.name);
      setResults(resp.occupations);
      setQueryMessage(resp.message);
    } catch (e: any) {
      setResults([]);
      setQueryMessage(e?.message ?? "Something went wrong. Please try again.");
    } finally {
      setQueryLoading(false);
    }
  }, [school.name]);

  const handleExpand = useCallback(async (occ: ApiOccupationMatch) => {
    const scrollEl = findScrollParent(rootRef.current);
    const savedScroll = scrollEl?.scrollTop ?? 0;
    const restoreScroll = () => requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = savedScroll; });

    const soc = occ.soc_code;
    if (expandedSocs.has(soc)) {
      setExpandedSocs((prev) => { const next = new Set(prev); next.delete(soc); return next; });
      restoreScroll();
      return;
    }
    setExpandedSocs((prev) => new Set(prev).add(soc));
    restoreScroll();
    if (!details[soc]) {
      setLoadingSocs((prev) => new Set(prev).add(soc));
      try {
        const d = await getOccupationDetail(soc, school.name);
        setDetails((prev) => ({ ...prev, [soc]: d }));
      } catch {}
      finally { setLoadingSocs((prev) => { const next = new Set(prev); next.delete(soc); return next; }); }
    }
  }, [expandedSocs, details, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]); setQueryMessage(null);
    setExpandedSocs(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  return (
    <div ref={rootRef}>
      <LeafHeader school={school} onBack={onBack} parentShape="tetrahedron" />
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
        {!submitted && !loading && overview && (
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
                  placeholder={`Ask me a question about occupations near ${school.name}.`}
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
                {allOccupations.length.toLocaleString()} occupations in {regionName}
              </p>
              <OccupationList
                occupations={allOccupations} initialCap={100} school={school}
                expandedSocs={expandedSocs} details={details} loadingSocs={loadingSocs}
                onExpand={handleExpand} regionName={regionName}
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
                placeholder={`Ask me a question about occupations near ${school.name}.`}
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
                <RisingSun style={{ width: "50px", height: "auto", opacity: 0.4 }} />
              </div>
            )}

            {!queryLoading && queryMessage && (
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>{queryMessage}</p>
            )}

            {!queryLoading && (
              <>
                <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
                  {results.length.toLocaleString()} occupation{results.length !== 1 ? "s" : ""} found
                </p>

                <OccupationList
                  occupations={results} initialCap={200} school={school}
                  expandedSocs={expandedSocs} details={details} loadingSocs={loadingSocs}
                  onExpand={handleExpand} regionName={regionName}
                />
              </>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}

/* ── Occupation Row ────────────────────────────────────────────────────── */

function OccupationRow({ occ, i, school, expandedSocs, details, loadingSocs, onExpand, regionName }: {
  occ: ApiOccupationMatch; i: number; school: SchoolConfig;
  expandedSocs: Set<string>; details: Record<string, ApiOccupationDetail>;
  loadingSocs: Set<string>; onExpand: (occ: ApiOccupationMatch) => void; regionName: string;
}) {
  const isOpen = expandedSocs.has(occ.soc_code);
  return (
    <div>
      <motion.button
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: Math.min(i * 0.01, 0.2) }}
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
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px" }}>
              {loadingSocs.has(occ.soc_code) && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}
              {details[occ.soc_code] && (() => { const detail = details[occ.soc_code]; return (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {/* Summary stats */}
                  <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
                    {occ.employment != null && (
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
                        <span style={{ color: "rgba(255,255,255,0.7)", fontWeight: 500 }}>{occ.employment.toLocaleString()}</span> jobs in region
                      </span>
                    )}
                    <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
                      <span style={{ color: school.brandColorLight, fontWeight: 500 }}>{occ.matching_skills}</span> aligned skills
                    </span>
                    {occ.education_level && (
                      <span style={{
                        fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.4)",
                        background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "100px", padding: "3px 10px",
                      }}>
                        {occ.education_level}
                      </span>
                    )}
                  </div>
                  {detail.description && (
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: 0 }}>
                      {detail.description}
                    </p>
                  )}
                  {(() => {
                    const aligned = detail.skills.filter((s) => s.developed);
                    const gaps = detail.skills.filter((s) => !s.developed);
                    return (
                      <>
                        {aligned.length > 0 && (
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
                        )}
                        {gaps.length > 0 && (
                          <div>
                            <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "10px" }}>
                              Skill Gaps ({gaps.length})
                            </span>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                              {gaps.map((skill) => (
                                <span key={skill.skill} style={{
                                  fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)",
                                  background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                                  borderRadius: "100px", padding: "4px 10px",
                                }}>{skill.skill}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    );
                  })()}
                  {detail.regions.length > 0 && (
                    <div>
                      <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "8px" }}>
                        Regional Employment
                      </span>
                      <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", lineHeight: 1.8 }}>
                        {[...detail.regions].sort((a: any, b: any) => (a.region === regionName ? -1 : b.region === regionName ? 1 : 0)).map((r: any) => (
                          <div key={r.region}>{r.region}: <span style={{ color: "rgba(255,255,255,0.65)", fontWeight: 500 }}>{r.employment.toLocaleString()}</span> currently employed</div>
                        ))}
                      </div>
                      <p style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)", marginTop: "8px", lineHeight: 1.5 }}>
                        Employment figures from the California Employment Development Department, Occupational Employment and Wage Statistics (OEWS) survey, May 2024.
                      </p>
                    </div>
                  )}
                </div>
              ); })()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ── Occupation List (shared) ──────────────────────────────────────────── */

function OccupationList({
  occupations, initialCap, school, expandedSocs, details, loadingSocs, onExpand, regionName,
}: {
  occupations: ApiOccupationMatch[];
  initialCap: number;
  school: SchoolConfig;
  expandedSocs: Set<string>;
  details: Record<string, ApiOccupationDetail>;
  loadingSocs: Set<string>;
  onExpand: (occ: ApiOccupationMatch) => void;
  regionName: string;
}) {
  const [visibleCount, setVisibleCount] = useState(initialCap);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Reset visible count when occupations change (e.g., new search)
  useEffect(() => { setVisibleCount(initialCap); }, [occupations, initialCap]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && visibleCount < occupations.length) {
        setVisibleCount((prev) => Math.min(prev + 100, occupations.length));
      }
    }, { threshold: 0.1 });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [visibleCount, occupations.length]);

  const visible = occupations.slice(0, visibleCount);

  // Column headers
  const hdrStyle: React.CSSProperties = { fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 };
  const columnHeaders = (
    <div style={{
      display: "grid", gridTemplateColumns: "24px 1fr 100px 80px 110px",
      padding: "12px 16px", gap: "10px", alignItems: "center",
    }}>
      <span />
      <span style={hdrStyle}>Occupation</span>
      <span style={{ ...hdrStyle, textAlign: "right" }}>Wage</span>
      <span style={{ ...hdrStyle, textAlign: "right" }}>Openings</span>
      <span style={{ ...hdrStyle, textAlign: "right" }}>Growth</span>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {columnHeaders}
      {visible.map((occ, i) => (
        <OccupationRow key={occ.soc_code} occ={occ} i={i} school={school}
          expandedSocs={expandedSocs} details={details} loadingSocs={loadingSocs}
          onExpand={onExpand} regionName={regionName} />
      ))}
      {visibleCount < occupations.length && (
        <div ref={sentinelRef} style={{ padding: "14px", textAlign: "center" }}>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
            Showing {visibleCount} of {occupations.length.toLocaleString()} occupations...
          </p>
        </div>
      )}
      {occupations.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No occupations match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
