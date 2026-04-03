"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ApiTargetedProposal, ApiOccupationEvidence, ApiDepartmentEvidence, ApiStudentEvidence } from "@/lib/api";
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

function SubHeader({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.06em",
      textTransform: "uppercase", color: "rgba(255,255,255,0.25)", display: "block", marginBottom: "6px",
    }}>
      {children}
    </span>
  );
}

function EvidenceContainer({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      marginTop: "12px", padding: "14px 16px",
      background: "rgba(255,255,255,0.02)", borderRadius: "8px",
      border: "1px solid rgba(255,255,255,0.04)",
    }}>
      {children}
    </div>
  );
}

function formatWage(wage: number | null): string {
  if (!wage) return "—";
  return `$${Math.round(wage / 1000)}K`;
}

function formatNumber(n: number | null): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

function formatGrowth(rate: number | null): string {
  if (rate == null) return "—";
  return `${rate > 0 ? "+" : ""}${(rate * 100).toFixed(1)}%`;
}

function OccupationEvidenceGrid({ items }: { items: ApiOccupationEvidence[] }) {
  if (!items.length) return null;
  return (
    <EvidenceContainer>
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 70px 80px 80px 60px",
        gap: "4px 12px", alignItems: "center",
      }}>
        <span style={{ fontFamily: FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.2)" }}>Occupation</span>
        <span style={{ fontFamily: FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.2)", textAlign: "right" }}>Wage</span>
        <span style={{ fontFamily: FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.2)", textAlign: "right" }}>Employed</span>
        <span style={{ fontFamily: FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.2)", textAlign: "right" }}>Openings</span>
        <span style={{ fontFamily: FONT, fontSize: "9px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.2)", textAlign: "right" }}>Growth</span>
        {items.map((occ) => (
          <div key={occ.title} style={{ display: "contents" }}>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.6)" }}>{occ.title}</span>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontWeight: 500 }}>{formatWage(occ.annual_wage)}</span>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{formatNumber(occ.employment)}</span>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{formatNumber(occ.annual_openings)}</span>
            <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{formatGrowth(occ.growth_rate)}</span>
          </div>
        ))}
      </div>
    </EvidenceContainer>
  );
}

function DepartmentEvidenceList({ items }: { items: ApiDepartmentEvidence[] }) {
  if (!items.length) return null;
  return (
    <EvidenceContainer>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {items.map((dept) => (
          <div key={dept.department}>
            <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.65)" }}>
              {dept.department}
            </span>
            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", marginLeft: "8px" }}>
              {dept.course_count} course{dept.course_count !== 1 ? "s" : ""}
            </span>
            <div style={{ marginTop: "3px", display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {dept.aligned_skills.map((skill) => (
                <span key={skill} style={{
                  fontFamily: FONT, fontSize: "10px", padding: "2px 8px", borderRadius: "4px",
                  background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.4)",
                }}>
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </EvidenceContainer>
  );
}

function StudentEvidenceBar({ data }: { data: ApiStudentEvidence }) {
  return (
    <EvidenceContainer>
      <div style={{ display: "flex", gap: "24px", alignItems: "baseline", flexWrap: "wrap" }}>
        <div>
          <span style={{ fontFamily: FONT, fontSize: "18px", fontWeight: 600, color: "#f0eef4" }}>
            {data.total_students.toLocaleString()}
          </span>
          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", marginLeft: "6px" }}>
            students
          </span>
        </div>
        <div>
          <span style={{ fontFamily: FONT, fontSize: "18px", fontWeight: 600, color: "#f0eef4" }}>
            {data.students_with_3plus_courses.toLocaleString()}
          </span>
          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", marginLeft: "6px" }}>
            with 3+ courses
          </span>
        </div>
        {data.top_skills.length > 0 && (
          <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
            {data.top_skills.map((skill) => (
              <span key={skill} style={{
                fontFamily: FONT, fontSize: "10px", padding: "2px 8px", borderRadius: "4px",
                background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.4)",
              }}>
                {skill}
              </span>
            ))}
          </div>
        )}
      </div>
    </EvidenceContainer>
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

        {/* ── Opportunity ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Opportunity</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.opportunity}
          </p>
          <OccupationEvidenceGrid items={proposal.opportunity_evidence} />
        </div>

        {/* ── Curriculum Alignment ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Curriculum Alignment</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.curriculum_composition}
          </p>
          <DepartmentEvidenceList items={proposal.justification.curriculum_evidence} />
        </div>

        {/* ── Student Pipeline ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Student Pipeline</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.student_composition}
          </p>
          <StudentEvidenceBar data={proposal.justification.student_evidence} />
        </div>

        {/* ── Roadmap ── */}
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
