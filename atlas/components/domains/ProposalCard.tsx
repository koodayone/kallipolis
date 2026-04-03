"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
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

/* ── Shared Components ─────────────────────────────────────────────────── */

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

function Chevron({ open }: { open: boolean }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
      style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s", flexShrink: 0 }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
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

function SkillBadge({ skill, brandColor }: { skill: string; brandColor: string }) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "12px", fontWeight: 500, padding: "5px 12px",
      borderRadius: "6px", border: `1px solid ${brandColor}60`, color: brandColor,
      background: "rgba(255,255,255,0.02)",
    }}>
      {skill}
    </span>
  );
}

/* ── Occupation Evidence (matches OccupationsView) ─────────────────────── */

function OccupationEvidence({ items, brandColor }: { items: ApiOccupationEvidence[]; brandColor: string }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  if (!items.length) return null;

  const hdrStyle = {
    fontFamily: FONT, fontSize: "10px", fontWeight: 600 as const, letterSpacing: "0.1em",
    textTransform: "uppercase" as const, color: brandColor, opacity: 0.6,
  };

  return (
    <div style={{ marginTop: "12px" }}>
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr 100px 80px 110px",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ ...hdrStyle }}>Occupation</span>
        <span style={{ ...hdrStyle, textAlign: "right" }}>Wage</span>
        <span style={{ ...hdrStyle, textAlign: "right" }}>Openings</span>
        <span style={{ ...hdrStyle, textAlign: "right" }}>Growth</span>
      </div>
      {items.map((occ, i) => {
        const isOpen = expanded.has(occ.title);
        return (
          <div key={occ.title}>
            <motion.button
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(i * 0.01, 0.2) }}
              onClick={() => setExpanded(prev => {
                const next = new Set(prev);
                isOpen ? next.delete(occ.title) : next.add(occ.title);
                return next;
              })}
              style={{
                width: "100%", textAlign: "left",
                display: "grid", gridTemplateColumns: "24px 1fr 100px 80px 110px",
                padding: "12px 16px", gap: "10px", alignItems: "center",
                background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
                cursor: "pointer", transition: "background 0.15s",
              }}
              onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
            >
              <Chevron open={isOpen} />
              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4 }}>
                {occ.title}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "right" }}>
                {occ.annual_wage ? `$${occ.annual_wage.toLocaleString()}` : "\u2014"}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>
                {occ.annual_openings != null ? `${occ.annual_openings.toLocaleString()}/yr` : "\u2014"}
              </span>
              <span style={{
                fontFamily: FONT, fontSize: "12px", fontWeight: 500, textAlign: "right",
                color: occ.growth_rate != null ? (occ.growth_rate >= 0 ? "#4ade80" : "#f87171") : "rgba(255,255,255,0.25)",
              }}>
                {occ.growth_rate != null ? `${occ.growth_rate >= 0 ? "+" : ""}${(occ.growth_rate * 100).toFixed(1)}%` : "\u2014"}
              </span>
            </motion.button>
            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                  style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                >
                  <div style={{ padding: "12px 20px 16px", display: "flex", gap: "24px" }}>
                    {occ.employment != null && (
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>
                        {occ.employment.toLocaleString()} employed regionally
                      </span>
                    )}
                    {occ.soc_code && (
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)" }}>
                        SOC {occ.soc_code}
                      </span>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

/* ── Department Evidence (matches CoursesView departments) ─────────────── */

function DepartmentEvidence({ items, brandColor }: { items: ApiDepartmentEvidence[]; brandColor: string }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  if (!items.length) return null;

  const hdrStyle = {
    fontFamily: FONT, fontSize: "10px", fontWeight: 600 as const, letterSpacing: "0.1em",
    textTransform: "uppercase" as const, color: brandColor, opacity: 0.6,
  };

  return (
    <div style={{ marginTop: "12px" }}>
      <div style={{
        display: "grid", gridTemplateColumns: "24px 1fr auto",
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        <span style={{ ...hdrStyle }}>Department</span>
        <span style={{ ...hdrStyle, textAlign: "right" }}>Courses</span>
      </div>
      {items.map((dept, i) => {
        const isOpen = expanded.has(dept.department);
        return (
          <div key={dept.department}>
            <motion.button
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(i * 0.01, 0.2) }}
              onClick={() => setExpanded(prev => {
                const next = new Set(prev);
                isOpen ? next.delete(dept.department) : next.add(dept.department);
                return next;
              })}
              style={{
                width: "100%", textAlign: "left",
                display: "grid", gridTemplateColumns: "24px 1fr auto",
                padding: "12px 16px", gap: "10px", alignItems: "center",
                background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
                cursor: "pointer", transition: "background 0.15s",
              }}
              onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
            >
              <Chevron open={isOpen} />
              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                {dept.department}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
                {dept.courses.length} course{dept.courses.length !== 1 ? "s" : ""}
              </span>
            </motion.button>
            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                  style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
                >
                  <div style={{ padding: "8px 16px 16px", display: "flex", flexDirection: "column", gap: "2px" }}>
                    {dept.courses.map(course => (
                      <div key={course.code} style={{
                        display: "flex", alignItems: "baseline", gap: "10px",
                        padding: "8px 12px", borderRadius: "4px", background: "rgba(255,255,255,0.02)",
                      }}>
                        <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: brandColor, flexShrink: 0 }}>
                          {course.code}
                        </span>
                        <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.65)", flex: 1 }}>
                          {course.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

/* ── Student Evidence (compact stats) ──────────────────────────────────── */

function StudentEvidence({ data, brandColor }: { data: ApiStudentEvidence; brandColor: string }) {
  return (
    <div style={{
      marginTop: "12px",
      background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.05)",
    }}>
      {/* Stats bar */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1px 1fr",
        padding: "16px 0",
      }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
          <span style={{ fontFamily: FONT, fontSize: "20px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
            {data.total_students.toLocaleString()}
          </span>
          <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
            Students in Pipeline
          </span>
        </div>
        <div style={{ background: "rgba(255,255,255,0.08)" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
          <span style={{ fontFamily: FONT, fontSize: "20px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
            {data.students_with_3plus_courses.toLocaleString()}
          </span>
          <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
            With 3+ Courses
          </span>
        </div>
      </div>
      {/* Skills */}
      {data.top_skills.length > 0 && (
        <div style={{
          padding: "12px 16px 16px",
          borderTop: "1px solid rgba(255,255,255,0.05)",
        }}>
          <span style={{
            fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.2)",
            display: "block", marginBottom: "8px",
          }}>
            Aligned Skills
          </span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {data.top_skills.map(skill => (
              <SkillBadge key={skill} skill={skill} brandColor={brandColor} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main ProposalCard ─────────────────────────────────────────────────── */

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

        {/* Header */}
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
          <OccupationEvidence items={proposal.opportunity_evidence} brandColor={brandColor} />
        </div>

        {/* ── Curriculum Alignment ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Curriculum Alignment</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.curriculum_composition}
          </p>
          <DepartmentEvidence items={proposal.justification.curriculum_evidence} brandColor={brandColor} />
        </div>

        {/* ── Student Pipeline ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Student Pipeline</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.student_composition}
          </p>
          <StudentEvidence data={proposal.justification.student_evidence} brandColor={brandColor} />
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
