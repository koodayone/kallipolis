"use client";

import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import type { ApiPartnershipOpportunity, ApiTargetedProposal } from "@/college-atlas/partnerships/api";
import ProposalCard from "./ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  employer: ApiPartnershipOpportunity;
  phase: "generating" | "complete";
  onRetry: () => void;
  onReject: () => void;
  proposal: ApiTargetedProposal | null;
  proposalError: string | null;
};

export default function ProposalFlow({
  school, employer, phase, onRetry, onReject, proposal, proposalError,
}: Props) {
  return (
    <div style={{ maxWidth: "640px", margin: "0 auto", padding: "48px 40px" }}>
      <AnimatePresence mode="wait">

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
              Generating {employer.name} partnership opportunity...
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
            <button onClick={onRetry}
              style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
              Retry
            </button>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
