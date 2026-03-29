"use client";

import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployerDetail, getEmployerPipeline } from "@/lib/api";
import type { ApiPartnershipOpportunity, ApiEmployerDetail, ApiTargetedProposal } from "@/lib/api";
import { saveProposal } from "@/lib/savedProposals";
import PartnershipContext from "./PartnershipContext";
import ProposalCard from "@/components/domains/ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const ENGAGEMENT_TYPES = [
  { key: "internship", title: "Internship Pipeline", description: "Place students at this employer for structured work rotations" },
  { key: "apprenticeship", title: "Apprenticeship Program", description: "Create a registered, paid, multi-year career pathway" },
  { key: "curriculum_codesign", title: "Curriculum Co-Design", description: "Partner with this employer to shape program content" },
  { key: "hiring_mou", title: "Hiring MOU", description: "Secure a commitment from this employer to hire graduates" },
  { key: "advisory_board", title: "Advisory Board", description: "Establish ongoing strategic guidance for your programs" },
];

type Props = {
  school: SchoolConfig;
  employer: ApiPartnershipOpportunity;
  phase: "split-view" | "generating" | "complete";
  engagementType: string;
  onEngagementTypeChange: (v: string) => void;
  onGenerate: () => void;
  onReject: () => void;
  proposal: ApiTargetedProposal | null;
  proposalError: string | null;
};

export default function SplitView({
  school, employer, phase, engagementType, onEngagementTypeChange, onGenerate, onReject, proposal, proposalError,
}: Props) {
  const [detail, setDetail] = useState<ApiEmployerDetail | null>(null);
  const [proposalSaved, setProposalSaved] = useState(false);
  const [pipelineSize, setPipelineSize] = useState<number | null>(null);

  useEffect(() => {
    getEmployerDetail(employer.name, school.name).then(setDetail).catch(() => {});
    getEmployerPipeline(employer.name, school.name).then((d) => setPipelineSize(d.pipeline_size)).catch(() => {});
  }, [employer.name, school.name]);

  return (
    <div style={{ display: "flex", width: "100%", minHeight: "calc(100vh - 80px)" }}>

      {/* ── Left Panel ── */}
      <div style={{
        width: "40%", padding: "48px 36px", display: "flex", flexDirection: "column",
        borderRight: "1px solid rgba(255,255,255,0.06)",
      }}>
        {/* System message */}
        <div style={{ marginBottom: "32px" }}>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, margin: 0 }}>
            You&apos;ve selected <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{employer.name}</span>.
            Let&apos;s build a partnership proposal.
          </p>
        </div>

        {/* Engagement type selection */}
        {phase === "split-view" && (
          <>
            <div style={{ marginBottom: "20px" }}>
              <h3 style={{ fontFamily: FONT, fontSize: "16px", fontWeight: 600, color: "#f0eef4", margin: "0 0 6px" }}>
                What kind of partnership?
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
              {ENGAGEMENT_TYPES.map((et) => {
                const selected = engagementType === et.key;
                return (
                  <button
                    key={et.key}
                    onClick={() => onEngagementTypeChange(selected ? "" : et.key)}
                    style={{
                      textAlign: "left", padding: "16px 18px", borderRadius: "10px", cursor: "pointer",
                      border: `1px solid ${selected ? school.brandColorLight + "60" : "rgba(255,255,255,0.08)"}`,
                      background: selected ? `${school.brandColorLight}10` : "rgba(255,255,255,0.02)",
                      transition: "border-color 0.15s, background 0.15s",
                    }}
                    onMouseEnter={(e) => { if (!selected) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"; e.currentTarget.style.background = "rgba(255,255,255,0.04)"; } }}
                    onMouseLeave={(e) => { if (!selected) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; e.currentTarget.style.background = "rgba(255,255,255,0.02)"; } }}
                  >
                    <div style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 600, color: selected ? school.brandColorLight : "rgba(255,255,255,0.85)", marginBottom: "4px" }}>
                      {et.title}
                    </div>
                    <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", lineHeight: 1.5 }}>
                      {et.description}
                    </div>
                  </button>
                );
              })}
            </div>

            <button
              onClick={onGenerate}
              disabled={!engagementType}
              style={{
                width: "100%", padding: "14px 24px", borderRadius: "8px",
                fontFamily: FONT, fontSize: "14px", fontWeight: 600,
                cursor: engagementType ? "pointer" : "default", border: "none",
                background: engagementType ? school.brandColorLight : "rgba(255,255,255,0.06)",
                color: engagementType ? "#ffffff" : "rgba(255,255,255,0.25)",
                transition: "opacity 0.15s, background 0.2s",
              }}
              onMouseEnter={(e) => { if (engagementType) e.currentTarget.style.opacity = "0.85"; }}
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

            {/* Post-generation action buttons */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <button
                onClick={() => {
                  if (!proposalSaved && proposal) {
                    saveProposal(school.name, proposal, engagementType, "saved");
                    setProposalSaved(true);
                  }
                }}
                disabled={proposalSaved}
                style={{
                  padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 600,
                  cursor: proposalSaved ? "default" : "pointer", border: "none",
                  background: proposalSaved ? "rgba(74,222,128,0.15)" : school.brandColorLight,
                  color: proposalSaved ? "rgba(74,222,128,0.9)" : "#ffffff",
                  transition: "opacity 0.15s, background 0.2s",
                }}
                onMouseEnter={(e) => { if (!proposalSaved) e.currentTarget.style.opacity = "0.85"; }}
                onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
              >
                {proposalSaved ? "Proposal Saved" : "Save Proposal"}
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
              <ProposalCard proposal={proposal} brandColor={school.brandColorLight} onDismiss={onReject} collegeId={school.name} engagementType={engagementType} />
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
