"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import type {
  ApiLmiContext,
  ApiSwpProject,
  ApiSwpSection,
} from "@/college-atlas/strong-workforce/api";
import SwpArtifact from "./SwpArtifact";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type SwpPhase = "selection" | "generating" | "streaming" | "complete";

type Props = {
  school: SchoolConfig;
  phase: SwpPhase;
  swpProject: ApiSwpProject | null;
  streamedSections: ApiSwpSection[];
  lmiContext: ApiLmiContext | null;
  swpError: string | null;
  swpSaved: boolean;
  onSave: () => void;
  onReject: () => void;
  onRetry: () => void;
};

export default function SwpGenerationFlow({
  school,
  phase,
  swpProject,
  streamedSections,
  lmiContext,
  swpError,
  swpSaved,
  onSave,
  onReject,
  onRetry,
}: Props) {
  if (phase === "generating") {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "16px" }}>
        <div style={{
          width: "32px", height: "32px",
          border: "3px solid rgba(255,255,255,0.08)",
          borderTopColor: school.brandColorLight,
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)" }}>
          Drafting SWP project proposal for NOVA...
        </p>
      </div>
    );
  }

  if (phase !== "streaming" && phase !== "complete") return null;

  return (
    <div style={{ maxWidth: "700px", margin: "0 auto" }}>
      <AnimatePresence>
        {(streamedSections.length > 0 || swpProject) && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
            <SwpArtifact
              project={swpProject}
              streamedSections={streamedSections}
              lmiContext={lmiContext}
              brandColor={school.brandColorLight}
              isStreaming={phase === "streaming"}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {phase === "complete" && swpProject && (
        <div style={{ display: "flex", gap: "10px", marginTop: "24px" }}>
          <button
            onClick={onSave}
            disabled={swpSaved}
            style={{
              padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 600,
              cursor: swpSaved ? "default" : "pointer", border: "none",
              background: swpSaved ? "rgba(74,222,128,0.15)" : school.brandColorLight,
              color: swpSaved ? "rgba(74,222,128,0.9)" : "#ffffff",
            }}
          >
            {swpSaved ? "SWP Document Saved" : "Save SWP Document"}
          </button>
          <button
            onClick={onReject}
            style={{
              padding: "10px 20px", borderRadius: "8px", fontFamily: FONT, fontSize: "13px", fontWeight: 500,
              cursor: "pointer",
              border: "1px solid rgba(248,113,113,0.3)",
              background: "rgba(248,113,113,0.06)",
              color: "rgba(248,113,113,0.8)",
            }}
          >
            Reject &amp; Revise
          </button>
        </div>
      )}

      {phase === "complete" && swpError && (
        <div style={{
          padding: "16px",
          background: "rgba(248,113,113,0.08)",
          border: "1px solid rgba(248,113,113,0.2)",
          borderRadius: "8px",
          marginTop: "24px",
        }}>
          <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(248,113,113,0.9)", margin: "0 0 8px" }}>
            Failed to generate: {swpError}
          </p>
          <button
            onClick={onRetry}
            style={{
              fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer",
              border: "1px solid rgba(255,255,255,0.12)",
              background: "transparent",
              color: "rgba(255,255,255,0.7)",
              borderRadius: "6px",
              padding: "6px 14px",
            }}
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
