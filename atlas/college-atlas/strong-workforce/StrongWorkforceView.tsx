"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import { streamSwpProject } from "@/college-atlas/strong-workforce/api";
import type { ApiLmiContext, ApiSwpProject, ApiSwpSection, SwpProjectRequest } from "@/college-atlas/strong-workforce/api";
import { getSavedProposals, type SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import { getSavedSwpProjects, saveSwpProject, removeSwpProject, type SavedSwpProject } from "@/college-atlas/strong-workforce/savedSwpProjects";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import RisingSun from "@/ui/RisingSun";
import SwpArtifact from "./SwpArtifact";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type SwpPhase = "selection" | "generating" | "streaming" | "complete";
type Mode = "build" | "manage";

const PARTNERSHIP_DEFAULTS: Record<string, {
  goal: string;
  metrics: string[];
  apprenticeship: boolean;
  wbl: boolean;
}> = {
  "internship":          { goal: "Workforce",  metrics: ["Employed in Field of Study", "Median Annual Earnings"], apprenticeship: false, wbl: true },
  "apprenticeship":      { goal: "Workforce",  metrics: ["Employed in Field of Study", "Attained a Living Wage", "Job Closely Related to Field of Study"], apprenticeship: true, wbl: true },
  "curriculum_codesign": { goal: "Completion", metrics: ["Completed a Degree or Certificate"], apprenticeship: false, wbl: false },
  "hiring_mou":          { goal: "Workforce",  metrics: ["Employed in Field of Study", "Attained a Living Wage"], apprenticeship: false, wbl: false },
  "advisory_board":      { goal: "Completion", metrics: ["Completed a Degree or Certificate"], apprenticeship: false, wbl: false },
};


type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

function findScrollParent(el: HTMLElement | null): HTMLElement | null {
  while (el) {
    if (el.scrollHeight > el.clientHeight && getComputedStyle(el).overflowY !== "visible") return el;
    el = el.parentElement;
  }
  return null;
}

export default function StrongWorkforceView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<Mode>("build");
  const [phase, setPhase] = useState<SwpPhase>("selection");

  // Build state
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [buildQuery, setBuildQuery] = useState("");
  const [expandedBuildId, setExpandedBuildId] = useState<string | null>(null);
  const [selectedPartnership, setSelectedPartnership] = useState<SavedProposal | null>(null);
  const [lmiContext, setLmiContext] = useState<ApiLmiContext | null>(null);
  const [swpProject, setSwpProject] = useState<ApiSwpProject | null>(null);
  const [streamedSections, setStreamedSections] = useState<ApiSwpSection[]>([]);
  const [swpError, setSwpError] = useState<string | null>(null);

  // SWP parameter inputs
  const [goal, setGoal] = useState("Workforce");
  const [metrics, setMetrics] = useState<string[]>([]);
  const [apprenticeship, setApprenticeship] = useState(false);
  const [wbl, setWbl] = useState(false);

  // Manage state
  const [savedSwpProjects, setSavedSwpProjects] = useState<SavedSwpProject[]>([]);
  const [expandedSwpId, setExpandedSwpId] = useState<string | null>(null);
  const [manageQuery, setManageQuery] = useState("");

  const [userName, setUserName] = useState("");

  // Load data
  useEffect(() => {
    setSavedProposals(getSavedProposals(school.name));
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((data) => { if (data?.user?.name) setUserName(data.user.name.split(" ")[0]); })
      .catch(() => {});
  }, [school.name]);

  useEffect(() => {
    if (mode === "manage") {
      setSavedSwpProjects(getSavedSwpProjects(school.name));
    }
  }, [mode, school.name]);

  const filteredProposals = buildQuery.trim()
    ? savedProposals.filter((s) => s.proposal.employer.toLowerCase().includes(buildQuery.toLowerCase()))
    : savedProposals;

  const filteredSwpProjects = manageQuery.trim()
    ? savedSwpProjects.filter((s) => s.project.employer.toLowerCase().includes(manageQuery.toLowerCase()))
    : savedSwpProjects;

  const toggleWithScroll = useCallback((setter: (v: string | null) => void, current: string | null, id: string) => {
    const scrollEl = findScrollParent(rootRef.current);
    const saved = scrollEl?.scrollTop ?? 0;
    setter(current === id ? null : id);
    requestAnimationFrame(() => { if (scrollEl) scrollEl.scrollTop = saved; });
  }, []);

  const handleDraft = useCallback((saved: SavedProposal) => {
    setSelectedPartnership(saved);
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);
    setSwpSaved(false);
    setPhase("generating");

    const defaults = PARTNERSHIP_DEFAULTS[saved.engagementType] || {
      goal: "Workforce", metrics: ["Employed in Field of Study"], apprenticeship: false, wbl: false,
    };
    setGoal(defaults.goal);
    setMetrics(defaults.metrics);
    setApprenticeship(defaults.apprenticeship);
    setWbl(defaults.wbl);

    const p = saved.proposal;
    const req: SwpProjectRequest = {
      employer: p.employer,
      college: school.name,
      partnership_type: p.partnership_type,
      selected_occupation: p.selected_occupation,
      selected_soc_code: p.selected_soc_code ?? null,
      core_skills: p.core_skills,
      gap_skill: p.gap_skill,
      opportunity: p.opportunity,
      opportunity_evidence: p.opportunity_evidence,
      curriculum_composition: p.justification.curriculum_composition,
      curriculum_evidence: p.justification.curriculum_evidence,
      student_composition: p.justification.student_composition,
      student_evidence: p.justification.student_evidence,
      roadmap: p.roadmap,
      goal: defaults.goal,
      metrics: defaults.metrics,
      apprenticeship: defaults.apprenticeship,
      work_based_learning: defaults.wbl,
    };

    streamSwpProject(
      req,
      (lmi) => { setLmiContext(lmi); setPhase("streaming"); },
      (section) => { setStreamedSections(prev => [...prev, section]); },
      () => { setPhase("complete"); },
      (err) => { setSwpError(err); setPhase("complete"); },
    );
  }, [school.name]);

  // Build complete SwpProject when streaming finishes
  useEffect(() => {
    if (phase === "complete" && streamedSections.length > 0 && lmiContext && selectedPartnership && !swpError) {
      setSwpProject({
        employer: selectedPartnership.proposal.employer,
        college: school.name,
        partnership_type: selectedPartnership.proposal.partnership_type,
        sections: streamedSections,
        lmi_context: lmiContext,
        goal,
        metrics,
      });
    }
  }, [phase, streamedSections, lmiContext, selectedPartnership, swpError, school.name, goal, metrics]);

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

  const [swpSaved, setSwpSaved] = useState(false);


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

              {/* ── Build Mode ── */}
              {mode === "build" && (
                <>
                  {/* Build mode header with sun + greeting */}
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", marginBottom: "24px" }}>
                    <RisingSun style={{ width: "90px", height: "auto" }} />
                    <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center", margin: 0 }}>
                      SWP compliance{userName ? `, ${userName}` : ""}?
                    </h1>
                  </div>

                  {savedProposals.length === 0 ? (
                    <div style={{ padding: "40px", textAlign: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" }}>
                      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>No saved partnerships yet.</p>
                      <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Visit the Industry domain to build and save a partnership proposal.</p>
                    </div>
                  ) : (
                    <>
                      {/* Search bar */}
                      <div style={{ position: "relative", marginBottom: "16px" }}>
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
                          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
                          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        <input type="text" value={buildQuery} onChange={(e) => setBuildQuery(e.target.value)}
                          placeholder="Search partnerships..."
                          style={{
                            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
                            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
                            outline: "none",
                          }}
                        />
                      </div>

                      {/* Column headers */}
                      <div style={{ display: "grid", gridTemplateColumns: "24px 1fr 160px", padding: "12px 16px", gap: "10px", alignItems: "center" }}>
                        <span />
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
                      </div>

                      {/* Rows */}
                      {filteredProposals.map((saved) => {
                        const isExpanded = expandedBuildId === saved.id;
                        return (
                          <div key={saved.id}>
                            <button
                              onClick={() => toggleWithScroll(setExpandedBuildId, expandedBuildId, saved.id)}
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
                                {saved.proposal.employer}
                              </span>
                              <span style={{ textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600, color: school.brandColorLight }}>
                                {saved.proposal.partnership_type}
                              </span>
                            </button>
                            {isExpanded && (
                              <div style={{ background: "rgba(255,255,255,0.02)" }}>
                                <div style={{ padding: "14px 20px 18px" }}>
                                  <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: "0 0 14px" }}>
                                    {saved.proposal.partnership_type} partnership with {saved.proposal.employer}{saved.proposal.sector ? ` for the ${saved.proposal.sector} sector` : ""}.
                                  </p>
                                  <button
                                    onClick={() => handleDraft(saved)}
                                    style={{
                                      width: "100%", padding: "14px 24px", borderRadius: "10px",
                                      fontFamily: FONT, fontSize: "15px", fontWeight: 600, letterSpacing: "-0.01em",
                                      cursor: "pointer", border: "none",
                                      background: school.brandColorLight, color: "#ffffff",
                                      transition: "opacity 0.15s",
                                    }}
                                    onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
                                    onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
                                  >
                                    Draft SWP Project Proposal for NOVA
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </>
                  )}
                </>
              )}

              {/* ── Manage Mode ── */}
              {mode === "manage" && (
                <>
                  {savedSwpProjects.length === 0 ? (
                    <div style={{ padding: "40px", textAlign: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" }}>
                      <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>No saved SWP projects yet.</p>
                      <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Generate and save an SWP document from the Build tab.</p>
                    </div>
                  ) : (
                    <div style={{ minHeight: "100vh" }}>
                      {/* Search bar */}
                      <div style={{ position: "relative", marginBottom: "16px" }}>
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
                          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
                          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        <input type="text" value={manageQuery} onChange={(e) => setManageQuery(e.target.value)}
                          placeholder="Search Strong Workforce Program projects for NOVA..."
                          style={{
                            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
                            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
                            outline: "none",
                          }}
                        />
                      </div>

                      {/* Column headers */}
                      <div style={{ display: "grid", gridTemplateColumns: "24px 1fr 160px", padding: "12px 16px", gap: "10px", alignItems: "center" }}>
                        <span />
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
                      </div>

                      {/* Rows */}
                      {filteredSwpProjects.map((saved) => {
                        const isExpanded = expandedSwpId === saved.id;
                        return (
                          <div key={saved.id}>
                            <button
                              onClick={() => toggleWithScroll(setExpandedSwpId, expandedSwpId, saved.id)}
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
                                {saved.project.employer}
                              </span>
                              <span style={{ textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600, color: school.brandColorLight }}>
                                {saved.project.partnership_type}
                              </span>
                            </button>
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                                transition={{ duration: 0.25 }}
                                style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                              >
                                <div style={{ padding: "16px 20px 24px" }}>
                                  <SwpArtifact
                                    project={saved.project}
                                    streamedSections={saved.project.sections}
                                    lmiContext={saved.project.lmi_context}
                                    brandColor={school.brandColorLight}
                                    isStreaming={false}
                                  />
                                  <button
                                    onClick={() => {
                                      removeSwpProject(school.name, saved.id);
                                      setSavedSwpProjects(getSavedSwpProjects(school.name));
                                      setExpandedSwpId(null);
                                    }}
                                    style={{
                                      marginTop: "16px", fontFamily: FONT, fontSize: "11px", cursor: "pointer",
                                      border: "1px solid rgba(255,255,255,0.08)", borderRadius: "4px",
                                      background: "transparent", color: "rgba(255,255,255,0.3)", padding: "4px 10px",
                                    }}
                                  >Remove</button>
                                </div>
                              </motion.div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
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
              {/* ── Generating ── */}
              {phase === "generating" && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "16px" }}>
                  <div style={{ width: "32px", height: "32px", border: "3px solid rgba(255,255,255,0.08)", borderTopColor: school.brandColorLight, borderRadius: "50%", animation: "spin 1s linear infinite" }} />
                  <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                  <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>
                    Drafting SWP project proposal for NOVA...
                  </p>
                </div>
              )}

              {/* ── Streaming + Complete ── */}
              {(phase === "streaming" || phase === "complete") && (
                <div style={{ maxWidth: "700px", margin: "0 auto" }}>
                  <AnimatePresence>
                    {(streamedSections.length > 0 || swpProject) && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
                        <SwpArtifact
                          project={swpProject}
                          streamedSections={streamedSections}
                          lmiContext={lmiContext}
                          brandColor={school.brandColorLight}
                          isStreaming={phase === "streaming"}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {phase === "complete" && swpProject && (
                    <div style={{ display: "flex", gap: "10px", marginTop: "24px" }}>
                      <button
                        onClick={() => {
                          if (!swpSaved && selectedPartnership) {
                            saveSwpProject(school.name, swpProject, selectedPartnership.id);
                            setSwpSaved(true);
                          }
                        }}
                        disabled={swpSaved}
                        style={{
                          padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 600,
                          cursor: swpSaved ? "default" : "pointer", border: "none",
                          background: swpSaved ? "rgba(74,222,128,0.15)" : school.brandColorLight,
                          color: swpSaved ? "rgba(74,222,128,0.9)" : "#ffffff",
                        }}
                      >{swpSaved ? "SWP Document Saved" : "Save SWP Document"}</button>
                      <button onClick={handleReject}
                        style={{
                          padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
                          cursor: "pointer", border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.06)", color: "rgba(248,113,113,0.8)",
                        }}
                      >Reject &amp; Revise</button>
                    </div>
                  )}

                  {phase === "complete" && swpError && (
                    <div style={{ padding: "16px", background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: "8px", marginTop: "24px" }}>
                      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(248,113,113,0.9)", margin: "0 0 8px" }}>Failed to generate: {swpError}</p>
                      <button onClick={() => { if (selectedPartnership) handleDraft(selectedPartnership); }}
                        style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
                        Retry
                      </button>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
