"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ApiTargetedProposal } from "@/lib/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type CardState = "default" | "saved" | "dismissed" | "flagged";

type Props = {
  proposal: ApiTargetedProposal;
  brandColor: string;
  onDismiss: () => void;
  onReject?: () => void;
  onRefine?: () => void;
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

export default function ProposalCard({ proposal, brandColor, onDismiss, onReject, onRefine }: Props) {
  const [state, setState] = useState<CardState>("default");

  if (state === "dismissed") return null;

  const isSaved = state === "saved";
  const isFlagged = state === "flagged";

  return (
    <motion.div layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{
        padding: "28px", background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", position: "relative",
      }}>
        {/* Status indicator */}
        {(isSaved || isFlagged) && (
          <div style={{ position: "absolute", top: "16px", right: "16px" }}>
            <span style={{
              padding: "4px 10px", borderRadius: "100px", fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.05em",
              background: isSaved ? "rgba(74,222,128,0.15)" : "rgba(251,191,36,0.15)",
              color: isSaved ? "rgba(74,222,128,0.9)" : "rgba(251,191,36,0.9)",
              border: `1px solid ${isSaved ? "rgba(74,222,128,0.3)" : "rgba(251,191,36,0.3)"}`,
            }}>
              {isSaved ? "Saved" : "Flagged"}
            </span>
          </div>
        )}

        {/* Header: employer + partnership type */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", paddingRight: isSaved || isFlagged ? "80px" : "0" }}>
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

        {/* Executive Summary */}
        <div style={{ marginBottom: "20px" }}>
          <SectionHeader color={brandColor + "99"}>Executive Summary</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.executive_summary}
          </p>
        </div>

        {/* Partnership Type Rationale */}
        <div style={{ marginBottom: "20px" }}>
          <p style={{ fontFamily: FONT, fontSize: "13px", fontStyle: "italic", color: "rgba(255,255,255,0.45)", lineHeight: 1.55, margin: 0 }}>
            {proposal.partnership_type_rationale}
          </p>
        </div>

        {/* Curriculum Alignment */}
        {proposal.curriculum_alignment.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <SectionHeader>Curriculum Alignment</SectionHeader>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {proposal.curriculum_alignment.map((a, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                  <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", minWidth: "110px", flexShrink: 0, paddingTop: "1px" }}>
                    {a.department}
                  </span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, color: brandColor }}>{a.course_code}</span>
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.65)" }}>{a.course_name}</span>
                    </div>
                    <span style={{
                      display: "inline-block", padding: "2px 8px",
                      background: `${brandColor}15`, border: `1px solid ${brandColor}30`,
                      borderRadius: "100px", fontFamily: FONT, fontSize: "11px", color: brandColor, alignSelf: "flex-start",
                    }}>
                      {a.skill}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skill Gaps */}
        {proposal.skill_gaps.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <SectionHeader>Skill Gaps</SectionHeader>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {proposal.skill_gaps.map((g, i) => (
                <div key={i} style={{ padding: "10px 14px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                  <div style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.7)", marginBottom: "4px" }}>
                    {g.skill}
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", marginBottom: "4px" }}>
                    Required by: {g.required_by.join(", ")}
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", lineHeight: 1.5 }}>
                    {g.recommended_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Student Pipeline */}
        <div style={{ marginBottom: "20px" }}>
          <SectionHeader>Student Pipeline</SectionHeader>
          <div style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.8 }}>
            <span style={{ fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>{proposal.student_pipeline.total_students.toLocaleString()}</span> students with relevant skills
            {" · "}
            <span style={{ fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>{proposal.student_pipeline.students_with_3plus_courses.toLocaleString()}</span> with 3+ completed courses
          </div>
          {proposal.student_pipeline.top_skills.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "8px" }}>
              {proposal.student_pipeline.top_skills.map((skill) => (
                <span key={skill} style={{
                  fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.5)",
                  background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "100px", padding: "3px 10px",
                }}>{skill}</span>
              ))}
            </div>
          )}
        </div>

        {/* Economic Impact */}
        {proposal.economic_impact.occupations.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <SectionHeader>Economic Impact</SectionHeader>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {proposal.economic_impact.occupations.map((occ, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: FONT, fontSize: "12px" }}>
                  <span style={{ color: "rgba(255,255,255,0.6)" }}>{occ.title}</span>
                  <div style={{ display: "flex", gap: "16px" }}>
                    {occ.annual_wage && <span style={{ color: "rgba(255,255,255,0.5)" }}>${occ.annual_wage.toLocaleString()}/yr</span>}
                    {occ.employment && <span style={{ color: "rgba(255,255,255,0.4)" }}>{occ.employment.toLocaleString()} employed</span>}
                  </div>
                </div>
              ))}
            </div>
            {proposal.economic_impact.aggregate_employment && (
              <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.35)", marginTop: "8px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "8px" }}>
                Total regional employment: <span style={{ fontWeight: 500, color: "rgba(255,255,255,0.5)" }}>{proposal.economic_impact.aggregate_employment.toLocaleString()}</span>
              </div>
            )}
          </div>
        )}

        {/* Next Steps */}
        {proposal.next_steps.length > 0 && (
          <div style={{ marginBottom: "24px" }}>
            <SectionHeader>Next Steps</SectionHeader>
            <ol style={{ margin: 0, paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
              {proposal.next_steps.map((step, i) => (
                <li key={i} style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.55 }}>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Actions */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "16px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => setState(isSaved ? "default" : "saved")}
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
              onClick={() => setState(isFlagged ? "default" : "flagged")}
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

          {/* Post-generation actions — shown in split-view context */}
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
