"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { ApiSwpProject, ApiSwpSection, ApiLmiContext } from "@/lib/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function SectionHeader({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
      textTransform: "uppercase", color: color || "rgba(255,255,255,0.3)",
      display: "block", marginBottom: "10px", opacity: 0.65,
    }}>
      {children}
    </span>
  );
}

const proseStyle: React.CSSProperties = {
  fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)",
  lineHeight: 1.65, margin: 0, whiteSpace: "pre-wrap",
};

const tCellStyle: React.CSSProperties = {
  fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.55)",
  padding: "5px 6px", borderBottom: "1px solid rgba(255,255,255,0.03)",
};

function thStyle(brandColor: string): React.CSSProperties {
  return {
    fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
    textTransform: "uppercase", color: brandColor, opacity: 0.65,
    textAlign: "left", padding: "5px 6px",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  };
}

type Props = {
  project: ApiSwpProject | null;
  streamedSections: ApiSwpSection[];
  lmiContext: ApiLmiContext | null;
  brandColor: string;
  isStreaming: boolean;
};

export default function SwpArtifact({ project, streamedSections, lmiContext, brandColor, isStreaming }: Props) {
  const sections = project?.sections ?? streamedSections;
  const lmi = project?.lmi_context ?? lmiContext;

  const find = (key: string) => sections.find(s => s.key === key);

  const projectName = find("project_name");
  const projectDescription = find("project_description");
  const rationale = find("rationale");
  const studentImpact = find("student_impact");
  const visionGoal = find("vision_goal");
  const objective = find("objective");
  const activity = find("activity");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{
          padding: "28px", background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px",
        }}>

          {/* Header */}
          {projectName && (
            <div style={{ marginBottom: "20px" }}>
              <h3 style={{
                fontFamily: FONT, fontSize: "17px", fontWeight: 600,
                color: "rgba(255,255,255,0.9)", letterSpacing: "-0.01em",
                lineHeight: 1.3, margin: 0,
              }}>
                {projectName.content}
              </h3>
            </div>
          )}

          {/* Project Description */}
          {projectDescription && (
            <div style={{ marginBottom: "24px" }}>
              <SectionHeader color={brandColor}>Project Description</SectionHeader>
              <p style={proseStyle}>{projectDescription.content}</p>
            </div>
          )}

          {/* Project Rationale */}
          {rationale && (
            <div style={{ marginBottom: "24px" }}>
              <SectionHeader color={brandColor}>Project Rationale</SectionHeader>
              <p style={proseStyle}>{rationale.content}</p>
            </div>
          )}

          {/* LMI — inline under rationale */}
          {lmi && (
            <div style={{ marginBottom: "24px" }}>
              {/* Demand table */}
              <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "12px" }}>
                <thead>
                  <tr>
                    {["SOC Code", "Occupation", "Region", "Wage", "Annual Openings"].map((h) => (
                      <th key={h} style={thStyle(brandColor)}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lmi.occupations.map((occ, i) => (
                    <tr key={i}>
                      <td style={tCellStyle}>{occ.soc_code}</td>
                      <td style={tCellStyle}>{occ.title}</td>
                      <td style={tCellStyle}>{occ.region}</td>
                      <td style={tCellStyle}>{occ.annual_wage ? `$${occ.annual_wage.toLocaleString()}` : "—"}</td>
                      <td style={tCellStyle}>{occ.annual_openings ? occ.annual_openings.toLocaleString() : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Supply table */}
              {lmi.supply_estimates.length > 0 && (
                <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "12px" }}>
                  <thead>
                    <tr>
                      {["TOP Code", "Program", "Award Level", "Annual Supply"].map((h) => (
                        <th key={h} style={{ ...thStyle(brandColor), textAlign: h === "Annual Supply" ? "right" : "left" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {lmi.supply_estimates.map((s, i) => (
                      <tr key={i}>
                        <td style={tCellStyle}>{s.top_code}</td>
                        <td style={tCellStyle}>{s.top_title}</td>
                        <td style={tCellStyle}>{s.award_level}</td>
                        <td style={{ ...tCellStyle, textAlign: "right" }}>{s.annual_projected_supply}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Gap summary */}
              <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.55)", lineHeight: 1.8 }}>
                <span style={{ fontWeight: 500 }}>Annual Openings:</span> {lmi.total_demand.toLocaleString()}
                {" · "}
                <span style={{ fontWeight: 500 }}>Annual Supply:</span> {Math.round(lmi.total_supply).toLocaleString()}
                {" · "}
                <span style={{ fontWeight: 500 }}>Gap:</span>{" "}
                <span style={{ color: lmi.gap_eligible ? "rgba(74,222,128,0.8)" : "rgba(248,113,113,0.8)" }}>
                  {lmi.gap > 0 ? "+" : ""}{Math.round(lmi.gap).toLocaleString()}
                </span>
              </div>
              <div style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", marginTop: "10px" }}>
                Source: Centers of Excellence for Labor Market Research
              </div>
            </div>
          )}

          {/* Student Impact */}
          {studentImpact && (
            <div style={{ marginBottom: "24px" }}>
              <SectionHeader color={brandColor}>Student Impact</SectionHeader>
              <p style={proseStyle}>{studentImpact.content}</p>
              {lmi && lmi.department_enrollments && lmi.department_enrollments.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        <th style={thStyle(brandColor)}>Department</th>
                        <th style={{ ...thStyle(brandColor), textAlign: "right" }}>Students</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lmi.department_enrollments.map((d, i) => (
                        <tr key={i}>
                          <td style={tCellStyle}>{d.department}</td>
                          <td style={{ ...tCellStyle, textAlign: "right" }}>{d.student_count.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.55)", lineHeight: 1.8, marginTop: "8px" }}>
                    <span style={{ fontWeight: 500 }}>Total Students:</span>{" "}
                    {lmi.department_enrollments.reduce((sum, d) => sum + d.student_count, 0).toLocaleString()}
                  </div>
                  <div style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", marginTop: "6px" }}>
                    Source: California Community Colleges Chancellor's Office MIS Data Mart
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Vision for Success */}
          {visionGoal && (
            <div style={{ marginBottom: "24px" }}>
              <SectionHeader color={brandColor}>Vision for Success</SectionHeader>
              <p style={proseStyle}>{visionGoal.content}</p>
            </div>
          )}

          {/* Objective */}
          {objective && (
            <div style={{ marginBottom: "24px" }}>
              <SectionHeader color={brandColor}>Objective</SectionHeader>
              <p style={proseStyle}>{objective.content}</p>
            </div>
          )}

          {/* Activity */}
          {activity && (
            <div style={{ marginBottom: "0" }}>
              <SectionHeader color={brandColor}>Activity</SectionHeader>
              <p style={proseStyle}>{activity.content}</p>
            </div>
          )}

        </div>
      </motion.div>

      {/* Streaming indicator */}
      {isStreaming && (
        <div style={{
          display: "flex", alignItems: "center", gap: "10px",
          padding: "16px", borderRadius: "8px",
          background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.08)",
        }}>
          <div style={{
            width: "16px", height: "16px",
            border: "2px solid rgba(255,255,255,0.08)", borderTopColor: brandColor,
            borderRadius: "50%", animation: "spin 1s linear infinite",
          }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.35)" }}>
            Generating section {sections.length + 1} of 7...
          </span>
        </div>
      )}
    </div>
  );
}
