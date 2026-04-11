"use client";

import { motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import {
  getSavedProposals,
  removeProposal,
  type SavedProposal,
} from "@/college-atlas/partnerships/savedProposals";
import ProposalCard from "./ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  savedProposals: SavedProposal[];
  setSavedProposals: (proposals: SavedProposal[]) => void;
  manageQuery: string;
  setManageQuery: (q: string) => void;
  expandedSavedId: string | null;
  toggleExpanded: (id: string) => void;
};

export default function PartnershipManageMode({
  school,
  savedProposals,
  setSavedProposals,
  manageQuery,
  setManageQuery,
  expandedSavedId,
  toggleExpanded,
}: Props) {
  if (savedProposals.length === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", paddingTop: "80px" }}>
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)", margin: 0 }}>
          No saved partnerships yet.
        </p>
        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.25)", margin: 0 }}>
          Draft and save your first proposal to get started.
        </p>
      </div>
    );
  }

  const filtered = manageQuery.trim()
    ? savedProposals.filter((s) => s.proposal.employer.toLowerCase().includes(manageQuery.toLowerCase()))
    : savedProposals;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px", paddingTop: "24px", minHeight: "100vh" }}>
      {/* Search bar */}
      <div style={{ position: "relative", marginBottom: "16px" }}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          type="text"
          value={manageQuery}
          onChange={(e) => setManageQuery(e.target.value)}
          placeholder="Search saved partnerships..."
          style={{
            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
            outline: "none", transition: "border-color 0.2s, box-shadow 0.2s",
          }}
          onFocus={(e) => { e.currentTarget.style.borderColor = `${school.brandColorLight}50`; e.currentTarget.style.boxShadow = `0 0 0 3px ${school.brandColorLight}15`; }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)"; e.currentTarget.style.boxShadow = "none"; }}
        />
      </div>

      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr 160px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
      </div>

      {/* Rows */}
      {filtered.map((saved) => {
        const p = saved.proposal;
        const isExpanded = expandedSavedId === saved.id;
        return (
          <div key={saved.id}>
            <button
              onClick={() => toggleExpanded(saved.id)}
              style={{
                width: "100%", textAlign: "left", cursor: "pointer",
                display: "grid", gridTemplateColumns: "24px 1fr 160px",
                padding: "12px 16px", gap: "10px", alignItems: "center",
                background: isExpanded ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                style={{ transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
                <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                {p.employer}
              </span>
              <span style={{
                textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600,
                color: school.brandColorLight,
              }}>
                {p.partnership_type}
              </span>
            </button>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                transition={{ duration: 0.25 }}
                style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
              >
                <div style={{ padding: "16px 20px 24px" }}>
                  <ProposalCard
                    proposal={p}
                    brandColor={school.brandColorLight}
                    collegeId={school.name}
                    onDismiss={() => {
                      removeProposal(school.name, saved.id);
                      setSavedProposals(getSavedProposals(school.name));
                    }}
                  />
                </div>
              </motion.div>
            )}
          </div>
        );
      })}
    </div>
  );
}
