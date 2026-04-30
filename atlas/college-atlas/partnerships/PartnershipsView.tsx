"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import {
  getEmployerOccupations,
  getPartnershipLandscape,
  streamTargetedProposal,
} from "@/college-atlas/partnerships/api";
import type {
  ApiEmployerOccupation,
  ApiPartnershipOpportunity,
  ApiTargetedProposal,
} from "@/college-atlas/partnerships/api";
import { getSavedProposals, type SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import FormHeader from "@/ui/FormHeader";
import RisingSun from "@/ui/RisingSun";
import { findScrollParent } from "@/ui/QueryShell";
import { PREVIEW_MODE } from "@/preview/mode";
import { getSeededProposals } from "@/preview/seededPartnerships";
import ProposalFlow from "./ProposalFlow";
import PartnershipBuildMode from "./PartnershipBuildMode";
import PartnershipManageMode from "./PartnershipManageMode";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Phase = "selection" | "draft" | "generating" | "complete";
type Mode = "build" | "manage";

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);

  // Phase state — drives the selection screen → occupation picker → ProposalFlow handoff.
  const [phase, setPhase] = useState<Phase>("selection");
  const [mode, setMode] = useState<Mode>("build");
  const [selectedEmployer, setSelectedEmployer] = useState<ApiPartnershipOpportunity | null>(null);
  const [proposal, setProposal] = useState<ApiTargetedProposal | null>(null);
  const [proposalError, setProposalError] = useState<string | null>(null);

  // Occupation picker state — populated when an employer is selected.
  // The first occupation is the deterministic suggested default (sorted by
  // coverage ratio then annual openings on the backend); pre-selecting it
  // means Generate is enabled by default.
  const [occupations, setOccupations] = useState<ApiEmployerOccupation[]>([]);
  const [coeRegion, setCoeRegion] = useState<string>("");
  const [selectedSocCode, setSelectedSocCode] = useState<string | null>(null);
  const [occupationsLoading, setOccupationsLoading] = useState(false);
  const [occupationsError, setOccupationsError] = useState<string | null>(null);

  // Build mode state — landscape data + search query. Rows are no longer
  // expandable; the picker absorbs all per-employer context (description,
  // website, occupations).
  const [landscape, setLandscape] = useState<ApiPartnershipOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Manage mode state — saved proposal search + row expansion. Saved
  // proposals are also surfaced in Build mode as a per-employer
  // "N saved" indicator, so we refetch on every return to the selection
  // phase (not just when entering Manage).
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [expandedSavedId, setExpandedSavedId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const filteredOpportunities = useMemo(() => {
    if (!query.trim()) return landscape;
    const q = query.toLowerCase();
    return landscape.filter((opp) =>
      opp.name.toLowerCase().includes(q)
      || (opp.sector || "").toLowerCase().includes(q)
      || opp.swp_sectors.some((s) => s.toLowerCase().includes(q)),
    );
  }, [landscape, query]);

  // Saved-count per employer, used for the "N saved" indicator in Build
  // mode rows. Recomputes whenever savedProposals changes (which happens
  // on phase return — see effect below).
  const savedCountsByEmployer = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const sp of savedProposals) {
      counts[sp.proposal.employer] = (counts[sp.proposal.employer] ?? 0) + 1;
    }
    return counts;
  }, [savedProposals]);

  // Set of regional-priority sector names, computed from the landscape's
  // priority_sectors_matched. Used by both Build mode (already) and Manage
  // mode (to surface the priority dot on saved-proposal rows whose sector
  // is in the set, mirroring Build mode's per-sector indicator).
  const prioritySet = useMemo(() => {
    const set = new Set<string>();
    for (const opp of landscape) {
      for (const p of opp.priority_sectors_matched) set.add(p);
    }
    return set;
  }, [landscape]);

  // Load landscape on mount.
  useEffect(() => {
    getPartnershipLandscape(school.name)
      .then((data) => setLandscape(data.opportunities))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [school.name]);

  // Reload saved proposals whenever we land back on the selection phase
  // (initial mount, after picker dismiss, after a generation completes).
  // Build mode reads them for the saved-count indicator; Manage mode
  // reads them for its row list. In preview mode the library is the
  // static seeded set — session-generated drafts are not surfaced in
  // Manage to keep the "nothing persists in preview" story coherent.
  useEffect(() => {
    if (phase !== "selection") return;
    if (PREVIEW_MODE) {
      setSavedProposals(getSeededProposals(school.name));
    } else {
      setSavedProposals(getSavedProposals(school.name));
    }
  }, [phase, school.name]);

  const toggleSavedExpanded = useCallback((id: string) => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    setExpandedSavedId((current) => (current === id ? null : id));
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  // Generate the partnership artifact for a (employer, SOC) pair. The SOC
  // comes from the picker — either the suggested default the coordinator
  // accepted, or one they overrode.
  const runGeneration = useCallback((employerName: string, socCode: string) => {
    setPhase("generating");
    setProposal(null);
    setProposalError(null);
    streamTargetedProposal(
      employerName,
      school.name,
      (p) => { setProposal(p); setPhase("complete"); },
      () => {},
      (err) => { setProposalError(err); setPhase("complete"); },
      socCode,
    );
  }, [school.name]);

  // Phase transitions.
  // Clicking an employer fetches its occupation set, pre-selects the
  // suggested default (the first row), and shows the picker. Even when
  // the employer has only one occupation we keep the picker — consistency
  // beats saving one click, and the card carries informational value.
  const handleDraftCTA = useCallback((opp: ApiPartnershipOpportunity) => {
    setSelectedEmployer(opp);
    setProposal(null);
    setProposalError(null);
    setOccupations([]);
    setSelectedSocCode(null);
    setOccupationsError(null);
    setOccupationsLoading(true);
    setPhase("draft");
    getEmployerOccupations(opp.name, school.name)
      .then((data) => {
        setOccupations(data.occupations);
        setCoeRegion(data.coe_region);
        // First row is the deterministic suggested default per the backend sort.
        if (data.occupations.length > 0) {
          setSelectedSocCode(data.occupations[0].soc_code);
        }
      })
      .catch((e) => setOccupationsError(e.message))
      .finally(() => setOccupationsLoading(false));
  }, [school.name]);

  const handleGenerate = useCallback(() => {
    if (!selectedEmployer || !selectedSocCode) return;
    runGeneration(selectedEmployer.name, selectedSocCode);
  }, [selectedEmployer, selectedSocCode, runGeneration]);

  const handleRetry = useCallback(() => {
    if (selectedEmployer && selectedSocCode) {
      runGeneration(selectedEmployer.name, selectedSocCode);
    }
  }, [selectedEmployer, selectedSocCode, runGeneration]);

  const resetToSelection = useCallback(() => {
    setPhase("selection");
    setSelectedEmployer(null);
    setProposal(null);
    setProposalError(null);
    setOccupations([]);
    setSelectedSocCode(null);
    setOccupationsError(null);
    setCoeRegion("");
  }, []);

  const handleBackFromSplit = resetToSelection;

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
            {loading && (
              <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
                <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
              </div>
            )}

            {!loading && (
              <>
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

                <div style={{ marginBottom: "40px" }}>
                  <FormHeader formName="Partnerships" />
                </div>

                {mode === "manage" && (
                  <PartnershipManageMode
                    school={school}
                    savedProposals={savedProposals}
                    manageQuery={manageQuery}
                    setManageQuery={setManageQuery}
                    expandedSavedId={expandedSavedId}
                    toggleExpanded={toggleSavedExpanded}
                    prioritySet={prioritySet}
                  />
                )}

                {mode === "build" && (
                  <PartnershipBuildMode
                    school={school}
                    loading={loading}
                    error={error}
                    query={query}
                    setQuery={setQuery}
                    inputRef={inputRef}
                    filteredOpportunities={filteredOpportunities}
                    savedCountsByEmployer={savedCountsByEmployer}
                    onDraft={handleDraftCTA}
                  />
                )}
              </>
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
            occupations={occupations}
            coeRegion={coeRegion}
            selectedSocCode={selectedSocCode}
            occupationsLoading={occupationsLoading}
            occupationsError={occupationsError}
            onSelectSoc={setSelectedSocCode}
            onGenerate={handleGenerate}
            onRetry={handleRetry}
            proposal={proposal}
            proposalError={proposalError}
          />
        </div>
      )}
    </div>
  );
}
