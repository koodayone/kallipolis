"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { generatePartnerships, PartnershipProposal } from "@/lib/api";
import ProposalCard from "./ProposalCard";
import LoadingDots from "@/components/ui/LoadingDots";
import Button from "@/components/ui/Button";

type ViewState = "idle" | "loading" | "loaded" | "error";

export default function IndustryView() {
  const [viewState, setViewState] = useState<ViewState>("idle");
  const [proposals, setProposals] = useState<PartnershipProposal[]>([]);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());

  const handleGenerate = useCallback(async () => {
    setViewState("loading");
    setProposals([]);
    setDismissedIds(new Set());
    try {
      const result = await generatePartnerships();
      setProposals(result.proposals);
      setViewState("loaded");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "An unexpected error occurred.");
      setViewState("error");
    }
  }, []);

  const handleDismiss = useCallback((index: number) => {
    setDismissedIds((prev) => new Set([...prev, index]));
  }, []);

  const visibleCount = proposals.length - dismissedIds.size;

  return (
    <div
      style={{
        maxWidth: "780px",
        margin: "0 auto",
        padding: "56px 40px 100px",
      }}
    >
      {/* Page header */}
      <div style={{ marginBottom: "40px" }}>
        <h1
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "24px",
            fontWeight: 600,
            color: "#111827",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
          }}
        >
          Partnership Proposals
        </h1>
        <p
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            color: "#6b7280",
            lineHeight: 1.6,
            marginBottom: "28px",
            maxWidth: "520px",
          }}
        >
          Analyze curriculum-to-job-role alignment between your programs and employers
          in the Inland Empire labor market. Each proposal is grounded in live ontology data.
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Button
            variant="solid-gold"
            onClick={handleGenerate}
            disabled={viewState === "loading"}
            style={{ fontSize: "14px", padding: "11px 28px" }}
          >
            {viewState === "loading" ? "Generating…" : viewState === "loaded" ? "Regenerate" : "Generate Partnerships"}
          </Button>

          {viewState === "loaded" && visibleCount > 0 && (
            <span
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "13px",
                color: "#9ca3af",
              }}
            >
              {visibleCount} proposal{visibleCount !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Loading state */}
      <AnimatePresence>
        {viewState === "loading" && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <LoadingDots />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
      <AnimatePresence>
        {viewState === "error" && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              padding: "24px",
              background: "#fff7f7",
              border: "1px solid #fecaca",
              borderRadius: "10px",
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "14px",
                color: "#b91c1c",
              }}
            >
              {errorMsg}
            </p>
            <p
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "12px",
                color: "#9ca3af",
                marginTop: "8px",
              }}
            >
              Ensure the backend is running and your ANTHROPIC_API_KEY is set.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Proposals */}
      <AnimatePresence>
        {viewState === "loaded" && (
          <motion.div
            key="proposals"
            layout
            style={{ display: "flex", flexDirection: "column", gap: "20px" }}
          >
            {proposals.map((proposal, index) => (
              !dismissedIds.has(index) && (
                <ProposalCard
                  key={index}
                  proposal={proposal}
                  onDismiss={() => handleDismiss(index)}
                />
              )
            ))}

            {visibleCount === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{
                  textAlign: "center",
                  padding: "60px 0",
                  color: "#9ca3af",
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "14px",
                }}
              >
                All proposals dismissed. Generate a new set to continue.
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Idle state — hint */}
      {viewState === "idle" && (
        <div
          style={{
            borderTop: "1px solid #f0ede6",
            paddingTop: "40px",
            display: "flex",
            gap: "32px",
          }}
        >
          {[
            ["6", "Proposals generated per run"],
            ["10", "Employers analyzed"],
            ["25+", "Curricula mapped to job roles"],
          ].map(([value, label]) => (
            <div key={label} style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <span
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "24px",
                  fontWeight: 600,
                  color: "#c9a84c",
                  letterSpacing: "-0.03em",
                }}
              >
                {value}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "12px",
                  color: "#9ca3af",
                  lineHeight: 1.4,
                  maxWidth: "120px",
                }}
              >
                {label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
