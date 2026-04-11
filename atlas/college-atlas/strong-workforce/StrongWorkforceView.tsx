"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { streamSwpProject } from "@/college-atlas/strong-workforce/api";
import type {
  ApiLmiContext,
  ApiSwpProject,
  ApiSwpSection,
} from "@/college-atlas/strong-workforce/api";
import { getSavedProposals, type SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import {
  getSavedSwpProjects,
  saveSwpProject,
  type SavedSwpProject,
} from "@/college-atlas/strong-workforce/savedSwpProjects";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import { findScrollParent } from "@/ui/QueryShell";
import { buildSwpRequest, type SwpDefaults } from "./buildSwpRequest";
import SwpBuildMode from "./SwpBuildMode";
import SwpManageMode from "./SwpManageMode";
import SwpGenerationFlow from "./SwpGenerationFlow";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type SwpPhase = "selection" | "generating" | "streaming" | "complete";
type Mode = "build" | "manage";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function StrongWorkforceView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<Mode>("build");
  const [phase, setPhase] = useState<SwpPhase>("selection");

  // Build mode state — saved partnerships to draft from.
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [buildQuery, setBuildQuery] = useState("");
  const [expandedBuildId, setExpandedBuildId] = useState<string | null>(null);

  // Draft / streaming state — holds the in-flight or completed SWP project.
  const [selectedPartnership, setSelectedPartnership] = useState<SavedProposal | null>(null);
  const [selectedDefaults, setSelectedDefaults] = useState<SwpDefaults | null>(null);
  const [lmiContext, setLmiContext] = useState<ApiLmiContext | null>(null);
  const [swpProject, setSwpProject] = useState<ApiSwpProject | null>(null);
  const [streamedSections, setStreamedSections] = useState<ApiSwpSection[]>([]);
  const [swpError, setSwpError] = useState<string | null>(null);
  const [swpSaved, setSwpSaved] = useState(false);

  // Manage mode state — saved SWP projects list.
  const [savedSwpProjects, setSavedSwpProjects] = useState<SavedSwpProject[]>([]);
  const [expandedSwpId, setExpandedSwpId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const [userName, setUserName] = useState("");

  // Load saved partnerships + user name on mount.
  useEffect(() => {
    setSavedProposals(getSavedProposals(school.name));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, [school.name]);

  // Reload saved SWP projects when switching to manage mode.
  useEffect(() => {
    if (mode === "manage") {
      setSavedSwpProjects(getSavedSwpProjects(school.name));
    }
  }, [mode, school.name]);

  // Assemble the final SwpProject from streamed sections once the stream
  // finishes cleanly. The defaults captured when the draft started
  // determine which goal/metrics the project claims.
  useEffect(() => {
    if (phase === "complete" && streamedSections.length > 0 && lmiContext && selectedPartnership && selectedDefaults && !swpError) {
      setSwpProject({
        employer: selectedPartnership.proposal.employer,
        college: school.name,
        partnership_type: selectedPartnership.proposal.partnership_type,
        sections: streamedSections,
        lmi_context: lmiContext,
        goal: selectedDefaults.goal,
        metrics: selectedDefaults.metrics,
      });
    }
  }, [phase, streamedSections, lmiContext, selectedPartnership, selectedDefaults, swpError, school.name]);

  // Expand/collapse a row while preserving scroll position.
  const toggleWithScroll = useCallback((setter: (v: string | null) => void, current: string | null, id: string) => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    setter(current === id ? null : id);
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  const toggleBuildExpanded = useCallback(
    (id: string) => toggleWithScroll(setExpandedBuildId, expandedBuildId, id),
    [toggleWithScroll, expandedBuildId],
  );

  const toggleSwpExpanded = useCallback(
    (id: string) => toggleWithScroll(setExpandedSwpId, expandedSwpId, id),
    [toggleWithScroll, expandedSwpId],
  );

  // Start drafting a SWP project from a saved partnership. Builds the
  // request payload from the proposal + per-engagement defaults via the
  // pure helper, then kicks off the streaming generation endpoint.
  const handleDraft = useCallback((saved: SavedProposal) => {
    setSelectedPartnership(saved);
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);
    setSwpSaved(false);
    setPhase("generating");

    const { req, defaults } = buildSwpRequest(saved, school.name);
    setSelectedDefaults(defaults);

    streamSwpProject(
      req,
      (lmi) => { setLmiContext(lmi); setPhase("streaming"); },
      (section) => { setStreamedSections((prev) => [...prev, section]); },
      () => { setPhase("complete"); },
      (err) => { setSwpError(err); setPhase("complete"); },
    );
  }, [school.name]);

  const handleReject = useCallback(() => {
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);
    setPhase("selection");
  }, []);

  const handleBackToSelection = useCallback(() => {
    setSelectedPartnership(null);
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);
    setPhase("selection");
  }, []);

  const handleSave = useCallback(() => {
    if (swpSaved || !selectedPartnership || !swpProject) return;
    saveSwpProject(school.name, swpProject, selectedPartnership.id);
    setSwpSaved(true);
  }, [swpSaved, selectedPartnership, swpProject, school.name]);

  const handleRetry = useCallback(() => {
    if (selectedPartnership) handleDraft(selectedPartnership);
  }, [selectedPartnership, handleDraft]);

  return (
    <div ref={rootRef}>
      <AtlasHeader
        school={school}
        onBack={phase === "selection" ? onBack : handleBackToSelection}
        title={school.name}
        rightSlot={<KallipolisBrand />}
      />

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "32px 40px 80px" }}>
        <AnimatePresence mode="wait" initial={false}>
          {phase === "selection" ? (
            <motion.div
              key="selection"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
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

              {mode === "build" && (
                <SwpBuildMode
                  school={school}
                  userName={userName}
                  savedProposals={savedProposals}
                  buildQuery={buildQuery}
                  setBuildQuery={setBuildQuery}
                  expandedBuildId={expandedBuildId}
                  toggleExpanded={toggleBuildExpanded}
                  onDraft={handleDraft}
                />
              )}

              {mode === "manage" && (
                <SwpManageMode
                  school={school}
                  savedSwpProjects={savedSwpProjects}
                  setSavedSwpProjects={setSavedSwpProjects}
                  manageQuery={manageQuery}
                  setManageQuery={setManageQuery}
                  expandedSwpId={expandedSwpId}
                  toggleExpanded={toggleSwpExpanded}
                />
              )}
            </motion.div>
          ) : (
            <motion.div
              key="swp-flow"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <SwpGenerationFlow
                school={school}
                phase={phase}
                swpProject={swpProject}
                streamedSections={streamedSections}
                lmiContext={lmiContext}
                swpError={swpError}
                swpSaved={swpSaved}
                onSave={handleSave}
                onReject={handleReject}
                onRetry={handleRetry}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
