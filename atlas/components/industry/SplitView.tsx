"use client";

import { useState, useEffect, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployerDetail, getEmployerPipeline } from "@/lib/api";
import type { ApiPartnershipOpportunity, ApiEmployerDetail, ApiTargetedProposal } from "@/lib/api";
import PartnershipContext from "./PartnershipContext";
import ProposalCard from "@/components/domains/ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  employer: ApiPartnershipOpportunity;
  phase: "split-view" | "generating" | "complete";
  objective: string;
  onObjectiveChange: (v: string) => void;
  onGenerate: () => void;
  onReject: () => void;
  proposal: ApiTargetedProposal | null;
  proposalError: string | null;
};

function deriveObjectiveSuggestions(employer: ApiPartnershipOpportunity): string[] {
  const suggestions: string[] = [];

  if (employer.top_occupation && employer.top_wage) {
    suggestions.push(
      `Build a pipeline for ${employer.top_occupation} roles ($${employer.top_wage.toLocaleString()}/yr)`
    );
  }

  if (employer.alignment_score > 5) {
    suggestions.push(
      `Create an internship pipeline leveraging ${employer.alignment_score} aligned skills`
    );
  }

  if (employer.gap_skills.length > 3) {
    const topGaps = employer.gap_skills.slice(0, 3).join(", ");
    suggestions.push(
      `Close skill gaps in ${topGaps} through advisory partnership`
    );
  }

  if (employer.sector) {
    suggestions.push(
      `Establish a ${employer.sector} workforce development partnership`
    );
  }

  return suggestions.slice(0, 4);
}

export default function SplitView({
  school, employer, phase, objective, onObjectiveChange, onGenerate, onReject, proposal, proposalError,
}: Props) {
  const [detail, setDetail] = useState<ApiEmployerDetail | null>(null);
  const [pipelineSize, setPipelineSize] = useState<number | null>(null);

  useEffect(() => {
    getEmployerDetail(employer.name, school.name).then(setDetail).catch(() => {});
    getEmployerPipeline(employer.name, school.name).then((d) => setPipelineSize(d.pipeline_size)).catch(() => {});
  }, [employer.name, school.name]);

  const suggestions = useMemo(() => deriveObjectiveSuggestions(employer), [employer]);

  return (
    <div style={{ display: "flex", width: "100%", minHeight: "calc(100vh - 80px)" }}>

      {/* ── Left Panel: Conversation ── */}
      <div style={{
        width: "40%", padding: "48px 36px", display: "flex", flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)",
      }}>
        {/* System message */}
        <div style={{ marginBottom: "32px" }}>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, margin: "0 0 8px" }}>
            You&apos;ve selected <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{employer.name}</span>.
            Let&apos;s build a partnership proposal.
          </p>
        </div>

        {/* Objective prompt */}
        <div style={{ marginBottom: "24px" }}>
          <h3 style={{ fontFamily: FONT, fontSize: "16px", fontWeight: 600, color: "#f0eef4", margin: "0 0 8px" }}>
            What is your strategic objective?
          </h3>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", lineHeight: 1.5, margin: 0 }}>
            e.g., &ldquo;Build a clinical placement pipeline for our Nursing students&rdquo; or
            &ldquo;Establish an advisory board to align our CS curriculum with industry needs&rdquo;
          </p>
        </div>

        {/* Suggestion chips */}
        {phase === "split-view" && suggestions.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "20px" }}>
            {suggestions.map((s) => (
              <button key={s} onClick={() => onObjectiveChange(s)}
                style={{
                  fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)",
                  background: "transparent", border: `1px solid ${school.brandColorLight}30`,
                  borderRadius: "100px", padding: "7px 14px", cursor: "pointer",
                  transition: "background 0.15s, color 0.15s, border-color 0.15s",
                  textAlign: "left", lineHeight: 1.4,
                }}
                onMouseEnter={(e) => { const el = e.currentTarget; el.style.background = `${school.brandColorLight}15`; el.style.borderColor = `${school.brandColorLight}40`; el.style.color = school.brandColorLight; }}
                onMouseLeave={(e) => { const el = e.currentTarget; el.style.background = "transparent"; el.style.borderColor = `${school.brandColorLight}30`; el.style.color = "rgba(255,255,255,0.5)"; }}
              >{s}</button>
            ))}
          </div>
        )}

        {/* Objective input */}
        {phase === "split-view" && (
          <>
            <textarea
              value={objective}
              onChange={(e) => onObjectiveChange(e.target.value)}
              placeholder="Describe your strategic objective..."
              rows={4}
              style={{
                width: "100%", padding: "14px 18px", fontFamily: FONT, fontSize: "14px",
                color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)", borderRadius: "12px",
                outline: "none", resize: "vertical", lineHeight: 1.6,
                transition: "border-color 0.2s, box-shadow 0.2s",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
            />
            <button
              onClick={onGenerate}
              disabled={!objective.trim()}
              style={{
                marginTop: "16px", width: "100%", padding: "14px 24px", borderRadius: "8px",
                fontFamily: FONT, fontSize: "14px", fontWeight: 600,
                cursor: objective.trim() ? "pointer" : "default", border: "none",
                background: objective.trim() ? school.brandColorLight : "rgba(255,255,255,0.06)",
                color: objective.trim() ? "#ffffff" : "rgba(255,255,255,0.25)",
                transition: "opacity 0.15s, background 0.2s",
              }}
              onMouseEnter={(e) => { if (objective.trim()) e.currentTarget.style.opacity = "0.85"; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
            >
              Generate Proposal
            </button>
          </>
        )}

        {/* Generating status */}
        {phase === "generating" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", padding: "32px 0" }}>
            <div style={{
              width: "28px", height: "28px",
              border: "3px solid rgba(255,255,255,0.1)", borderTopColor: school.brandColorLight,
              borderRadius: "50%", animation: "spin 1s linear infinite",
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.4)", textAlign: "center" }}>
              Analyzing alignment and generating proposal...
            </p>
            <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
              This may take 15-30 seconds
            </p>
          </div>
        )}

        {/* Complete — summary + actions */}
        {phase === "complete" && proposal && (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ padding: "16px", background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: "8px" }}>
              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(74,222,128,0.8)", margin: 0 }}>
                Proposal generated for {employer.name}.
              </p>
            </div>
            <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.35)", lineHeight: 1.5 }}>
              Your strategic objective: &ldquo;{objective}&rdquo;
            </p>

            {/* Post-generation action buttons */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <button
                onClick={() => {}}
                style={{
                  padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 600,
                  cursor: "pointer", border: "none", background: school.brandColorLight, color: "#ffffff",
                  transition: "opacity 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
              >
                Save Proposal
              </button>
              <button
                onClick={onReject}
                style={{
                  padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
                  cursor: "pointer", border: "1px solid rgba(248,113,113,0.3)", background: "rgba(248,113,113,0.06)",
                  color: "rgba(248,113,113,0.8)", transition: "background 0.15s",
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
                Refine (coming soon)
              </button>
              <button disabled title="Coming soon — Google Docs export via MCP"
                style={{
                  padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
                  cursor: "default", border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                Export to Google Docs
              </button>
            </div>
          </div>
        )}

        {/* Complete — error */}
        {phase === "complete" && proposalError && (
          <div style={{ padding: "16px", background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", borderRadius: "8px" }}>
            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(248,113,113,0.9)", margin: "0 0 8px" }}>
              Failed to generate proposal: {proposalError}
            </p>
            <button onClick={onGenerate}
              style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
              Retry
            </button>
          </div>
        )}
      </div>

      {/* ── Right Panel: Context → Proposal ── */}
      <div style={{
        width: "60%", background: "rgba(255,255,255,0.02)",
        padding: "48px 36px", overflowY: "auto", maxHeight: "calc(100vh - 80px)",
      }}>
        <AnimatePresence mode="wait">
          {phase === "split-view" && (
            <motion.div key="context" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
              <PartnershipContext employer={employer} detail={detail} pipelineSize={pipelineSize} school={school} />
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
                Generating {employer.name} partnership proposal...
              </p>
            </motion.div>
          )}

          {phase === "complete" && proposal && (
            <motion.div key="proposal" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <ProposalCard proposal={proposal} brandColor={school.brandColorLight} onDismiss={onReject} />
            </motion.div>
          )}

          {phase === "complete" && proposalError && !proposal && (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "16px" }}>
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(248,113,113,0.8)" }}>
                Failed to generate proposal
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
