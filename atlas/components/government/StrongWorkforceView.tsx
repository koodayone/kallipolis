"use client";

import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getSwpLmiContext, streamSwpProject } from "@/lib/api";
import type { ApiLmiContext, ApiSwpProject, ApiSwpSection, SwpProjectRequest } from "@/lib/api";
import { getSavedProposals, getSavedSwpProjects, saveSwpProject, removeSwpProject, type SavedProposal, type SavedSwpProject } from "@/lib/savedProposals";
import LeafHeader from "@/components/ui/LeafHeader";
import RisingSun from "@/components/ui/RisingSun";
import SwpArtifact from "./SwpArtifact";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type SwpPhase = "selection" | "params" | "generating" | "streaming" | "complete";
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

const GOALS = [
  { key: "Completion", label: "Completion" },
  { key: "Transfer", label: "Transfer" },
  { key: "Workforce", label: "Workforce" },
  { key: "Unit Accumulation", label: "Unit Accumulation" },
];

const SWP_METRICS: Record<string, string[]> = {
  Completion: ["Completed a Degree or Certificate", "Attained Apprenticeship Journey Status", "Completed a Noncredit Workforce Milestone"],
  Transfer: ["Transfer to Four-Year Institution"],
  Workforce: ["Employed in Field of Study", "Attained a Living Wage", "Median Annual Earnings", "Median Change in Earnings", "Job Closely Related to Field of Study"],
  "Unit Accumulation": ["Completed a Degree or Certificate"],
};

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function StrongWorkforceView({ school, onBack }: Props) {
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

  const handleSelectPartnership = useCallback(async (saved: SavedProposal) => {
    setSelectedPartnership(saved);
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);

    const defaults = PARTNERSHIP_DEFAULTS[saved.engagementType] || {
      goal: "Workforce", metrics: ["Employed in Field of Study"], apprenticeship: false, wbl: false,
    };
    setGoal(defaults.goal);
    setMetrics(defaults.metrics);
    setApprenticeship(defaults.apprenticeship);
    setWbl(defaults.wbl);
    setPhase("params");

    try {
      const lmi = await getSwpLmiContext(saved.proposal.employer, school.name);
      setLmiContext(lmi);
    } catch {
      setLmiContext(null);
    }
  }, [school.name]);

  const handleGenerate = useCallback(() => {
    if (!selectedPartnership || metrics.length === 0) return;
    setPhase("generating");
    setSwpProject(null);
    setStreamedSections([]);
    setSwpError(null);

    const req: SwpProjectRequest = {
      employer: selectedPartnership.proposal.employer,
      college: school.name,
      partnership_type: selectedPartnership.proposal.partnership_type,
      executive_summary: selectedPartnership.proposal.executive_summary,
      curriculum_alignment: selectedPartnership.proposal.curriculum_alignment,
      skill_gaps: selectedPartnership.proposal.skill_gaps,
      student_pipeline: selectedPartnership.proposal.student_pipeline,
      economic_impact: selectedPartnership.proposal.economic_impact,
      project_framing: `${goal} goal targeting ${metrics.join(", ")} through ${selectedPartnership.proposal.partnership_type} with ${selectedPartnership.proposal.employer}`,
      goal,
      metrics,
      apprenticeship,
      work_based_learning: wbl,
    };

    streamSwpProject(
      req,
      (lmi) => { setLmiContext(lmi); setPhase("streaming"); },
      (section) => { setStreamedSections(prev => [...prev, section]); },
      () => { setPhase("complete"); },
      (err) => { setSwpError(err); setPhase("complete"); },
    );
  }, [selectedPartnership, goal, metrics, apprenticeship, wbl, school.name]);

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
    setPhase("params");
  }, []);

  const handleBackToSelection = useCallback(() => {
    setSelectedPartnership(null);
    setSwpProject(null);
    setSwpError(null);
    setStreamedSections([]);
    setPhase("selection");
  }, []);

  const [swpSaved, setSwpSaved] = useState(false);

  const availableMetrics = SWP_METRICS[goal] || [];

  return (
    <>
      <LeafHeader school={school} onBack={phase === "selection" ? onBack : handleBackToSelection} parentShape="dodecahedron" />

      <div style={{ maxWidth: "760px", margin: "0 auto", padding: "0 40px 80px" }}>

        {/* Build / Manage segmented control */}
        {phase === "selection" && (
          <div style={{ display: "flex", justifyContent: "center", marginBottom: "32px", paddingTop: "24px" }}>
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
        )}

        {/* Build mode header with sun + greeting */}
        {mode === "build" && phase === "selection" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", marginBottom: "24px" }}>
            <RisingSun style={{ width: "70px", height: "auto" }} />
            <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center", margin: 0 }}>
              SWP compliance{userName ? `, ${userName}` : ""}?
            </h1>
          </div>
        )}

        {/* ── Build Mode: Selection ── */}
        {mode === "build" && phase === "selection" && (
          <>
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
                        onClick={() => setExpandedBuildId(isExpanded ? null : saved.id)}
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
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}
                            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                          >
                            <div style={{ padding: "14px 20px 18px" }}>
                              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: "0 0 14px" }}>
                                {saved.proposal.partnership_type} partnership with {saved.proposal.employer}{saved.proposal.sector ? ` for the ${saved.proposal.sector} sector` : ""}.
                              </p>
                              <button
                                onClick={() => handleSelectPartnership(saved)}
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
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </>
            )}
          </>
        )}

        {/* ── Build Mode: SWP Parameters ── */}
        {mode === "build" && phase === "params" && selectedPartnership && (
          <div style={{ maxWidth: "640px", margin: "0 auto" }}>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, marginBottom: "28px" }}>
              Building SWP project from your{" "}
              <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{selectedPartnership.proposal.partnership_type}</span>
              {" "}partnership with{" "}
              <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{selectedPartnership.proposal.employer}</span>.
            </p>

            {/* Goal selector */}
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: "8px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Vision for Success Goal
              </label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {GOALS.map((g) => (
                  <button key={g.key} onClick={() => { setGoal(g.key); setMetrics([]); }}
                    style={{
                      fontFamily: FONT, fontSize: "12px", fontWeight: goal === g.key ? 600 : 400,
                      padding: "6px 14px", borderRadius: "6px", cursor: "pointer",
                      border: `1px solid ${goal === g.key ? school.brandColorLight + "60" : "rgba(255,255,255,0.10)"}`,
                      background: goal === g.key ? `${school.brandColorLight}15` : "transparent",
                      color: goal === g.key ? school.brandColorLight : "rgba(255,255,255,0.5)",
                    }}
                  >{g.label}</button>
                ))}
              </div>
            </div>

            {/* Metric checkboxes */}
            {availableMetrics.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <label style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: "8px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                  SWP Metrics
                </label>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {availableMetrics.map((m) => (
                    <label key={m} style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                      <input type="checkbox" checked={metrics.includes(m)}
                        onChange={() => setMetrics(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])}
                        style={{ accentColor: school.brandColorLight }}
                      />
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>{m}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Scope flags */}
            <div style={{ marginBottom: "24px" }}>
              <label style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: "8px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Program Classification
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input type="checkbox" checked={apprenticeship} onChange={(e) => setApprenticeship(e.target.checked)} style={{ accentColor: school.brandColorLight }} />
                  <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Apprenticeship program</span>
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input type="checkbox" checked={wbl} onChange={(e) => setWbl(e.target.checked)} style={{ accentColor: school.brandColorLight }} />
                  <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Work-based learning component</span>
                </label>
              </div>
            </div>

            <button onClick={handleGenerate} disabled={metrics.length === 0}
              style={{
                width: "100%", padding: "14px 24px", borderRadius: "8px",
                fontFamily: FONT, fontSize: "14px", fontWeight: 600,
                cursor: metrics.length > 0 ? "pointer" : "default", border: "none",
                background: metrics.length > 0 ? school.brandColorLight : "rgba(255,255,255,0.06)",
                color: metrics.length > 0 ? "#ffffff" : "rgba(255,255,255,0.25)",
              }}
            >
              Generate SWP Document
            </button>
          </div>
        )}

        {/* ── Build Mode: Generating ── */}
        {mode === "build" && phase === "generating" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "300px", gap: "16px" }}>
            <div style={{ width: "32px", height: "32px", border: "3px solid rgba(255,255,255,0.08)", borderTopColor: school.brandColorLight, borderRadius: "50%", animation: "spin 1s linear infinite" }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>Preparing SWP document...</p>
          </div>
        )}

        {/* ── Build Mode: Streaming + Complete ── */}
        {mode === "build" && (phase === "streaming" || phase === "complete") && (
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
                <button onClick={handleGenerate}
                  style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
                  Retry
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Manage Mode ── */}
        {mode === "manage" && phase === "selection" && (
          <>
            {savedSwpProjects.length === 0 ? (
              <div style={{ padding: "40px", textAlign: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" }}>
                <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>No saved SWP projects yet.</p>
                <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Generate and save an SWP document from the Build tab.</p>
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
                  <input type="text" value={manageQuery} onChange={(e) => setManageQuery(e.target.value)}
                    placeholder="Search SWP projects..."
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
                        onClick={() => setExpandedSwpId(isExpanded ? null : saved.id)}
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
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }}
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
                      </AnimatePresence>
                    </div>
                  );
                })}
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
