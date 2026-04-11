"use client";

import type { SchoolConfig } from "@/config/schoolConfig";
import type { SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import RisingSun from "@/ui/RisingSun";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  userName: string;
  savedProposals: SavedProposal[];
  buildQuery: string;
  setBuildQuery: (q: string) => void;
  expandedBuildId: string | null;
  toggleExpanded: (id: string) => void;
  onDraft: (saved: SavedProposal) => void;
};

export default function SwpBuildMode({
  school,
  userName,
  savedProposals,
  buildQuery,
  setBuildQuery,
  expandedBuildId,
  toggleExpanded,
  onDraft,
}: Props) {
  const filtered = buildQuery.trim()
    ? savedProposals.filter((s) => s.proposal.employer.toLowerCase().includes(buildQuery.toLowerCase()))
    : savedProposals;

  return (
    <>
      {/* Build mode header with sun + greeting */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", marginBottom: "24px" }}>
        <RisingSun style={{ width: "90px", height: "auto" }} />
        <h1 style={{ fontFamily: FONT, fontSize: "28px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", textAlign: "center", margin: 0 }}>
          SWP compliance{userName ? `, ${userName}` : ""}?
        </h1>
      </div>

      {savedProposals.length === 0 ? (
        <div style={{ padding: "40px", textAlign: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" }}>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>No saved partnerships yet.</p>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Visit the Industry domain to build and save a partnership proposal.</p>
        </div>
      ) : (
        <>
          {/* Search bar */}
          <div style={{ position: "relative", marginBottom: "16px" }}>
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
              style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
              <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
              <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              value={buildQuery}
              onChange={(e) => setBuildQuery(e.target.value)}
              placeholder="Search partnerships..."
              style={{
                width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
                color: "#f0eef4", background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
                outline: "none",
              }}
            />
          </div>

          {/* Column headers */}
          <div style={{ display: "grid", gridTemplateColumns: "24px 1fr 160px", padding: "12px 16px", gap: "10px", alignItems: "center" }}>
            <span />
            <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
            <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
          </div>

          {/* Rows */}
          {filtered.map((saved) => {
            const isExpanded = expandedBuildId === saved.id;
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
                    {saved.proposal.employer}
                  </span>
                  <span style={{ textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600, color: school.brandColorLight }}>
                    {saved.proposal.partnership_type}
                  </span>
                </button>
                {isExpanded && (
                  <div style={{ background: "rgba(255,255,255,0.02)" }}>
                    <div style={{ padding: "14px 20px 18px" }}>
                      <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.55, margin: "0 0 14px" }}>
                        {saved.proposal.partnership_type} partnership with {saved.proposal.employer}{saved.proposal.sector ? ` for the ${saved.proposal.sector} sector` : ""}.
                      </p>
                      <button
                        onClick={() => onDraft(saved)}
                        style={{
                          width: "100%", padding: "14px 24px", borderRadius: "10px",
                          fontFamily: FONT, fontSize: "15px", fontWeight: 600, letterSpacing: "-0.01em",
                          cursor: "pointer", border: "none",
                          background: school.brandColorLight, color: "#ffffff",
                          transition: "opacity 0.15s",
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
                        onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
                      >
                        Draft SWP Project Proposal for NOVA
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}
    </>
  );
}
