"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import {
  getPartnershipLandscape,
  getEmployerPipeline,
  queryPartnerships,
  streamTargetedProposal,
} from "@/lib/api";
import type { ApiPartnershipOpportunity, ApiTargetedProposal } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";
import SplitView from "./SplitView";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const SUGGESTIONS = [
  "Employers with strongest alignment",
  "Healthcare sector opportunities",
  "Biggest skill gaps to close",
  "Technology partnerships",
  "Highest paying roles",
];

type Phase = "selection" | "split-view" | "generating" | "complete";

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  // Phase state
  const [phase, setPhase] = useState<Phase>("selection");
  const [selectedEmployer, setSelectedEmployer] = useState<ApiPartnershipOpportunity | null>(null);
  const [objective, setObjective] = useState("");
  const [proposal, setProposal] = useState<ApiTargetedProposal | null>(null);
  const [proposalError, setProposalError] = useState<string | null>(null);

  // Phase 1: Selection state
  const [landscape, setLandscape] = useState<ApiPartnershipOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState<ApiPartnershipOpportunity[]>([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryMessage, setQueryMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [expandedNames, setExpandedNames] = useState<Set<string>>(new Set());
  const [pipelineData, setPipelineData] = useState<Record<string, number>>({});
  const [pipelineLoading, setPipelineLoading] = useState<Set<string>>(new Set());

  const allOpportunities = [...landscape].sort((a, b) => b.alignment_score - a.alignment_score);

  useEffect(() => {
    getPartnershipLandscape(school.name)
      .then((data) => setLandscape(data.opportunities))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, [school.name]);

  // Phase 1 handlers
  const handleSubmit = useCallback(async () => {
    if (!query.trim()) return;
    setSubmitted(true);
    setExpandedNames(new Set());
    setQueryLoading(true);
    setQueryMessage(null);
    try {
      const resp = await queryPartnerships(query, school.name);
      setResults(resp.opportunities);
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
      const resp = await queryPartnerships(text, school.name);
      setResults(resp.opportunities);
      setQueryMessage(resp.message);
    } catch (err: any) {
      setResults([]);
      setQueryMessage(err?.message || "Something went wrong. Try a different question.");
    } finally {
      setQueryLoading(false);
    }
  }, [school.name]);

  const handleExpand = useCallback(async (opp: ApiPartnershipOpportunity) => {
    const name = opp.name;
    if (expandedNames.has(name)) {
      setExpandedNames((prev) => { const next = new Set(prev); next.delete(name); return next; });
      return;
    }
    setExpandedNames((prev) => new Set(prev).add(name));
    if (pipelineData[name] === undefined && !pipelineLoading.has(name)) {
      setPipelineLoading((prev) => new Set(prev).add(name));
      try {
        const data = await getEmployerPipeline(name, school.name);
        setPipelineData((prev) => ({ ...prev, [name]: data.pipeline_size }));
      } catch {}
      finally { setPipelineLoading((prev) => { const next = new Set(prev); next.delete(name); return next; }); }
    }
  }, [expandedNames, pipelineData, pipelineLoading, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]); setQueryMessage(null);
    setExpandedNames(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // Phase transition handlers
  const handleDraftCTA = useCallback((opp: ApiPartnershipOpportunity) => {
    setSelectedEmployer(opp);
    setPhase("split-view");
    setObjective("");
    setProposal(null);
    setProposalError(null);
  }, []);

  const handleGenerate = useCallback(() => {
    if (!selectedEmployer || !objective.trim()) return;
    setPhase("generating");
    setProposal(null);
    setProposalError(null);
    streamTargetedProposal(
      selectedEmployer.name,
      school.name,
      (p) => { setProposal(p); setPhase("complete"); },
      () => {},
      (err) => { setProposalError(err); setPhase("complete"); },
      objective,
    );
  }, [selectedEmployer, objective, school.name]);

  const handleReject = useCallback(() => {
    setPhase("split-view");
    setObjective("");
    setProposal(null);
    setProposalError(null);
  }, []);

  const handleBackFromSplit = useCallback(() => {
    setPhase("selection");
    setSelectedEmployer(null);
    setObjective("");
    setProposal(null);
    setProposalError(null);
  }, []);

  return (
    <>
      <LeafHeader school={school} onBack={phase === "selection" ? onBack : handleBackFromSplit} parentShape="tetrahedron" />

      <AnimatePresence mode="wait">
        {/* ── Phase 1: Selection ── */}
        {phase === "selection" && (
          <motion.div
            key="selection"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.25 }}
          >
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

              {/* Initial State */}
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
                        placeholder={`Ask about partnership opportunities near ${school.name}.`}
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
                      {allOpportunities.length} partnership opportunities
                    </p>
                    <PartnershipList
                      opportunities={allOpportunities} initialCap={50} school={school}
                      expandedNames={expandedNames} pipelineData={pipelineData} pipelineLoading={pipelineLoading}
                      onExpand={handleExpand} onDraft={handleDraftCTA}
                    />
                  </div>
                </motion.div>
              )}

              {/* Results State */}
              {submitted && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}
                  style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <input ref={inputRef} type="text" value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }}
                      placeholder={`Ask about partnership opportunities near ${school.name}.`}
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
                      style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer", padding: "8px" }}
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
                        {results.length} opportunit{results.length !== 1 ? "ies" : "y"} found
                      </p>
                      <PartnershipList
                        opportunities={results} initialCap={50} school={school}
                        expandedNames={expandedNames} pipelineData={pipelineData} pipelineLoading={pipelineLoading}
                        onExpand={handleExpand} onDraft={handleDraftCTA}
                      />
                    </>
                  )}
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* ── Phase 2+: Split View ── */}
        {phase !== "selection" && selectedEmployer && (
          <motion.div
            key="split-view"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ width: "100%" }}
          >
            <SplitView
              school={school}
              employer={selectedEmployer}
              phase={phase as "split-view" | "generating" | "complete"}
              objective={objective}
              onObjectiveChange={setObjective}
              onGenerate={handleGenerate}
              onReject={handleReject}
              proposal={proposal}
              proposalError={proposalError}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}


/* ── Partnership List ────────────────────────────────────────────────────── */

function PartnershipList({
  opportunities, initialCap, school, expandedNames, pipelineData, pipelineLoading,
  onExpand, onDraft,
}: {
  opportunities: ApiPartnershipOpportunity[];
  initialCap: number;
  school: SchoolConfig;
  expandedNames: Set<string>;
  pipelineData: Record<string, number>;
  pipelineLoading: Set<string>;
  onExpand: (opp: ApiPartnershipOpportunity) => void;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
}) {
  const [visibleCount, setVisibleCount] = useState(initialCap);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setVisibleCount(initialCap); }, [opportunities, initialCap]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && visibleCount < opportunities.length) {
        setVisibleCount((prev) => Math.min(prev + 50, opportunities.length));
      }
    }, { threshold: 0.1 });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [visibleCount, opportunities.length]);

  const visible = opportunities.slice(0, visibleCount);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr 140px 70px 70px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Sector</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "center" }}>Aligned</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "center" }}>Gaps</span>
      </div>

      {visible.map((opp, i) => {
        const isOpen = expandedNames.has(opp.name);
        return (
          <div key={opp.name}>
            <motion.button
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(i * 0.015, 0.3) }}
              onClick={() => onExpand(opp)}
              style={{
                width: "100%", textAlign: "left",
                display: "grid", gridTemplateColumns: "24px 1fr 140px 70px 70px",
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
              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{opp.name}</span>
              <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>{opp.sector || "—"}</span>
              <Badge style={{ color: school.brandColorLight, background: `${school.brandColorLight}20`, border: `1px solid ${school.brandColorLight}30`, fontSize: "11px", whiteSpace: "nowrap", display: "flex", justifyContent: "center" }}>
                {opp.alignment_score}
              </Badge>
              <Badge style={{ color: "rgba(255,255,255,0.45)", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.10)", fontSize: "11px", whiteSpace: "nowrap", display: "flex", justifyContent: "center" }}>
                {opp.gap_count}
              </Badge>
            </motion.button>

            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}
                  style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                >
                  <div style={{ padding: "16px 20px 24px" }}>
                    {opp.description && (
                      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: "0 0 16px" }}>
                        {opp.description}
                      </p>
                    )}
                    {opp.top_occupation && (
                      <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", marginBottom: "12px" }}>
                        Top role: <span style={{ color: "rgba(255,255,255,0.6)", fontWeight: 500 }}>{opp.top_occupation}</span>
                        {opp.top_wage && <span> · ${opp.top_wage.toLocaleString()}/yr</span>}
                      </div>
                    )}
                    <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", marginBottom: "12px" }}>
                      Student pipeline:{" "}
                      {pipelineLoading.has(opp.name) ? (
                        <span style={{ color: "rgba(255,255,255,0.3)" }}>Loading...</span>
                      ) : pipelineData[opp.name] !== undefined ? (
                        <span style={{ color: "rgba(255,255,255,0.6)", fontWeight: 500 }}>{pipelineData[opp.name].toLocaleString()} students</span>
                      ) : null}
                    </div>
                    {opp.aligned_skills.length > 0 && (
                      <div style={{ marginBottom: "12px" }}>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, display: "block", marginBottom: "8px" }}>
                          Aligned Skills ({opp.aligned_skills.length})
                        </span>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {opp.aligned_skills.map((skill) => (
                            <span key={skill} style={{
                              fontFamily: FONT, fontSize: "11px", color: school.brandColorLight,
                              background: `${school.brandColorLight}15`, border: `1px solid ${school.brandColorLight}30`,
                              borderRadius: "100px", padding: "4px 10px",
                            }}>{skill}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {opp.gap_skills.length > 0 && (
                      <div style={{ marginBottom: "16px" }}>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "8px" }}>
                          Skill Gaps ({opp.gap_skills.length})
                        </span>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                          {opp.gap_skills.map((skill) => (
                            <span key={skill} style={{
                              fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)",
                              background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                              borderRadius: "100px", padding: "4px 10px",
                            }}>{skill}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Draft CTA */}
                    <button
                      onClick={(e) => { e.stopPropagation(); onDraft(opp); }}
                      style={{
                        width: "100%", padding: "14px 24px", borderRadius: "10px",
                        fontFamily: FONT, fontSize: "15px", fontWeight: 600,
                        cursor: "pointer", border: "none",
                        background: school.brandColorLight, color: "#ffffff",
                        transition: "opacity 0.15s",
                        letterSpacing: "-0.01em",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
                      onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
                    >
                      Draft Partnership Proposal with {opp.name}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {visibleCount < opportunities.length && (
        <div ref={sentinelRef} style={{ padding: "14px", textAlign: "center" }}>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
            Showing {visibleCount} of {opportunities.length} opportunities...
          </p>
        </div>
      )}
      {opportunities.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No partnership opportunities match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
