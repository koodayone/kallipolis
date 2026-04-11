"use client";

import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import type { ApiPartnershipOpportunity, ApiTargetedProposal } from "@/lib/api";
import ProposalCard from "./ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const ENGAGEMENT_TYPES = [
  { key: "internship", title: "Internship Pipeline", description: "Place students at this employer for structured work rotations" },
  { key: "curriculum_codesign", title: "Curriculum Co-Design", description: "Partner with this employer to shape program content" },
  { key: "advisory_board", title: "Advisory Board", description: "Establish ongoing strategic guidance for your programs" },
];

type Props = {
  school: SchoolConfig;
  employer: ApiPartnershipOpportunity;
  phase: "draft" | "generating" | "complete";
  engagementType: string;
  onEngagementTypeChange: (v: string) => void;
  onGenerate: () => void;
  onReject: () => void;
  proposal: ApiTargetedProposal | null;
  proposalError: string | null;
};

export default function ProposalFlow({
  school, employer, phase, engagementType, onEngagementTypeChange, onGenerate, onReject, proposal, proposalError,
}: Props) {
  return (
    <div style={{ maxWidth: "640px", margin: "0 auto", padding: "48px 40px" }}>
      <AnimatePresence mode="wait">

        {/* ── Draft: engagement type selection ── */}
        {phase === "draft" && (
          <motion.div key="draft" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
            <div style={{ marginBottom: "32px" }}>
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, margin: 0 }}>
                You&apos;ve selected <span style={{ color: school.brandColorLight, fontWeight: 600 }}>{employer.name}</span>.
              </p>
            </div>

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
                color: engagementType ? "#1a1a2e" : "rgba(255,255,255,0.25)",
                transition: "opacity 0.15s, background 0.2s",
              }}
              onMouseEnter={(e) => { if (engagementType) e.currentTarget.style.opacity = "0.85"; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
            >
              Generate Proposal
            </button>
          </motion.div>
        )}

        {/* ── Generating ── */}
        {phase === "generating" && (
          <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "16px" }}>
            <div style={{
              width: "32px", height: "32px",
              border: "3px solid rgba(255,255,255,0.08)", borderTopColor: school.brandColorLight,
              borderRadius: "50%", animation: "spin 1s linear infinite",
            }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>
              Generating {employer.name} partnership proposal...
            </p>
            <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
              This may take 15-30 seconds
            </p>
          </motion.div>
        )}

        {/* ── Complete: Proposal ── */}
        {phase === "complete" && proposal && (
          <motion.div key="proposal" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <ProposalCard
              proposal={proposal}
              brandColor={school.brandColorLight}
              onDismiss={onReject}
              onReject={onReject}
              collegeId={school.name}
              engagementType={engagementType}
            />
          </motion.div>
        )}

        {/* ── Complete: Error ── */}
        {phase === "complete" && proposalError && !proposal && (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "300px", gap: "16px" }}>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(248,113,113,0.8)", margin: "0 0 8px" }}>
              Failed to generate proposal: {proposalError}
            </p>
            <button onClick={onGenerate}
              style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
              Retry
            </button>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
