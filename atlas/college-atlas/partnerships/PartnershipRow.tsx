"use client";

import { memo, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import type { ApiPartnershipOpportunity } from "@/college-atlas/partnerships/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  opp: ApiPartnershipOpportunity;
  i: number;
  school: SchoolConfig;
  savedCount: number;
  onDraft: (opp: ApiPartnershipOpportunity) => void;
};

// Single-line row in the partnerships Build mode. Not expandable —
// employer context (description, website, occupations) lives in the
// picker view that opens when the coordinator clicks Draft Partnership.
//
// The row carries three things:
//   1. Employer name (left)
//   2. Optional "● N saved" indicator if the coordinator has drafts saved
//      against this employer (subtle visibility into existing work)
//   3. Draft Partnership CTA (right) — the only interaction
const PartnershipRow = memo(function PartnershipRow({
  opp, i, school, savedCount, onDraft,
}: Props) {
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);

  return (
    <motion.div
      initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(i * 0.015, 0.3) }}
      style={{
        display: "grid", gridTemplateColumns: "1fr auto",
        padding: "12px 16px 12px 44px", gap: "12px", alignItems: "center",
        background: "rgba(255,255,255,0.03)",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
    >
      <span style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
          {opp.name}
        </span>
        {savedCount > 0 && (
          <span style={{
            display: "inline-flex", alignItems: "center", gap: "5px",
            fontFamily: FONT, fontSize: "11px", fontWeight: 500,
            color: school.brandColorLight, opacity: 0.75,
          }}>
            <span style={{
              width: "5px", height: "5px", borderRadius: "50%",
              background: school.brandColorLight, opacity: 0.85,
            }} />
            {savedCount} saved
          </span>
        )}
      </span>
      <button
        onClick={() => onDraft(opp)}
        style={{
          display: "inline-flex", alignItems: "center", gap: "7px",
          padding: "8px 14px", borderRadius: "6px",
          fontFamily: FONT, fontSize: "12px", fontWeight: 600,
          letterSpacing: "0.01em",
          cursor: "pointer", border: "none",
          background: `${school.brandColorLight}20`,
          color: school.brandColorLight,
          transition: "background 0.15s, box-shadow 0.2s",
          whiteSpace: "nowrap",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = `${school.brandColorLight}30`;
          e.currentTarget.style.boxShadow = `0 0 14px ${school.brandColorLight}30`;
          const s = e.currentTarget.querySelector("svg");
          if (s) s.style.transform = "scale(1.18) rotate(18deg)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = `${school.brandColorLight}20`;
          e.currentTarget.style.boxShadow = "none";
          const s = e.currentTarget.querySelector("svg");
          if (s) s.style.transform = "scale(1) rotate(0deg)";
        }}
      >
        Draft Partnership
        {/* Sparkle (4-pointed star) — signals the LLM-generated nature of the
            artifact and twinkles on hover. Replaces the prior right-arrow,
            which read as "navigate next" rather than "synthesize". */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          style={{
            transition: "transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)",
            transformOrigin: "center",
            flexShrink: 0,
          }}
        >
          <path
            d="M6 0.5L6.95 4.7L11.5 6L6.95 7.3L6 11.5L5.05 7.3L0.5 6L5.05 4.7L6 0.5Z"
            fill="currentColor"
          />
        </svg>
      </button>
    </motion.div>
  );
});

export default PartnershipRow;
