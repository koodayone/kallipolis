"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import {
  getPartnershipLandscape,
  streamTargetedProposal,
} from "@/college-atlas/partnerships/api";
import type { ApiPartnershipOpportunity, ApiTargetedProposal } from "@/college-atlas/partnerships/api";
import { getSavedProposals, type SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import { findScrollParent } from "@/ui/QueryShell";
import ProposalFlow from "./ProposalFlow";
import PartnershipBuildMode from "./PartnershipBuildMode";
import PartnershipManageMode from "./PartnershipManageMode";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Phase = "selection" | "draft" | "generating" | "complete";
type Mode = "build" | "manage";

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);

  // Phase state — drives the selection screen → ProposalFlow handoff.
  const [phase, setPhase] = useState<Phase>("selection");
  const [mode, setMode] = useState<Mode>("build");
  const [selectedEmployer, setSelectedEmployer] = useState<ApiPartnershipOpportunity | null>(null);
  const [engagementType, setEngagementType] = useState("");
  const [proposal, setProposal] = useState<ApiTargetedProposal | null>(null);
  const [proposalError, setProposalError] = useState<string | null>(null);

  // Build mode state — landscape data + search query + row expansion.
  const [landscape, setLandscape] = useState<ApiPartnershipOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const [expandedNames, setExpandedNames] = useState<Set<string>>(new Set());

  // Manage mode state — saved proposal search + row expansion.
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [expandedSavedId, setExpandedSavedId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const filteredOpportunities = useMemo(() => {
    const sorted = [...landscape].sort((a, b) => a.name.localeCompare(b.name));
    if (!query.trim()) return sorted;
    const q = query.toLowerCase();
    return sorted.filter((opp) =>
      opp.name.toLowerCase().includes(q) || (opp.sector || "").toLowerCase().includes(q),
    );
  }, [landscape, query]);

  // Load landscape + user name on mount.
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

  // Reload saved proposals when switching to manage mode.
  useEffect(() => {
    if (mode === "manage") {
      setSavedProposals(getSavedProposals(school.name));
    }
  }, [mode, school.name]);

  // Expand/collapse a row while preserving the scroll position of the
  // nearest scrollable ancestor — avoids jumping when the row height changes.
  const handleExpand = useCallback((opp: ApiPartnershipOpportunity) => {
    const scrollEl = findScrollParent(rootRef.current);
    const savedScroll = scrollEl?.scrollTop ?? 0;
    const restoreScroll = () => requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = savedScroll; });

    setExpandedNames((prev) => {
      const next = new Set(prev);
      if (next.has(opp.name)) next.delete(opp.name);
      else next.add(opp.name);
      return next;
    });
    restoreScroll();
  }, []);

  const toggleSavedExpanded = useCallback((id: string) => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    setExpandedSavedId((current) => (current === id ? null : id));
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  // Phase transitions.
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

            {mode === "manage" && (
              <PartnershipManageMode
                school={school}
                savedProposals={savedProposals}
                setSavedProposals={setSavedProposals}
                manageQuery={manageQuery}
                setManageQuery={setManageQuery}
                expandedSavedId={expandedSavedId}
                toggleExpanded={toggleSavedExpanded}
              />
            )}

            {mode === "build" && (
              <PartnershipBuildMode
                school={school}
                userName={userName}
                loading={loading}
                error={error}
                query={query}
                setQuery={setQuery}
                inputRef={inputRef}
                filteredOpportunities={filteredOpportunities}
                expandedNames={expandedNames}
                onExpand={handleExpand}
                onDraft={handleDraftCTA}
              />
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
