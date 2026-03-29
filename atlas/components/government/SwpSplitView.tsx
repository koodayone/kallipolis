"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import type { ApiTargetedProposal, ApiLmiContext, ApiSwpProject, ApiSwpSection } from "@/lib/api";
import { saveSwpProject } from "@/lib/savedProposals";
import SwpContextPanel from "./SwpContextPanel";
import SwpArtifact from "./SwpArtifact";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const GOALS = [
  { key: "Completion", label: "Completion", desc: "Increase credential and certificate attainment" },
  { key: "Transfer", label: "Transfer", desc: "Increase transfer to UC or CSU" },
  { key: "Workforce", label: "Workforce", desc: "Increase employment in field of study" },
  { key: "Unit Accumulation", label: "Unit Accumulation", desc: "Decrease excess units for associate degree" },
];

const SWP_METRICS: Record<string, string[]> = {
  Completion: [
    "Completed a Degree or Certificate",
    "Attained Apprenticeship Journey Status",
    "Completed a Noncredit Workforce Milestone",
  ],
  Transfer: [
    "Transfer to Four-Year Institution",
  ],
  Workforce: [
    "Employed in Field of Study",
    "Attained a Living Wage",
    "Median Annual Earnings",
    "Median Change in Earnings",
    "Job Closely Related to Field of Study",
  ],
  "Unit Accumulation": [
    "Completed a Degree or Certificate",
  ],
};

type Props = {
  school: SchoolConfig;
  proposal: ApiTargetedProposal;
  partnershipId: string;
  lmiContext: ApiLmiContext | null;
  phase: "split-view" | "generating" | "streaming" | "complete";
  // Coordinator inputs
  projectFraming: string;
  onProjectFramingChange: (v: string) => void;
  goal: string;
  onGoalChange: (v: string) => void;
  metrics: string[];
  onMetricsChange: (v: string[]) => void;
  apprenticeship: boolean;
  onApprenticeshipChange: (v: boolean) => void;
  wbl: boolean;
  onWblChange: (v: boolean) => void;
  // Actions
  onGenerate: () => void;
  onReject: () => void;
  // Result
  streamedSections: ApiSwpSection[];
  swpProject: ApiSwpProject | null;
  swpError: string | null;
};

function deriveSwpSuggestions(proposal: ApiTargetedProposal): string[] {
  const suggestions: string[] = [];

  if (proposal.skill_gaps.length > 0) {
    const topGap = proposal.skill_gaps[0].skill;
    suggestions.push(`Close regional skill gap in ${topGap} through employer partnership`);
  }

  const depts = [...new Set(proposal.curriculum_alignment.map(a => a.department))];
  if (depts.length > 0) {
    suggestions.push(`Expand ${depts[0]} program capacity to meet regional demand`);
  }

  if (proposal.partnership_type.includes("Internship") || proposal.partnership_type.includes("Co-op")) {
    suggestions.push(`Create work-based learning pathway at ${proposal.employer}`);
  }

  if (proposal.partnership_type.includes("Apprenticeship")) {
    suggestions.push(`Launch registered apprenticeship with ${proposal.employer}`);
  }

  if (proposal.economic_impact.occupations.length > 0) {
    const topOcc = proposal.economic_impact.occupations[0];
    if (topOcc.annual_wage) {
      suggestions.push(`Build pipeline for ${topOcc.title} roles ($${topOcc.annual_wage.toLocaleString()}/yr)`);
    }
  }

  return suggestions.slice(0, 4);
}

export default function SwpSplitView({
  school, proposal, partnershipId, lmiContext, phase,
  projectFraming, onProjectFramingChange,
  goal, onGoalChange, metrics, onMetricsChange,
  apprenticeship, onApprenticeshipChange, wbl, onWblChange,
  onGenerate, onReject, streamedSections, swpProject, swpError,
}: Props) {
  const suggestions = useMemo(() => deriveSwpSuggestions(proposal), [proposal]);
  const availableMetrics = SWP_METRICS[goal] || [];

  const handleMetricToggle = (metric: string) => {
    if (metrics.includes(metric)) {
      onMetricsChange(metrics.filter(m => m !== metric));
    } else {
      onMetricsChange([...metrics, metric]);
    }
  };

  return (
    <div style={{ display: "flex", width: "100%", minHeight: "calc(100vh - 80px)" }}>

      {/* ── Left Panel: Coordinator Input ── */}
      <div style={{
        width: "40%", padding: "48px 36px", display: "flex", flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)",
      }}>
        {/* System message */}
        <div style={{ marginBottom: "28px" }}>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, margin: 0 }}>
            Building SWP project from your{" "}
            <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{proposal.partnership_type}</span>
            {" "}partnership with{" "}
            <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{proposal.employer}</span>.
          </p>
        </div>

        {phase === "split-view" && (
          <>
            {/* Project framing */}
            <div style={{ marginBottom: "16px" }}>
              <h3 style={{ fontFamily: FONT, fontSize: "15px", fontWeight: 600, color: "#f0eef4", margin: "0 0 6px" }}>
                What is the institutional need?
              </h3>
              <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", lineHeight: 1.5, margin: 0 }}>
                Describe the project goal in your own words. This becomes the needs narrative.
              </p>
            </div>

            {/* Suggestion chips */}
            {suggestions.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>
                {suggestions.map((s) => (
                  <button key={s} onClick={() => onProjectFramingChange(s)}
                    style={{
                      fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)",
                      background: "transparent", border: `1px solid ${school.brandColorLight}30`,
                      borderRadius: "100px", padding: "7px 14px", cursor: "pointer",
                      transition: "background 0.15s, color 0.15s", textAlign: "left", lineHeight: 1.4,
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = `${school.brandColorLight}15`; e.currentTarget.style.color = school.brandColorLight; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.5)"; }}
                  >{s}</button>
                ))}
              </div>
            )}

            <textarea
              value={projectFraming}
              onChange={(e) => onProjectFramingChange(e.target.value)}
              placeholder="Describe the institutional need this project addresses..."
              rows={3}
              style={{
                width: "100%", padding: "14px 18px", fontFamily: FONT, fontSize: "14px",
                color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                outline: "none", resize: "vertical", lineHeight: 1.6, marginBottom: "20px",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; }}
            />

            {/* Goal selector */}
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: "8px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Vision for Success Goal
              </label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {GOALS.map((g) => (
                  <button key={g.key} onClick={() => { onGoalChange(g.key); onMetricsChange([]); }}
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
                      <input
                        type="checkbox"
                        checked={metrics.includes(m)}
                        onChange={() => handleMetricToggle(m)}
                        style={{ accentColor: school.brandColorLight }}
                      />
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>{m}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Scope flags */}
            <div style={{ marginBottom: "20px" }}>
              <label style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.5)", display: "block", marginBottom: "8px", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Program Classification
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input type="checkbox" checked={apprenticeship} onChange={(e) => onApprenticeshipChange(e.target.checked)} style={{ accentColor: school.brandColorLight }} />
                  <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Apprenticeship program</span>
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
                  <input type="checkbox" checked={wbl} onChange={(e) => onWblChange(e.target.checked)} style={{ accentColor: school.brandColorLight }} />
                  <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>Work-based learning component</span>
                </label>
              </div>
            </div>

            {/* Generate button */}
            <button
              onClick={onGenerate}
              disabled={!projectFraming.trim() || metrics.length === 0}
              style={{
                width: "100%", padding: "14px 24px", borderRadius: "8px",
                fontFamily: FONT, fontSize: "14px", fontWeight: 600,
                cursor: projectFraming.trim() && metrics.length > 0 ? "pointer" : "default",
                border: "none",
                background: projectFraming.trim() && metrics.length > 0 ? school.brandColorLight : "rgba(255,255,255,0.06)",
                color: projectFraming.trim() && metrics.length > 0 ? "#ffffff" : "rgba(255,255,255,0.25)",
                transition: "opacity 0.15s, background 0.2s",
              }}
              onMouseEnter={(e) => { if (projectFraming.trim() && metrics.length > 0) e.currentTarget.style.opacity = "0.85"; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
            >
              Generate SWP Document
            </button>
          </>
        )}

        {/* Generating / Streaming status */}
        {(phase === "generating" || phase === "streaming") && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", padding: "32px 0" }}>
            <div style={{
              width: "28px", height: "28px",
              border: "3px solid rgba(255,255,255,0.1)", borderTopColor: school.brandColorLight,
              borderRadius: "50%", animation: "spin 1s linear infinite",
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.4)", textAlign: "center" }}>
              {phase === "generating" ? "Preparing LMI data..." : `Generating sections... (${streamedSections.length}/8)`}
            </p>
          </div>
        )}

        {/* Complete — actions */}
        {phase === "complete" && swpProject && (
          <SwpCompleteActions
            school={school}
            swpProject={swpProject}
            partnershipId={partnershipId}
            onReject={onReject}
          />
        )}

        {/* Complete — error */}
        {phase === "complete" && swpError && (
          <div style={{ padding: "16px", background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: "8px" }}>
            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(248,113,113,0.9)", margin: "0 0 8px" }}>
              Failed to generate SWP document: {swpError}
            </p>
            <button onClick={onGenerate}
              style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
              Retry
            </button>
          </div>
        )}
      </div>

      {/* ── Right Panel: Context → Artifact ── */}
      <div style={{
        width: "60%", background: "rgba(255,255,255,0.02)",
        padding: "48px 36px", overflowY: "auto", maxHeight: "calc(100vh - 80px)",
      }}>
        <AnimatePresence mode="wait">
          {phase === "split-view" && (
            <motion.div key="context" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
              <SwpContextPanel lmiContext={lmiContext} proposal={proposal} brandColor={school.brandColorLight} />
            </motion.div>
          )}

          {phase === "generating" && (
            <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "16px" }}>
              <div style={{
                width: "36px", height: "36px",
                border: "3px solid rgba(255,255,255,0.08)", borderTopColor: school.brandColorLight,
                borderRadius: "50%", animation: "spin 1s linear infinite",
              }} />
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>
                Preparing LMI data...
              </p>
            </motion.div>
          )}

          {(phase === "streaming" || (phase === "complete" && swpProject)) && (
            <motion.div key="streaming" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
              <SwpArtifact
                project={swpProject}
                streamedSections={streamedSections}
                lmiContext={lmiContext}
                brandColor={school.brandColorLight}
                isStreaming={phase === "streaming"}
              />
            </motion.div>
          )}

          {phase === "complete" && swpError && !swpProject && (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px" }}>
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(248,113,113,0.8)" }}>
                Failed to generate SWP document
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SwpCompleteActions({ school, swpProject, partnershipId, onReject }: {
  school: SchoolConfig;
  swpProject: ApiSwpProject;
  partnershipId: string;
  onReject: () => void;
}) {
  const [saved, setSavedState] = useState(false);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ padding: "16px", background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: "8px" }}>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(74,222,128,0.8)", margin: 0 }}>
          SWP project document generated for {swpProject.employer}.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <button
          onClick={() => {
            if (!saved) {
              saveSwpProject(school.name, swpProject, partnershipId);
              setSavedState(true);
            }
          }}
          disabled={saved}
          style={{
            padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 600,
            cursor: saved ? "default" : "pointer", border: "none",
            background: saved ? "rgba(74,222,128,0.15)" : school.brandColorLight,
            color: saved ? "rgba(74,222,128,0.9)" : "#ffffff",
            transition: "opacity 0.15s, background 0.2s",
          }}
          onMouseEnter={(e) => { if (!saved) e.currentTarget.style.opacity = "0.85"; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
        >
          {saved ? "SWP Document Saved" : "Save SWP Document"}
        </button>
        <button onClick={onReject}
          style={{
            padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
            cursor: "pointer", border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.06)",
            color: "rgba(248,113,113,0.8)",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(248,113,113,0.1)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(248,113,113,0.06)")}
        >
          Reject &amp; Revise
        </button>
        <button disabled
          style={{
            padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
            cursor: "default", border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
            color: "rgba(255,255,255,0.2)",
          }}
        >
          Export to NOVA (coming soon)
        </button>
      </div>
    </div>
  );
}
