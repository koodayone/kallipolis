"use client";

import { useState, useCallback } from "react";
import LeafHeader from "@/components/ui/LeafHeader";
import ProposalCard from "@/components/domains/ProposalCard";
import { SchoolConfig } from "@/lib/schoolConfig";
import { streamPartnerships } from "@/lib/api";
import type { PartnershipProposal } from "@/lib/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type ViewState = "ready" | "generating" | "results" | "error";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function PartnershipsView({ school, onBack }: Props) {
  const [viewState, setViewState] = useState<ViewState>("ready");
  const [proposals, setProposals] = useState<PartnershipProposal[]>([]);
  const [error, setError] = useState<string>("");

  const handleGenerate = useCallback(() => {
    setViewState("generating");
    setProposals([]);
    setError("");

    streamPartnerships(
      (proposal) => {
        setProposals((prev) => [...prev, proposal]);
        setViewState("results");
      },
      () => {},
      (err) => {
        setError(err);
        setViewState("error");
      },
    );
  }, []);

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="tetrahedron" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>
      <div
        style={{
          maxWidth: "800px",
          margin: "0 auto",
          padding: "32px 40px 80px",
          display: "flex",
          flexDirection: "column",
          gap: "32px",
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: FONT,
              fontSize: "24px",
              fontWeight: 600,
              color: "#f0eef4",
              letterSpacing: "-0.02em",
              marginBottom: "8px",
            }}
          >
            Partnerships
          </h1>
          <p
            style={{
              fontFamily: FONT,
              fontSize: "14px",
              color: "rgba(255,255,255,0.5)",
              lineHeight: 1.6,
            }}
          >
            AI-generated employer partnership proposals grounded in curriculum-to-job-role
            alignment. Each proposal references specific programs, skills, and regional employers.
          </p>
        </div>

        {/* Ready state — generate button */}
        {viewState === "ready" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "12px" }}>
            <button
              onClick={handleGenerate}
              style={{
                padding: "12px 28px",
                borderRadius: "8px",
                fontFamily: FONT,
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                border: "none",
                background: school.brandColorLight,
                color: "#ffffff",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              Generate Partnership Proposals
            </button>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.35)" }}>
              Analyzes curriculum, skills, and regional employers to produce actionable proposals
            </span>
          </div>
        )}

        {/* Generating state — loading */}
        {viewState === "generating" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "16px", padding: "48px 0" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                border: `3px solid rgba(255,255,255,0.1)`,
                borderTopColor: school.brandColorLight,
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
              }}
            />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)" }}>
              Analyzing curriculum-employer alignment...
            </p>
            <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)" }}>
              This may take 15-30 seconds
            </p>
          </div>
        )}

        {/* Error state */}
        {viewState === "error" && (
          <div
            style={{
              padding: "24px",
              background: "rgba(248,113,113,0.08)",
              border: "1px solid rgba(248,113,113,0.2)",
              borderRadius: "8px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(248,113,113,0.9)" }}>
              Failed to generate proposals: {error}
            </p>
            <button
              onClick={handleGenerate}
              style={{
                padding: "8px 20px",
                borderRadius: "6px",
                fontFamily: FONT,
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                border: "1px solid rgba(255,255,255,0.12)",
                background: "transparent",
                color: "rgba(255,255,255,0.7)",
                alignSelf: "flex-start",
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Results state — proposal cards */}
        {viewState === "results" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.4)" }}>
                {proposals.length} of 3 proposals generated{proposals.length < 3 ? "..." : ""}
              </span>
              <button
                onClick={handleGenerate}
                style={{
                  padding: "6px 16px",
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
                Regenerate
              </button>
            </div>
            {proposals.map((proposal, i) => (
              <ProposalCard
                key={`${proposal.employer_or_sector}-${i}`}
                proposal={proposal}
                brandColor={school.brandColorLight}
                onDismiss={() => {}}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
