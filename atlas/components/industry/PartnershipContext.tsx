"use client";

import { SchoolConfig } from "@/lib/schoolConfig";
import type { ApiPartnershipOpportunity, ApiEmployerDetail } from "@/lib/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

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

type Props = {
  employer: ApiPartnershipOpportunity;
  detail: ApiEmployerDetail | null;
  pipelineSize: number | null;
  school: SchoolConfig;
};

export default function PartnershipContext({ employer, detail, pipelineSize, school }: Props) {
  const totalSkills = employer.alignment_score + employer.gap_count;
  const alignmentPct = totalSkills > 0 ? (employer.alignment_score / totalSkills) * 100 : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>

      {/* ── Employer Banner ── */}
      <div>
        <h2 style={{ fontFamily: FONT, fontSize: "22px", fontWeight: 600, color: "#f0eef4", letterSpacing: "-0.02em", margin: "0 0 8px" }}>
          {employer.name}
        </h2>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {employer.sector && (
            <span style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.05em",
              padding: "4px 12px", borderRadius: "100px",
              background: `${school.brandColorLight}20`, color: school.brandColorLight,
              border: `1px solid ${school.brandColorLight}40`,
            }}>
              {employer.sector}
            </span>
          )}
        </div>
        {employer.description && (
          <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: "12px 0 0" }}>
            {employer.description}
          </p>
        )}
      </div>

      {/* ── Skill Alignment Overview ── */}
      <div>
        <SectionHeader color={school.brandColorLight + "99"}>Skill Alignment</SectionHeader>
        <div style={{ fontFamily: FONT, fontSize: "20px", fontWeight: 600, color: "#f0eef4", marginBottom: "10px" }}>
          {employer.alignment_score} <span style={{ fontSize: "14px", fontWeight: 400, color: "rgba(255,255,255,0.4)" }}>of {totalSkills} skills aligned</span>
        </div>
        {/* Alignment bar */}
        <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.06)", borderRadius: "4px", overflow: "hidden" }}>
          <div style={{
            width: `${alignmentPct}%`, height: "100%",
            background: school.brandColorLight, borderRadius: "4px",
            transition: "width 0.5s ease",
          }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px", fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
          <span>{employer.alignment_score} aligned</span>
          <span>{employer.gap_count} gaps</span>
        </div>
      </div>

      {/* ── Aligned Skills ── */}
      {detail ? (
        <div>
          <SectionHeader>Aligned Skills ({employer.alignment_score})</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {detail.occupations.map((occ) => {
              const aligned = (occ.skills || []).filter((s: any) => s.developed);
              if (aligned.length === 0) return null;
              return (
                <div key={occ.soc_code}>
                  <div style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.55)", marginBottom: "6px" }}>
                    {occ.title}
                    {occ.annual_wage && <span style={{ color: "rgba(255,255,255,0.3)" }}> · ${occ.annual_wage.toLocaleString()}/yr</span>}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", paddingLeft: "8px" }}>
                    {aligned.map((skill: any) => (
                      <div key={skill.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                          <circle cx="6" cy="6" r="5" stroke={school.brandColorLight} strokeWidth="1" />
                          <path d="M4 6l1.5 1.5L8 5" stroke={school.brandColorLight} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span style={{ fontFamily: FONT, fontSize: "12px", color: school.brandColorLight }}>{skill.skill}</span>
                        {skill.courses?.length > 0 && (
                          <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.25)" }}>
                            — {skill.courses.slice(0, 3).map((c: any) => c.code).join(", ")}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div>
          <SectionHeader>Aligned Skills ({employer.alignment_score})</SectionHeader>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {employer.aligned_skills.map((skill) => (
              <span key={skill} style={{
                fontFamily: FONT, fontSize: "11px", color: school.brandColorLight,
                background: `${school.brandColorLight}15`, border: `1px solid ${school.brandColorLight}30`,
                borderRadius: "100px", padding: "4px 10px",
              }}>{skill}</span>
            ))}
          </div>
        </div>
      )}

      {/* ── Skill Gaps ── */}
      {employer.gap_skills.length > 0 && (
        <div>
          <SectionHeader>Skill Gaps ({employer.gap_count})</SectionHeader>
          {detail ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {detail.occupations.map((occ) => {
                const gaps = (occ.skills || []).filter((s: any) => !s.developed);
                if (gaps.length === 0) return null;
                return (
                  <div key={occ.soc_code}>
                    <div style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.4)", marginBottom: "6px" }}>
                      {occ.title}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", paddingLeft: "8px" }}>
                      {gaps.map((skill: any) => (
                        <span key={skill.skill} style={{
                          fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)",
                          background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                          borderRadius: "100px", padding: "3px 10px",
                        }}>{skill.skill}</span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {employer.gap_skills.map((skill) => (
                <span key={skill} style={{
                  fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)",
                  background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                  borderRadius: "100px", padding: "4px 10px",
                }}>{skill}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Student Pipeline ── */}
      <div>
        <SectionHeader>Student Pipeline</SectionHeader>
        {pipelineSize !== null ? (
          <div style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)" }}>
            <span style={{ fontSize: "20px", fontWeight: 600, color: "#f0eef4" }}>{pipelineSize.toLocaleString()}</span>
            {" "}students with relevant skills enrolled at this college
          </div>
        ) : (
          <div style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading pipeline data...</div>
        )}
      </div>

      {/* ── Economic Context ── */}
      {detail && detail.occupations.length > 0 && (
        <div>
          <SectionHeader>Economic Context</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {detail.occupations.map((occ) => (
              <div key={occ.soc_code} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: FONT, fontSize: "12px" }}>
                <span style={{ color: "rgba(255,255,255,0.6)" }}>{occ.title}</span>
                {occ.annual_wage && (
                  <span style={{ color: "rgba(255,255,255,0.4)" }}>${occ.annual_wage.toLocaleString()}/yr</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
