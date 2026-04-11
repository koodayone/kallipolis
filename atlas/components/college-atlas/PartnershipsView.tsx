"use client";

import { useState, useEffect, useCallback, useRef, memo, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import {
  getPartnershipLandscape,
  queryPartnerships,
  streamTargetedProposal,
} from "@/lib/api";
import type { ApiPartnershipOpportunity, ApiTargetedProposal } from "@/lib/api";
import { getSavedProposals, removeProposal, type SavedProposal } from "@/lib/savedProposals";
import AtlasHeader from "@/components/ui/AtlasHeader";
import KallipolisBrand from "@/components/ui/KallipolisBrand";
import RisingSun from "@/components/ui/RisingSun";
import Badge from "@/components/ui/Badge";
import EntityScrollList from "@/components/ui/EntityScrollList";
import type { Column } from "@/components/ui/EntityScrollList";
import ProposalFlow from "./ProposalFlow";
import ProposalCard from "./ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const SUGGESTIONS = [
  "Employers with strongest alignment",
  "Healthcare sector opportunities",
  "Biggest skill gaps to close",
  "Technology partnerships",
  "Highest paying roles",
];

type Phase = "selection" | "draft" | "generating" | "complete";
type Mode = "build" | "manage";

const PARTNERSHIP_COLUMNS: Column[] = [
  { label: "Employer", width: "1fr" },
  { label: "Sector", width: "160px" },
];

function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
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

  // Manage mode state
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [expandedSavedId, setExpandedSavedId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const allOpportunities = useMemo(
    () => [...landscape].sort((a, b) => a.name.localeCompare(b.name)),
    [landscape],
  );

  const filteredOpportunities = useMemo(() => {
    if (!query.trim()) return allOpportunities;
    const q = query.toLowerCase();
    return allOpportunities.filter((opp) =>
      opp.name.toLowerCase().includes(q) || (opp.sector || "").toLowerCase().includes(q),
    );
  }, [allOpportunities, query]);

  useEffect(() => {
    getPartnershipLandscape(school.name)
      .then((data) => {
        setLandscape(data.opportunities);
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
    const scrollEl = findScrollParent(rootRef.current);
    const savedScroll = scrollEl?.scrollTop ?? 0;
    const restoreScroll = () => requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = savedScroll; });

    const name = opp.name;
    if (expandedNames.has(name)) {
      setExpandedNames((prev) => { const next = new Set(prev); next.delete(name); return next; });
      restoreScroll();
      return;
    }
    setExpandedNames((prev) => new Set(prev).add(name));
    restoreScroll();
  }, [expandedNames]);

  const handleReset = useCallback(() => {
    setQuery(""); setSubmitted(false); setResults([]); setQueryMessage(null);
    setExpandedNames(new Set());
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const toggleWithScroll = useCallback((setter: (v: string | null) => void, current: string | null, id: string) => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    setter(current === id ? null : id);
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  // Phase transition handlers
  const handleDraftCTA = useCallback((opp: ApiPartnershipOpportunity) => {
    setSelectedEmployer(opp);
    setPhase("draft");
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
    setPhase("draft");
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

  const renderPartnershipRow = useCallback((opp: ApiPartnershipOpportunity, i: number) => (
    <PartnershipRow opp={opp} i={i} school={school}
      expandedNames={expandedNames} onExpand={handleExpand} onDraft={handleDraftCTA} />
  ), [school, expandedNames, handleExpand, handleDraftCTA]);

  const partnershipKeyExtractor = useCallback((opp: ApiPartnershipOpportunity) => opp.name, []);

  return (
    <div ref={rootRef}>
      <AtlasHeader
        school={school}
        onBack={phase === "selection" ? onBack : handleBackFromSplit}
        title={school.name}
        rightSlot={<KallipolisBrand />}
      />

      {phase === "selection" && (
          <div>
          <div style={{ maxWidth: "760px", margin: "0 auto", padding: "32px 40px 80px" }}>
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
                      color: mode === m ? "#1a1a2e" : "rgba(255,255,255,0.4)",
                      transition: "background 0.2s, color 0.2s",
                      textTransform: "capitalize",
                    }}
                  >{m}</button>
                ))}
              </div>
            </div>

            {/* ── Manage Mode ── */}
            {mode === "manage" && (
              <div>
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
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px", paddingTop: "24px", minHeight: "100vh" }}>
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
                              onClick={() => toggleWithScroll(setExpandedSavedId, expandedSavedId, saved.id)}
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
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                                transition={{ duration: 0.25 }}
                                style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                              >
                                <div style={{ padding: "16px 20px 24px" }}>
                                  <ProposalCard
                                    proposal={p}
                                    brandColor={school.brandColorLight}
                                    collegeId={school.name}
                                    onDismiss={() => {
                                      removeProposal(school.name, saved.id);
                                      setSavedProposals(getSavedProposals(school.name));
                                      setExpandedSavedId(null);
                                    }}
                                  />
                                </div>
                              </motion.div>
                            )}
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
            <div>
              {error && <p style={{ fontFamily: FONT, fontSize: "14px", color: "#e55", textAlign: "center", paddingTop: "40px" }}>{error}</p>}
              {loading && (
                <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
                  <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
                </div>
              )}

              {!loading && (
                <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
                  style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
                    <RisingSun style={{ width: "90px", height: "auto" }} />
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
                  <EntityScrollList
                    items={filteredOpportunities} initialCap={50} batchSize={50}
                    columns={PARTNERSHIP_COLUMNS} renderRow={renderPartnershipRow}
                    keyExtractor={partnershipKeyExtractor} entityName="partnership opportunities" school={school}
                  />
                </motion.div>
              )}
            </div>
            )}
          </div>
          </div>
        )}
        {phase !== "selection" && selectedEmployer && (
          <div style={{ maxWidth: "760px", margin: "0 auto" }}>
            <ProposalFlow
              school={school}
              employer={selectedEmployer}
              phase={phase as "draft" | "generating" | "complete"}
              engagementType={engagementType}
              onEngagementTypeChange={setEngagementType}
              onGenerate={handleGenerate}
              onReject={handleReject}
              proposal={proposal}
              proposalError={proposalError}
            />
          </div>
        )}
    </div>
  );
}


/* ── Partnership Row ────────────────────────────────────────────────────── */

const PartnershipRow = memo(function PartnershipRow({ opp, i, school, expandedNames, onExpand, onDraft }: {
  opp: ApiPartnershipOpportunity; i: number; school: SchoolConfig;
  expandedNames: Set<string>;
  onExpand: (opp: ApiPartnershipOpportunity) => void; onDraft: (opp: ApiPartnershipOpportunity) => void;
}) {
  const isOpen = expandedNames.has(opp.name);
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.015, 0.3) }}
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
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px" }}>
              {opp.description && (
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: "0 0 16px" }}>
                  {opp.description}
                </p>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); onDraft(opp); }}
                style={{
                  width: "100%", padding: "14px 24px", borderRadius: "10px",
                  fontFamily: FONT, fontSize: "15px", fontWeight: 600,
                  cursor: "pointer", border: "none",
                  background: school.brandColorLight, color: "#1a1a2e",
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
});
