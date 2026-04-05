"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import type { ApiTargetedProposal } from "@/lib/api";
import { getOccupationDetail } from "@/lib/api";
import { saveProposal, removeProposal, updateProposalStatus, type SavedProposal } from "@/lib/savedProposals";
import OccupationRow from "@/components/shared/OccupationRow";
import DepartmentRow from "@/components/shared/DepartmentRow";
import StudentRow from "@/components/shared/StudentRow";
import ColumnHeaders from "@/components/shared/ColumnHeaders";

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

  // Occupation detail loading for expand
  const [occDetails, setOccDetails] = useState<Record<string, any>>({});
  const [loadingOccs, setLoadingOccs] = useState<Set<string>>(new Set());

  const handleOccExpand = useCallback(async (socCode: string) => {
    if (occDetails[socCode] || !collegeId || !socCode) return;
    setLoadingOccs(prev => new Set(prev).add(socCode));
    try {
      const detail = await getOccupationDetail(socCode, collegeId);
      setOccDetails(prev => ({ ...prev, [socCode]: detail }));
    } catch {}
    finally { setLoadingOccs(prev => { const next = new Set(prev); next.delete(socCode); return next; }); }
  }, [occDetails, collegeId]);



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
          {proposal.advisory_thesis && (
            <div style={{
              marginTop: "12px", padding: "12px 16px",
              borderLeft: `2px solid ${brandColor}40`,
              background: `${brandColor}08`, borderRadius: "0 6px 6px 0",
            }}>
              <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "6px" }}>
                Thesis
              </span>
              <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.75)", lineHeight: 1.6, margin: 0, fontStyle: "italic" }}>
                {proposal.advisory_thesis}
              </p>
            </div>
          )}
          <div style={{ marginTop: "12px" }}>
            <ColumnHeaders
              columns={[
                { label: "Occupation", width: "1fr" },
                { label: "Wage", width: "100px", align: "right" },
                { label: "Openings", width: "80px", align: "right" },
                { label: "Growth", width: "110px", align: "right" },
              ]}
              gridTemplateColumns="24px 1fr 100px 80px 110px"
              brandColor={brandColor}
            />
            {proposal.opportunity_evidence.map((occ, i) => (
              <OccupationRow
                key={occ.title}
                occ={occ}
                index={i}
                brandColor={brandColor}
                detail={occ.soc_code ? occDetails[occ.soc_code] ?? null : null}
                isLoading={occ.soc_code ? loadingOccs.has(occ.soc_code) : false}
                onExpand={occ.soc_code ? () => handleOccExpand(occ.soc_code!) : undefined}
                filterSkills={proposal.core_skills}
                regionNames={proposal.regions}
                collegeName={collegeId}
              />
            ))}
          </div>
        </div>

        {/* ── Curriculum Alignment ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Curriculum Alignment</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.curriculum_composition}
          </p>
          <div style={{ marginTop: "12px" }}>
            <ColumnHeaders
              columns={[
                { label: "Department", width: "1fr" },
                { label: "Courses", width: "auto", align: "right" },
              ]}
              gridTemplateColumns="24px 1fr auto"
              brandColor={brandColor}
            />
            {proposal.justification.curriculum_evidence.map((dept, i) => (
              <DepartmentRow
                key={dept.department}
                department={dept.department}
                courseCount={dept.courses.length}
                index={i}
                brandColor={brandColor}
                courses={dept.courses.map(c => ({
                  code: c.code, name: c.name, description: c.description,
                  learningOutcomes: c.learning_outcomes, skillMappings: c.skills,
                }))}
              />
            ))}
          </div>
        </div>

        {/* ── Student Pipeline ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Student Pipeline</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.justification.student_composition}
          </p>
          {/* Stats bar */}
          <div style={{
            marginTop: "12px",
            background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.05)",
          }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", padding: "16px 0" }}>
              <span style={{ fontFamily: FONT, fontSize: "20px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
                {proposal.justification.student_evidence.total_in_program.toLocaleString()}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
                Students in Aligned Programs
              </span>
            </div>
          </div>
          {/* Top compatible students */}
          {proposal.justification.student_evidence.top_students.length > 0 && (
            <div style={{ marginTop: "12px" }}>
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
                textTransform: "uppercase", color: "rgba(255,255,255,0.25)",
                display: "block", marginBottom: "8px", paddingLeft: "16px",
              }}>
                Top 10 Candidates
              </span>
              <ColumnHeaders
                columns={[
                  { label: "Student", width: "110px" },
                  { label: "Primary Focus", width: "1fr" },
                  { label: "Skills", width: "90px" },
                  { label: "GPA", width: "60px" },
                ]}
                gridTemplateColumns="24px 110px 1fr 90px 60px"
                brandColor={brandColor}
              />
              {proposal.justification.student_evidence.top_students.map((s, i) => (
                <StudentRow
                  key={s.uuid}
                  totalCoreSkills={proposal.core_skills.length}
                  student={{
                    uuid: s.uuid,
                    displayNumber: s.display_number,
                    primaryFocus: s.primary_focus,
                    coursesCompleted: s.courses_completed,
                    gpa: s.gpa,
                    matchingSkills: s.matching_skills,
                  }}
                  index={i}
                  brandColor={brandColor}
                  detail={{
                    enrollments: (s.enrollments || []).map(e => ({
                      courseCode: e.code, courseName: e.name,
                      grade: e.grade, term: e.term,
                      department: "", status: "",
                    })),
                    skills: s.relevant_skills || [],
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Roadmap ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Roadmap</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.roadmap}
          </p>
          {proposal.agenda_topics && proposal.agenda_topics.length > 0 && (
            <div style={{ marginTop: "14px" }}>
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                textTransform: "uppercase", color: "rgba(255,255,255,0.25)",
                display: "block", marginBottom: "8px",
              }}>
                Inaugural Agenda
              </span>
              {proposal.agenda_topics.map((topic, i) => (
                <div key={i} style={{
                  padding: "10px 14px", marginBottom: "6px",
                  background: "rgba(255,255,255,0.03)", borderRadius: "6px",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}>
                  <p style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.8)", margin: 0, lineHeight: 1.5 }}>
                    {topic.topic}
                  </p>
                  {topic.rationale && (
                    <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", margin: "4px 0 0 0", lineHeight: 1.5 }}>
                      {topic.rationale}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
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
