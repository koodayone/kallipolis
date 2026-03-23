"use client";

import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import LeafHeader from "@/components/ui/LeafHeader";
import { SchoolConfig } from "@/lib/schoolConfig";

const REQUIREMENTS = [
  "CALPADS cross-match for student demographics",
  "Prior year Perkins performance indicators",
  "Equity gap analysis by population subgroup",
  "Local advisory committee meeting records",
  "Program improvement action plan data",
];

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function PerkinsView({ school, onBack }: Props) {
  return (
    <>
    <LeafHeader school={school} onBack={onBack} parentShape="dodecahedron" />
    <div
      style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "32px 40px 80px",
        display: "flex",
        flexDirection: "column",
        gap: "32px",
      }}
    >
      {/* Page heading */}
      <div>
        <h1
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "24px",
            fontWeight: 600,
            color: "#f0eef4",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
          }}
        >
          Perkins V Report
        </h1>
        <p
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            color: "rgba(255,255,255,0.5)",
            lineHeight: 1.6,
          }}
        >
          Generates Comprehensive Local Needs Assessment documentation aligned to Carl D. Perkins V federal
          requirements, including disaggregated student performance indicators and equity gap analysis across
          all CTE programs. Required for continued federal CTE funding eligibility.
        </p>
      </div>

      <Card style={{ padding: "32px", background: school.brandColorDark, border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 2px 12px rgba(0,0,0,0.4)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
          <span
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "13px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.3)",
            }}
          >
            Required Data Inputs
          </span>
          <Badge style={{ color: school.brandColorLight, background: "rgba(123,45,62,0.25)", border: "1px solid rgba(123,45,62,0.35)" }}>
            Ready to Generate
          </Badge>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "32px" }}>
          {REQUIREMENTS.map((req) => (
            <div key={req} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0, marginTop: "1px" }}>
                <circle cx="7" cy="7" r="6.5" stroke="rgba(255,255,255,0.2)" />
                <path d="M4.5 7l1.75 1.75L9.5 5.5" stroke="rgba(255,255,255,0.2)" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "13px",
                  color: "rgba(255,255,255,0.38)",
                  lineHeight: 1.5,
                }}
              >
                {req}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div title="Connect your institutional data submission to enable report generation" style={{ display: "inline-block" }}>
            <Button variant="solid-gold" disabled style={{ background: school.brandColor, borderColor: school.brandColor, color: "#ffffff" }}>
              Generate Report
            </Button>
          </div>
          <span
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "12px",
              color: "rgba(255,255,255,0.35)",
            }}
          >
            Requires data connection to activate
          </span>
        </div>
      </Card>
    </div>
    </>
  );
}
