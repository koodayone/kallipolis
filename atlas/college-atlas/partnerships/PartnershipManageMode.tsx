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
  // Set of regional-priority sector names. Saved-proposal rows whose
  // sector is in this set render the small priority dot, mirroring the
  // Build mode per-sector priority indicator. Optional so legacy callers
  // still work; absent → no dots ever rendered.
  prioritySet?: Set<string>;
};

export default function PartnershipManageMode({
  school,
  savedProposals,
  setSavedProposals,
  manageQuery,
  setManageQuery,
  expandedSavedId,
  toggleExpanded,
  prioritySet,
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

      {/* Column headers — Sector header carries the same regional-priority
          legend Build mode uses, so the per-row dot has the same on-page
          explanation in both modes. */}
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr 240px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{
          display: "inline-flex", alignItems: "baseline", gap: "8px",
          justifyContent: "flex-end",
        }}>
          <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Sector</span>
          {prioritySet && prioritySet.size > 0 && (
            <span style={{ display: "inline-flex", alignItems: "baseline", gap: "5px" }}>
              <span style={{
                width: "5px", height: "5px", borderRadius: "50%",
                background: school.brandColorLight, opacity: 0.7,
                position: "relative", top: "-1px",
              }} />
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 500,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: school.brandColorLight, opacity: 0.4,
              }}>
                Regional priority
              </span>
            </span>
          )}
        </span>
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
                display: "grid", gridTemplateColumns: "24px 1fr 240px",
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
              {/* Sector designation — rhymes with Build mode's per-sector
                  treatment: uppercase letter-spaced sector label with the
                  regional-priority dot placed AFTER the label when the
                  sector is in the priority set. White text (matches the
                  employer-name color register) so it reads as a
                  designation rather than a brand accent; quieter than
                  Build mode's bigger section-header treatment. */}
              <span style={{
                display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "8px",
              }}>
                <span style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                  letterSpacing: "0.08em", textTransform: "uppercase",
                  color: "rgba(255,255,255,0.85)",
                  textAlign: "right",
                }}>
                  {p.sector ?? "—"}
                </span>
                {p.sector && prioritySet?.has(p.sector) && (
                  <span
                    title="Regional priority sector"
                    style={{
                      display: "inline-block", width: "6px", height: "6px",
                      borderRadius: "50%", background: school.brandColorLight, flexShrink: 0,
                    }}
                  />
                )}
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
