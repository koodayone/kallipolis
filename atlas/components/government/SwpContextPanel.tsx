"use client";

import type { ApiLmiContext, ApiTargetedProposal } from "@/lib/api";
import Badge from "@/components/ui/Badge";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  lmiContext: ApiLmiContext | null;
  proposal: ApiTargetedProposal;
  brandColor: string;
};

export default function SwpContextPanel({ lmiContext, proposal, brandColor }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>

      {/* LMI Demand / Supply Table */}
      {lmiContext && (
        <div>
          <SectionHeader>Labor Market Intelligence — Demand &amp; Supply</SectionHeader>

          {/* Demand table */}
          <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "16px" }}>
            <thead>
              <tr>
                {["SOC Code", "Occupation", "Region", "Wage", "Demand"].map((h) => (
                  <th key={h} style={{
                    fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                    textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                    textAlign: "left", padding: "6px 8px",
                    borderBottom: "1px solid rgba(255,255,255,0.08)",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lmiContext.occupations.map((occ, i) => (
                <tr key={i}>
                  <td style={cellStyle}>{occ.soc_code}</td>
                  <td style={cellStyle}>{occ.title}</td>
                  <td style={cellStyle}>{occ.region}</td>
                  <td style={cellStyle}>{occ.annual_wage ? `$${occ.annual_wage.toLocaleString()}` : "—"}</td>
                  <td style={cellStyle}>{occ.employment ? occ.employment.toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Supply table */}
          {lmiContext.supply_estimates.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "16px" }}>
              <thead>
                <tr>
                  {["TOP Group", "Department(s)", "Est. Annual Completions"].map((h) => (
                    <th key={h} style={{
                      fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                      textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                      textAlign: "left", padding: "6px 8px",
                      borderBottom: "1px solid rgba(255,255,255,0.08)",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {lmiContext.supply_estimates.map((s, i) => (
                  <tr key={i}>
                    <td style={cellStyle}>{s.top_title}</td>
                    <td style={cellStyle}>{s.department}</td>
                    <td style={cellStyle}>{s.estimated_annual_completions.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Gap summary */}
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "12px 16px", borderRadius: "8px",
            background: lmiContext.gap_eligible ? "rgba(74,222,128,0.06)" : "rgba(248,113,113,0.06)",
            border: `1px solid ${lmiContext.gap_eligible ? "rgba(74,222,128,0.15)" : "rgba(248,113,113,0.15)"}`,
          }}>
            <div style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)" }}>
              <span style={{ fontWeight: 500 }}>Demand:</span> {lmiContext.total_demand.toLocaleString()}
              {" · "}
              <span style={{ fontWeight: 500 }}>Supply:</span> {lmiContext.total_supply.toLocaleString()}
              {" · "}
              <span style={{ fontWeight: 500 }}>Gap:</span> {lmiContext.gap > 0 ? "+" : ""}{lmiContext.gap.toLocaleString()}
            </div>
            <Badge style={{
              color: lmiContext.gap_eligible ? "rgba(74,222,128,0.9)" : "rgba(248,113,113,0.9)",
              background: lmiContext.gap_eligible ? "rgba(74,222,128,0.15)" : "rgba(248,113,113,0.15)",
              border: `1px solid ${lmiContext.gap_eligible ? "rgba(74,222,128,0.3)" : "rgba(248,113,113,0.3)"}`,
            }}>
              {lmiContext.gap_eligible ? "Eligible for Funding" : "Supply Exceeds Demand"}
            </Badge>
          </div>
        </div>
      )}

      {/* Skill Alignment */}
      {proposal.curriculum_alignment.length > 0 && (
        <div>
          <SectionHeader>Curriculum Alignment ({proposal.curriculum_alignment.length} connections)</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {proposal.curriculum_alignment.slice(0, 6).map((a, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: FONT, fontSize: "12px" }}>
                <span style={{ color: "rgba(255,255,255,0.35)", minWidth: "90px" }}>{a.department}</span>
                <span style={{ color: brandColor, fontWeight: 600 }}>{a.course_code}</span>
                <span style={{ color: "rgba(255,255,255,0.55)" }}>→</span>
                <span style={{
                  padding: "2px 8px", borderRadius: "100px", fontSize: "11px",
                  background: `${brandColor}15`, border: `1px solid ${brandColor}30`, color: brandColor,
                }}>{a.skill}</span>
              </div>
            ))}
            {proposal.curriculum_alignment.length > 6 && (
              <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                + {proposal.curriculum_alignment.length - 6} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Skill Gaps */}
      {proposal.skill_gaps.length > 0 && (
        <div>
          <SectionHeader>Skill Gaps ({proposal.skill_gaps.length})</SectionHeader>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {proposal.skill_gaps.map((g, i) => (
              <span key={i} style={{
                fontFamily: FONT, fontSize: "11px", color: "rgba(248,113,113,0.8)",
                background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.15)",
                borderRadius: "100px", padding: "3px 10px",
              }}>{g.skill}</span>
            ))}
          </div>
        </div>
      )}

      {/* Student Pipeline */}
      <div>
        <SectionHeader>Student Pipeline</SectionHeader>
        <div style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.8 }}>
          <span style={{ fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
            {proposal.student_pipeline.total_students.toLocaleString()}
          </span> students with relevant skills
          {" · "}
          <span style={{ fontWeight: 500, color: "rgba(255,255,255,0.8)" }}>
            {proposal.student_pipeline.students_with_3plus_courses.toLocaleString()}
          </span> with 3+ completed courses
        </div>
      </div>

      {/* Economic Context */}
      {proposal.economic_impact.occupations.length > 0 && (
        <div>
          <SectionHeader>Economic Context</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {proposal.economic_impact.occupations.map((occ, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT, fontSize: "12px" }}>
                <span style={{ color: "rgba(255,255,255,0.6)" }}>{occ.title}</span>
                <div style={{ display: "flex", gap: "16px" }}>
                  {occ.annual_wage && <span style={{ color: "rgba(255,255,255,0.5)" }}>${occ.annual_wage.toLocaleString()}/yr</span>}
                  {occ.employment && <span style={{ color: "rgba(255,255,255,0.4)" }}>{occ.employment.toLocaleString()} employed</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const cellStyle: React.CSSProperties = {
  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
  fontSize: "12px",
  color: "rgba(255,255,255,0.6)",
  padding: "6px 8px",
  borderBottom: "1px solid rgba(255,255,255,0.04)",
};

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
      fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
      textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
      display: "block", marginBottom: "10px",
    }}>
      {children}
    </span>
  );
}
