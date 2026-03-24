"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { PartnershipProposal } from "@/lib/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type CardState = "default" | "saved" | "dismissed" | "flagged";

type Props = {
  proposal: PartnershipProposal;
  brandColor: string;
  onDismiss: () => void;
};

function FlagIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path
        d="M2 1v10M2 1h7.5L8 4.5 9.5 8H2"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path
        d="M2 6l3 3 5-5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function ProposalCard({ proposal, brandColor, onDismiss }: Props) {
  const [state, setState] = useState<CardState>("default");

  if (state === "dismissed") return null;

  const isSaved = state === "saved";
  const isFlagged = state === "flagged";

  return (
    <motion.div layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div
        style={{
          padding: "28px",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "8px",
          position: "relative",
        }}
      >
        {/* Status indicator */}
        {(isSaved || isFlagged) && (
          <div style={{ position: "absolute", top: "16px", right: "16px" }}>
            <span
              style={{
                padding: "4px 10px",
                borderRadius: "100px",
                fontFamily: FONT,
                fontSize: "11px",
                fontWeight: 600,
                letterSpacing: "0.05em",
                background: isSaved ? "rgba(74,222,128,0.15)" : "rgba(251,191,36,0.15)",
                color: isSaved ? "rgba(74,222,128,0.9)" : "rgba(251,191,36,0.9)",
                border: `1px solid ${isSaved ? "rgba(74,222,128,0.3)" : "rgba(251,191,36,0.3)"}`,
              }}
            >
              {isSaved ? "Saved" : "Flagged"}
            </span>
          </div>
        )}

        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "16px",
            paddingRight: isSaved || isFlagged ? "80px" : "0",
          }}
        >
          <h3
            style={{
              fontFamily: FONT,
              fontSize: "17px",
              fontWeight: 600,
              color: "rgba(255,255,255,0.9)",
              letterSpacing: "-0.01em",
              lineHeight: 1.3,
            }}
          >
            {proposal.employer_or_sector}
          </h3>
          <span
            style={{
              flexShrink: 0,
              marginLeft: "16px",
              padding: "4px 12px",
              borderRadius: "100px",
              fontFamily: FONT,
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.05em",
              background: `${brandColor}20`,
              color: brandColor,
              border: `1px solid ${brandColor}40`,
            }}
          >
            {proposal.partnership_type}
          </span>
        </div>

        {/* Curriculum alignment */}
        <div style={{ marginBottom: "16px" }}>
          <p
            style={{
              fontFamily: FONT,
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.35)",
              marginBottom: "10px",
            }}
          >
            Curriculum Alignment
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {proposal.curriculum_alignment.map((a, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                <span
                  style={{
                    fontFamily: FONT,
                    fontSize: "11px",
                    color: "rgba(255,255,255,0.4)",
                    minWidth: "130px",
                    flexShrink: 0,
                    paddingTop: "1px",
                  }}
                >
                  {a.program_name}
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <span
                    style={{
                      display: "inline-block",
                      padding: "3px 10px",
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: "100px",
                      fontFamily: FONT,
                      fontSize: "12px",
                      color: "rgba(255,255,255,0.8)",
                    }}
                  >
                    {a.curriculum_name}
                  </span>
                  {a.relevance_note && (
                    <span
                      style={{
                        fontFamily: FONT,
                        fontSize: "11px",
                        color: "rgba(255,255,255,0.4)",
                        lineHeight: 1.4,
                        paddingLeft: "2px",
                      }}
                    >
                      {a.relevance_note}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Student population relevance */}
        <p
          style={{
            fontFamily: FONT,
            fontSize: "13px",
            fontStyle: "italic",
            color: "rgba(255,255,255,0.5)",
            lineHeight: 1.55,
            marginBottom: "14px",
          }}
        >
          {proposal.student_population_relevance}
        </p>

        {/* Rationale */}
        <p
          style={{
            fontFamily: FONT,
            fontSize: "14px",
            color: "rgba(255,255,255,0.7)",
            lineHeight: 1.65,
            marginBottom: "24px",
          }}
        >
          {proposal.rationale}
        </p>

        {/* Actions */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "16px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => setState(isSaved ? "default" : "saved")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 14px",
                borderRadius: "6px",
                fontFamily: FONT,
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                border: "none",
                background: isSaved ? "rgba(74,222,128,0.15)" : `${brandColor}20`,
                color: isSaved ? "rgba(74,222,128,0.9)" : brandColor,
              }}
            >
              <CheckIcon />
              {isSaved ? "Saved" : "Save"}
            </button>
            <button
              onClick={() => {
                onDismiss();
                setState("dismissed");
              }}
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontFamily: FONT,
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer",
                border: "1px solid rgba(255,255,255,0.12)",
                background: "transparent",
                color: "rgba(255,255,255,0.5)",
              }}
            >
              Dismiss
            </button>
            <button
              onClick={() => setState(isFlagged ? "default" : "flagged")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 14px",
                borderRadius: "6px",
                fontFamily: FONT,
                fontSize: "12px",
                fontWeight: 500,
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
        </div>
      </div>
    </motion.div>
  );
}
