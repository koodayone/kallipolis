"use client";

import { useState, useEffect, useCallback } from "react";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getSwpLmiContext, streamSwpProject } from "@/lib/api";
import type { ApiLmiContext, ApiSwpProject, ApiSwpSection, SwpProjectRequest } from "@/lib/api";
import { getSavedProposals, type SavedProposal } from "@/lib/savedProposals";
import LeafHeader from "@/components/ui/LeafHeader";
import SwpSplitView from "./SwpSplitView";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type SwpPhase = "selection" | "split-view" | "generating" | "streaming" | "complete";

// Partnership type → default goal/metric/scope pre-fills
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

export default function StrongWorkforceView({ school, onBack }: Props) {
  const [phase, setPhase] = useState<SwpPhase>("selection");
  const [savedProposals, setSavedProposals] = useState<SavedProposal[]>([]);
  const [selectedPartnership, setSelectedPartnership] = useState<SavedProposal | null>(null);
  const [lmiContext, setLmiContext] = useState<ApiLmiContext | null>(null);
  const [swpProject, setSwpProject] = useState<ApiSwpProject | null>(null);
  const [streamedSections, setStreamedSections] = useState<ApiSwpSection[]>([]);
  const [swpError, setSwpError] = useState<string | null>(null);

  // Coordinator inputs
  const [projectFraming, setProjectFraming] = useState("");
  const [goal, setGoal] = useState("Workforce");
  const [metrics, setMetrics] = useState<string[]>([]);
  const [apprenticeship, setApprenticeship] = useState(false);
  const [wbl, setWbl] = useState(false);

  // Load saved partnerships on mount
  useEffect(() => {
    setSavedProposals(getSavedProposals(school.name));
  }, [school.name]);

  const handleSelectPartnership = useCallback(async (saved: SavedProposal) => {
    setSelectedPartnership(saved);
    setSwpProject(null);
    setSwpError(null);

    // Pre-fill from partnership type
    const defaults = PARTNERSHIP_DEFAULTS[saved.engagementType] || {
      goal: "Workforce", metrics: ["Employed in Field of Study"], apprenticeship: false, wbl: false,
    };
    setGoal(defaults.goal);
    setMetrics(defaults.metrics);
    setApprenticeship(defaults.apprenticeship);
    setWbl(defaults.wbl);
    setProjectFraming("");

    setPhase("split-view");

    // Fetch LMI context
    try {
      const lmi = await getSwpLmiContext(saved.proposal.employer, school.name);
      setLmiContext(lmi);
    } catch {
      setLmiContext(null);
    }
  }, [school.name]);

  const handleGenerate = useCallback(() => {
    if (!selectedPartnership || !projectFraming.trim() || metrics.length === 0) return;
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
      project_framing: projectFraming,
      goal,
      metrics,
      apprenticeship,
      work_based_learning: wbl,
    };

    streamSwpProject(
      req,
      (lmi) => {
        // LMI context arrives first — transition to streaming phase
        setLmiContext(lmi);
        setPhase("streaming");
      },
      (section) => {
        // Each section arrives as Claude completes it
        setStreamedSections(prev => [...prev, section]);
      },
      () => {
        // All sections done — build the complete project for save/export
        setPhase("complete");
      },
      (err) => { setSwpError(err); setPhase("complete"); },
    );
  }, [selectedPartnership, projectFraming, goal, metrics, apprenticeship, wbl, school.name]);

  // Build the complete SwpProject when streaming finishes (for save/export)
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
    setPhase("split-view");
  }, []);

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="dodecahedron" />

      {/* Phase 1: Selection */}
      {phase === "selection" && (
        <div style={{ maxWidth: "800px", margin: "0 auto", padding: "32px 40px 80px" }}>
          <div style={{ display: "flex", justifyContent: "center", paddingBottom: "16px" }}>
            <img src={school.logoPath} alt={school.name} style={{ height: "80px", width: "auto", objectFit: "contain" }} />
          </div>

          <h1 style={{
            fontFamily: FONT, fontSize: "22px", fontWeight: 600, color: "#f0eef4",
            letterSpacing: "-0.02em", marginBottom: "6px", textAlign: "center",
          }}>
            Strong Workforce Program
          </h1>
          <p style={{
            fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.4)",
            textAlign: "center", lineHeight: 1.6, marginBottom: "32px",
          }}>
            Select a saved partnership to translate into a NOVA-compatible SWP project document.
          </p>

          {savedProposals.length === 0 ? (
            <div style={{
              padding: "40px", textAlign: "center",
              background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: "8px",
            }}>
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>
                No saved partnerships yet.
              </p>
              <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>
                Visit the Industry domain to build and save a partnership proposal, then return here to generate an SWP project.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {savedProposals.map((saved) => {
                const p = saved.proposal;
                const depts = [...new Set(p.curriculum_alignment.map(a => a.department))];
                return (
                  <div key={saved.id} style={{
                    padding: "20px", background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px",
                    cursor: "pointer", transition: "border-color 0.15s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}40`; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; }}
                  onClick={() => handleSelectPartnership(saved)}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                      <div>
                        <h3 style={{ fontFamily: FONT, fontSize: "15px", fontWeight: 600, color: "rgba(255,255,255,0.9)", margin: "0 0 4px" }}>
                          {p.employer}
                        </h3>
                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <span style={{
                            padding: "2px 10px", borderRadius: "100px", fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                            background: `${school.brandColorLight}20`, color: school.brandColorLight, border: `1px solid ${school.brandColorLight}40`,
                          }}>{p.partnership_type}</span>
                          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                            {p.curriculum_alignment.length} skill connections · {depts.length} department{depts.length !== 1 ? "s" : ""}
                          </span>
                        </div>
                      </div>
                      <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>
                        {new Date(saved.savedAt).toLocaleDateString()}
                      </span>
                    </div>

                    <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", lineHeight: 1.5, margin: "0 0 12px" }}>
                      {p.executive_summary.slice(0, 200)}{p.executive_summary.length > 200 ? "..." : ""}
                    </p>

                    <button
                      onClick={(e) => { e.stopPropagation(); handleSelectPartnership(saved); }}
                      style={{
                        fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer",
                        border: `1px solid ${school.brandColorLight}40`, borderRadius: "6px",
                        background: `${school.brandColorLight}10`, color: school.brandColorLight,
                        padding: "6px 14px",
                      }}
                    >
                      Build SWP Project
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Phase 2+: Split View */}
      {phase !== "selection" && selectedPartnership && (
        <SwpSplitView
          school={school}
          proposal={selectedPartnership.proposal}
          partnershipId={selectedPartnership.id}
          lmiContext={lmiContext}
          phase={phase as "split-view" | "generating" | "streaming" | "complete"}
          projectFraming={projectFraming}
          onProjectFramingChange={setProjectFraming}
          goal={goal}
          onGoalChange={setGoal}
          metrics={metrics}
          onMetricsChange={setMetrics}
          apprenticeship={apprenticeship}
          onApprenticeshipChange={setApprenticeship}
          wbl={wbl}
          onWblChange={setWbl}
          onGenerate={handleGenerate}
          onReject={handleReject}
          streamedSections={streamedSections}
          swpProject={swpProject}
          swpError={swpError}
        />
      )}
    </>
  );
}
