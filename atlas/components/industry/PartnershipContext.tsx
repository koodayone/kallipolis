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
