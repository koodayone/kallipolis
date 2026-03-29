"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import {
  getPartnershipLandscape,
  getEmployerPipeline,
  getEmployerDetail,
  queryPartnerships,
  streamTargetedProposal,
} from "@/lib/api";
import type { ApiPartnershipOpportunity, ApiTargetedProposal, ApiEmployerDetail } from "@/lib/api";
import { getSavedProposals, removeProposal, type SavedProposal } from "@/lib/savedProposals";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";
import SplitView from "./SplitView";
import ProposalCard from "@/components/domains/ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const SUGGESTIONS = [
  "Employers with strongest alignment",
  "Healthcare sector opportunities",
  "Biggest skill gaps to close",
  "Technology partnerships",
  "Highest paying roles",
];

type Phase = "selection" | "split-view" | "generating" | "complete";
type Mode = "build" | "manage";

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  // Phase & mode state
  const [phase, setPhase] = useState<Phase>("selection");
  const [mode, setMode] = useState<Mode>("build");
  const [selectedEmployer, setSelectedEmployer] = useState<ApiPartnershipOpportunity | null>(null);
  const [engagementType, setEngagementType] = useState("");
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

  // Employer detail cache (for expanded row occupation list)
  const [employerDetails, setEmployerDetails] = useState<Record<string, ApiEmployerDetail>>({});

  // Manage mode state
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [expandedSavedId, setExpandedSavedId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const allOpportunities = [...landscape].sort((a, b) => a.name.localeCompare(b.name));

  const filteredOpportunities = query.trim()
    ? allOpportunities.filter((opp) => {
        const q = query.toLowerCase();
        return opp.name.toLowerCase().includes(q) || (opp.sector || "").toLowerCase().includes(q);
      })
    : allOpportunities;

  useEffect(() => {
    getPartnershipLandscape(school.name)
      .then((data) => {
        setLandscape(data.opportunities);
        // Pre-fetch pipeline sizes for expanded row display
        for (const opp of data.opportunities.slice(0, 20)) {
          getEmployerPipeline(opp.name, school.name)
            .then((d) => setPipelineData((prev) => ({ ...prev, [opp.name]: d.pipeline_size })))
            .catch(() => {});
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, [school.name]);

  // Reload saved proposals when switching to manage mode or after saving
  useEffect(() => {
    if (mode === "manage") {
      setSavedProposals(getSavedProposals(school.name));
    }
  }, [mode, school.name]);

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
    if (!employerDetails[name]) {
      getEmployerDetail(name, school.name)
        .then((detail) => setEmployerDetails((prev) => ({ ...prev, [name]: detail })))
        .catch(() => {});
    }
  }, [expandedNames, pipelineData, pipelineLoading, employerDetails, school.name]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]); setQueryMessage(null);
    setExpandedNames(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // Phase transition handlers
  const handleDraftCTA = useCallback((opp: ApiPartnershipOpportunity) => {
    setSelectedEmployer(opp);
    setPhase("split-view");
    setEngagementType("");
    setProposal(null);
    setProposalError(null);
  }, []);

  const handleGenerate = useCallback(() => {
    if (!selectedEmployer || !engagementType) return;
    setPhase("generating");
    setProposal(null);
    setProposalError(null);
    streamTargetedProposal(
      selectedEmployer.name,
      school.name,
      (p) => { setProposal(p); setPhase("complete"); },
      () => {},
      (err) => { setProposalError(err); setPhase("complete"); },
      engagementType,
    );
  }, [selectedEmployer, engagementType, school.name]);

  const handleReject = useCallback(() => {
    setPhase("split-view");
    setEngagementType("");
    setProposal(null);
    setProposalError(null);
  }, []);

  const handleBackFromSplit = useCallback(() => {
    setPhase("selection");
    setSelectedEmployer(null);
    setEngagementType("");
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
            <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "40px" }}>
              <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
            </div>

            {/* Build / Manage segmented control */}
            <div style={{ display: "flex", justifyContent: "center", marginBottom: "40px" }}>
              <div style={{
                display: "flex", borderRadius: "8px",
                border: "1px solid rgba(255,255,255,0.10)",
                background: "rgba(255,255,255,0.03)", overflow: "hidden",
              }}>
                {(["build", "manage"] as Mode[]).map((m, i) => (
                  <button key={m} onClick={() => setMode(m)}
                    style={{
                      fontFamily: FONT, fontSize: "12px", fontWeight: 600, letterSpacing: "0.02em",
                      padding: "8px 0", width: "90px", textAlign: "center", cursor: "pointer",
                      border: "none",
                      borderLeft: i > 0 ? "1px solid rgba(255,255,255,0.10)" : "none",
                      background: mode === m ? school.brandColorLight : "transparent",
                      color: mode === m ? "#ffffff" : "rgba(255,255,255,0.4)",
                      transition: "background 0.2s, color 0.2s",
                      textTransform: "capitalize",
                    }}
                  >{m}</button>
                ))}
              </div>
            </div>

            {/* ── Manage Mode ── */}
            {mode === "manage" && (
              <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>
                {savedProposals.length === 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", paddingTop: "80px" }}>
                    <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)", margin: 0 }}>
                      No saved partnerships yet.
                    </p>
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.25)", margin: 0 }}>
                      Draft and save your first proposal to get started.
                    </p>
                  </div>
                ) : (() => {
                  const filtered = manageQuery.trim()
                    ? savedProposals.filter((s) => s.proposal.employer.toLowerCase().includes(manageQuery.toLowerCase()))
                    : savedProposals;
                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px", paddingTop: "24px" }}>
                      {/* Search bar */}
                      <div style={{ position: "relative", marginBottom: "16px" }}>
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
                          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
                          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        <input type="text" value={manageQuery}
                          onChange={(e) => setManageQuery(e.target.value)}
                          placeholder="Search saved partnerships..."
                          style={{
                            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
                            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
                            outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                          }}
                          onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                          onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
                        />
                      </div>

                      {/* Column headers */}
                      <div style={{
                        display: "grid", gridTemplateColumns: "24px 1fr 160px",
                        padding: "12px 16px", gap: "10px", alignItems: "center",
                      }}>
                        <span />
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
                      </div>

                      {/* Rows */}
                      {filtered.map((saved) => {
                        const p = saved.proposal;
                        const isExpanded = expandedSavedId === saved.id;
                        return (
                          <div key={saved.id}>
                            <button
                              onClick={() => setExpandedSavedId(isExpanded ? null : saved.id)}
                              style={{
                                width: "100%", textAlign: "left", cursor: "pointer",
                                display: "grid", gridTemplateColumns: "24px 1fr 160px",
                                padding: "12px 16px", gap: "10px", alignItems: "center",
                                background: isExpanded ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                                border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
                                transition: "background 0.15s",
                              }}
                              onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
                              onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                            >
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                                style={{ transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
                                <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                                {p.employer}
                              </span>
                              <span style={{
                                textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                                color: school.brandColorLight,
                              }}>
                                {p.partnership_type}
                              </span>
                            </button>
                            <AnimatePresence>
                              {isExpanded && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}
                                  style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                                >
                                  <div style={{ padding: "16px 20px 24px" }}>
                                    <ProposalCard
                                      proposal={p}
                                      brandColor={school.brandColorLight}
                                      onDismiss={() => {
                                        removeProposal(school.name, saved.id);
                                        setSavedProposals(getSavedProposals(school.name));
                                        setExpandedSavedId(null);
                                      }}
                                    />
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* ── Build Mode ── */}
            {mode === "build" && (
            <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>
              {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
              {loading && (
                <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
                  <RisingSun style={{ width: "70px", height: "auto", opacity: 0.4 }} />
                </div>
              )}

              {!loading && (
                <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
                  style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
                    <RisingSun style={{ width: "70px", height: "auto" }} />
                    <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center", margin: 0 }}>
                      Who is our partner{userName ? `, ${userName}` : ""}?
                    </h1>
                    <div style={{ width: "100%", position: "relative" }}>
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
                        style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                        <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
                        <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                      <input ref={inputRef} type="text" value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search employers..."
                        style={{
                          width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
                          color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                          border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
                          outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
                        }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
                      />
                    </div>
                  </div>
                  <div style={{ minHeight: "100vh" }}>
                    <PartnershipList
                      opportunities={filteredOpportunities} initialCap={50} school={school}
                      expandedNames={expandedNames} pipelineData={pipelineData} pipelineLoading={pipelineLoading}
                      employerDetails={employerDetails} onExpand={handleExpand} onDraft={handleDraftCTA}
                    />
                  </div>
                </motion.div>
              )}
            </div>
            )}
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
              engagementType={engagementType}
              onEngagementTypeChange={setEngagementType}
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
  employerDetails, onExpand, onDraft,
}: {
  opportunities: ApiPartnershipOpportunity[];
  initialCap: number;
  school: SchoolConfig;
  expandedNames: Set<string>;
  pipelineData: Record<string, number>;
  pipelineLoading: Set<string>;
  employerDetails: Record<string, ApiEmployerDetail>;
  onExpand: (opp: ApiPartnershipOpportunity) => void;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
}) {
  const [visibleCount, setVisibleCount] = useState(initialCap);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setVisibleCount(initialCap); }, [initialCap]);

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
        display: "grid", gridTemplateColumns: "24px 1fr 160px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Sector</span>
      </div>

      {visible.map((opp, i) => {
        const isOpen = expandedNames.has(opp.name);
        return (
          <div key={opp.name}>
            <motion.button
              layout
              onClick={() => onExpand(opp)}
              style={{
                width: "100%", textAlign: "left",
                display: "grid", gridTemplateColumns: "24px 1fr 160px",
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
                      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: "0 0 14px" }}>
                        {opp.description}
                      </p>
                    )}
                    {/* Occupations & Wages */}
                    {employerDetails[opp.name] ? (
                      <div style={{ marginBottom: "16px" }}>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "8px" }}>
                          Relevant Occupations
                        </span>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {employerDetails[opp.name].occupations.map((occ: any) => (
                          <div key={occ.soc_code || occ.title} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: FONT, fontSize: "13px" }}>
                            <span style={{ color: "rgba(255,255,255,0.7)" }}>{occ.title}</span>
                            {occ.annual_wage && (
                              <span style={{ color: "rgba(255,255,255,0.4)", fontWeight: 500 }}>${occ.annual_wage.toLocaleString()}/yr</span>
                            )}
                          </div>
                        ))}
                      </div>
                      </div>
                    ) : (
                      <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", marginBottom: "16px" }}>
                        Loading occupations...
                      </div>
                    )}
                    {/* Student context */}
                    {pipelineData[opp.name] !== undefined && (
                      <div style={{ marginBottom: "16px" }}>
                        <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", lineHeight: 1.5, margin: 0 }}>
                          <span style={{ color: "rgba(255,255,255,0.7)", fontWeight: 500 }}>{pipelineData[opp.name].toLocaleString()}</span>
                          {" "}students have 3 or more skills relevant to this employer&apos;s hiring needs
                        </p>
                        {opp.aligned_skills.length > 0 && (
                          <div style={{ marginTop: "10px" }}>
                            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "6px" }}>
                              Top skills across this employer&apos;s roles
                            </span>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                            {opp.aligned_skills.slice(0, 4).map((skill) => (
                              <span key={skill} style={{
                                fontFamily: FONT, fontSize: "11px", color: school.brandColorLight,
                                background: `${school.brandColorLight}12`, border: `1px solid ${school.brandColorLight}25`,
                                borderRadius: "100px", padding: "4px 10px",
                              }}>{skill}</span>
                            ))}
                          </div>
                          </div>
                        )}
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
