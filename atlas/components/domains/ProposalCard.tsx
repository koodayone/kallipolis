"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { PartnershipProposal } from "@/lib/api";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

type CardState = "default" | "saved" | "dismissed" | "flagged";

type Props = {
  proposal: PartnershipProposal;
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

export default function ProposalCard({ proposal, onDismiss }: Props) {
  const [state, setState] = useState<CardState>("default");

  if (state === "dismissed") return null;

  const isSaved = state === "saved";
  const isFlagged = state === "flagged";

  return (
    <motion.div layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <Card style={{ padding: "28px", position: "relative" }}>
        {/* Status indicator */}
        {(isSaved || isFlagged) && (
          <div
            style={{
              position: "absolute",
              top: "16px",
              right: "16px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <Badge variant={isSaved ? "success" : "gold"}>
              {isSaved ? "Saved" : "Flagged"}
            </Badge>
          </div>
        )}

        {/* Header row */}
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
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "17px",
              fontWeight: 600,
              color: "#111827",
              letterSpacing: "-0.01em",
              lineHeight: 1.3,
            }}
          >
            {proposal.employer_or_sector}
          </h3>
          <Badge variant="gold" style={{ flexShrink: 0, marginLeft: "16px" }}>
            {proposal.partnership_type}
          </Badge>
        </div>

        {/* Curriculum alignment */}
        <div style={{ marginBottom: "16px" }}>
          <p
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "#9ca3af",
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
                    fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                    fontSize: "11px",
                    color: "#9ca3af",
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
                      background: "#fafaf9",
                      border: "1px solid #e4e2dc",
                      borderRadius: "100px",
                      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                      fontSize: "12px",
                      color: "#374151",
                    }}
                  >
                    {a.curriculum_name}
                  </span>
                  {a.relevance_note && (
                    <span
                      style={{
                        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                        fontSize: "11px",
                        color: "#9ca3af",
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
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontStyle: "italic",
            color: "#6b7280",
            lineHeight: 1.55,
            marginBottom: "14px",
          }}
        >
          {proposal.student_population_relevance}
        </p>

        {/* Rationale */}
        <p
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            color: "#374151",
            lineHeight: 1.65,
            marginBottom: "24px",
          }}
        >
          {proposal.rationale}
        </p>

        {/* Divider */}
        <div style={{ borderTop: "1px solid #f0ede6", paddingTop: "16px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <Button
              variant="solid-gold"
              size="sm"
              onClick={() => setState(isSaved ? "default" : "saved")}
            >
              <CheckIcon />
              {isSaved ? "Saved" : "Save"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onDismiss();
                setState("dismissed");
              }}
            >
              Dismiss
            </Button>
            <Button
              variant="outlined"
              size="sm"
              onClick={() => setState(isFlagged ? "default" : "flagged")}
              style={{
                color: isFlagged ? "#a07830" : "#6b7280",
                borderColor: isFlagged ? "#e8d5a0" : "#d1d5db",
                background: isFlagged ? "#fdf8ee" : "transparent",
              }}
            >
              <FlagIcon />
              Flag
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
