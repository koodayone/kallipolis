"use client";

import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import LeafHeader from "@/components/ui/LeafHeader";
import { SchoolConfig } from "@/lib/schoolConfig";

const CAPABILITIES = [
  "Regional employer identification by skill alignment",
  "Workforce hiring volume and wage analysis",
  "Industry sector mapping to college programs",
  "Partnership opportunity scoring and prioritization",
  "Employer-to-curriculum gap analysis",
];

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function EmployersView({ school, onBack }: Props) {
  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="dodecahedron" />
      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>
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
            Employers
          </h1>
          <p
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "14px",
              color: "rgba(255,255,255,0.5)",
              lineHeight: 1.6,
            }}
          >
            Identifies and profiles regional employers whose workforce needs align with the
            college's curriculum and skill production.
          </p>
        </div>

        <Card style={{ padding: "32px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 2px 12px rgba(0,0,0,0.4)" }}>
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
              Planned Capabilities
            </span>
            <Badge style={{ color: school.brandColorLight, background: `${school.brandColorLight}20`, border: `1px solid ${school.brandColorLight}30` }}>
              Coming Soon
            </Badge>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "32px" }}>
            {CAPABILITIES.map((cap) => (
              <div key={cap} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
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
                  {cap}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div title="Employer data integration in progress" style={{ display: "inline-block" }}>
              <Button variant="solid-gold" disabled style={{ background: school.brandColorLight, borderColor: school.brandColorLight, color: "#ffffff" }}>
                Explore Employers
              </Button>
            </div>
            <span
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "12px",
                color: "rgba(255,255,255,0.35)",
              }}
            >
              Employer data integration in progress
            </span>
          </div>
        </Card>
      </div>
    </>
  );
}
