import React from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";

type DemandRow = {
  soc_code?: string | null;
  title: string;
  annual_wage?: number | null;
  annual_openings?: number | null;
};

function ColHead({ brandColor, align, children }: {
  brandColor: string;
  align?: "left" | "right";
  children: React.ReactNode;
}) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: "10px", fontWeight: 600,
      letterSpacing: "0.08em", textTransform: "uppercase",
      color: brandColor, opacity: 0.55,
      textAlign: align ?? "left",
    }}>
      {children}
    </span>
  );
}

/**
 * Regional demand table (SOC · occupation · wage · annual openings). Extracted
 * verbatim from the Labor Market Information section of OpportunityReport so the
 * per-college occupation report and the SVAMP Programs lens render the same
 * table from one source. `label` defaults to the occupation report's heading
 * (so that caller is byte-identical); the Programs lens overrides it.
 */
export default function OccupationDemandTable({
  rows, brandColor, label = "Demand: regional annual openings by SOC",
}: {
  rows: DemandRow[];
  brandColor: string;
  label?: string;
}) {
  return (
    <div style={{ marginTop: "20px" }}>
      <span style={{
        fontFamily: FONT, fontSize: "12px", fontWeight: 600,
        color: "rgba(255,255,255,0.7)",
        display: "block", marginBottom: "10px",
      }}>
        {label}
      </span>
      <div style={{
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: "8px",
        padding: "10px 16px",
      }}>
        <div style={{
          display: "grid", gridTemplateColumns: "90px 1fr 110px 130px",
          gap: "12px", padding: "6px 0",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}>
          <ColHead brandColor={brandColor}>SOC</ColHead>
          <ColHead brandColor={brandColor}>Occupation</ColHead>
          <ColHead brandColor={brandColor} align="right">Wage</ColHead>
          <ColHead brandColor={brandColor} align="right">Annual openings</ColHead>
        </div>
        {rows.map((o) => (
          <div
            key={o.soc_code ?? o.title}
            style={{
              display: "grid", gridTemplateColumns: "90px 1fr 110px 130px",
              gap: "12px", padding: "10px 0",
              alignItems: "baseline",
            }}
          >
            <span style={{ fontFamily: MONO, fontSize: "12px", color: "rgba(255,255,255,0.55)" }}>
              {o.soc_code ?? "—"}
            </span>
            <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.78)" }}>
              {o.title}
            </span>
            <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
              {o.annual_wage != null ? `$${o.annual_wage.toLocaleString()}` : "—"}
            </span>
            <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
              {o.annual_openings != null ? o.annual_openings.toLocaleString() : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
