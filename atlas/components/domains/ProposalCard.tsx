"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ApiTargetedProposal } from "@/lib/api";
import { saveProposal, removeProposal, updateProposalStatus, type SavedProposal } from "@/lib/savedProposals";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type CardState = "default" | "saved" | "dismissed" | "flagged";

type Props = {
  proposal: ApiTargetedProposal;
  brandColor: string;
  onDismiss: () => void;
  onReject?: () => void;
  onRefine?: () => void;
  collegeId?: string;
  engagementType?: string;
  onSaved?: (saved: SavedProposal) => void;
};

function SectionHeader({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
      textTransform: "uppercase", color: color || "rgba(255,255,255,0.3)",
      display: "block", marginBottom: "10px",
    }}>
      {children}
    </span>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FlagIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path d="M2 1v10M2 1h7.5L8 4.5 9.5 8H2" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function ProposalCard({ proposal, brandColor, onDismiss, onReject, onRefine, collegeId, engagementType, onSaved }: Props) {
  const [state, setState] = useState<CardState>("default");
  const [savedId, setSavedId] = useState<string | null>(null);

  if (state === "dismissed") return null;

  const isSaved = state === "saved";
  const isFlagged = state === "flagged";

  return (
    <motion.div layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{
        padding: "28px", background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", position: "relative",
      }}>

        {/* Header: employer + partnership type */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h3 style={{ fontFamily: FONT, fontSize: "17px", fontWeight: 600, color: "rgba(255,255,255,0.9)", letterSpacing: "-0.01em", lineHeight: 1.3, margin: 0 }}>
            {proposal.employer}
          </h3>
          <span style={{
            flexShrink: 0, marginLeft: "16px", padding: "4px 12px", borderRadius: "100px",
            fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.05em",
            background: `${brandColor}20`, color: brandColor, border: `1px solid ${brandColor}40`,
          }}>
            {proposal.partnership_type}
          </span>
        </div>

        {/* ── Section 1: Summary ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Summary</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.summary}
          </p>
        </div>

        {/* ── Section 2: Justification ── */}
        <div style={{
          marginBottom: "24px", padding: "20px",
          background: "rgba(255,255,255,0.03)", borderRadius: "10px",
          border: "1px solid rgba(255,255,255,0.05)",
          display: "flex", flexDirection: "column", gap: "20px",
        }}>
          <SectionHeader>Justification</SectionHeader>
          <div>
            <span style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.06em",
              textTransform: "uppercase", color: "rgba(255,255,255,0.25)", display: "block", marginBottom: "6px",
            }}>
              Student Composition
            </span>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
              {proposal.justification.student_composition}
            </p>
          </div>
          <div>
            <span style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.06em",
              textTransform: "uppercase", color: "rgba(255,255,255,0.25)", display: "block", marginBottom: "6px",
            }}>
              Course Composition
            </span>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
              {proposal.justification.course_composition}
            </p>
          </div>
          <div>
            <span style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.06em",
              textTransform: "uppercase", color: "rgba(255,255,255,0.25)", display: "block", marginBottom: "6px",
            }}>
              Occupational Demand
            </span>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
              {proposal.justification.occupational_demand}
            </p>
          </div>
        </div>

        {/* ── Section 3: Roadmap ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Roadmap</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.roadmap}
          </p>
        </div>

        {/* Actions */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "16px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => {
                if (isSaved) {
                  if (collegeId && savedId) removeProposal(collegeId, savedId);
                  setSavedId(null);
                  setState("default");
                } else {
                  if (collegeId) {
                    const saved = saveProposal(collegeId, proposal, engagementType ?? "", "saved");
                    setSavedId(saved.id);
                    onSaved?.(saved);
                  }
                  setState("saved");
                }
              }}
              style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 600,
                cursor: "pointer", border: "none",
                background: isSaved ? "rgba(74,222,128,0.15)" : `${brandColor}20`,
                color: isSaved ? "rgba(74,222,128,0.9)" : brandColor,
              }}
            >
              <CheckIcon />
              {isSaved ? "Saved" : "Save"}
            </button>
            <button
              onClick={() => { onDismiss(); setState("dismissed"); }}
              style={{
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)",
                background: "transparent", color: "rgba(255,255,255,0.5)",
              }}
            >
              Dismiss
            </button>
            <button
              onClick={() => {
                if (isFlagged) {
                  if (collegeId && savedId) updateProposalStatus(collegeId, savedId, "saved");
                  setState("default");
                } else {
                  if (collegeId) {
                    if (savedId) {
                      updateProposalStatus(collegeId, savedId, "flagged");
                    } else {
                      const saved = saveProposal(collegeId, proposal, engagementType ?? "", "flagged");
                      setSavedId(saved.id);
                    }
                  }
                  setState("flagged");
                }
              }}
              style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                cursor: "pointer",
                border: `1px solid ${isFlagged ? "rgba(251,191,36,0.4)" : "rgba(255,255,255,0.12)"}`,
                background: isFlagged ? "rgba(251,191,36,0.1)" : "transparent",
                color: isFlagged ? "rgba(251,191,36,0.9)" : "rgba(255,255,255,0.5)",
              }}
            >
              <FlagIcon />
              Flag
            </button>
          </div>

          {/* Post-generation actions — shown in split-view context */}
          {onReject && (
            <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
              <button
                onClick={onReject}
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: "pointer", border: "1px solid rgba(248,113,113,0.3)",
                  background: "rgba(248,113,113,0.06)", color: "rgba(248,113,113,0.8)",
                }}
              >
                Reject &amp; Revise
              </button>
              <button
                onClick={onRefine}
                disabled={!onRefine}
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: onRefine ? "pointer" : "default",
                  border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                Refine
              </button>
              <button
                disabled
                title="Coming soon — Google Docs export via MCP"
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: "default", border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                Export to Docs
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
