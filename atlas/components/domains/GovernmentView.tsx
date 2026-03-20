"use client";

import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

type ReportSection = {
  id: string;
  title: string;
  description: string;
  requirements: string[];
  reportType: string;
};

const REPORTS: ReportSection[] = [
  {
    id: "strong-workforce",
    title: "Strong Workforce Program Report",
    description:
      "Analyzes program-level outcomes including job placement rates, wage data, and employer satisfaction surveys required for California's Strong Workforce Program annual reporting cycle. Reporting drives allocation decisions for the $248M statewide CTE investment.",
    requirements: [
      "MIS Enrollment & Completion Submission",
      "Employment Development Department wage match",
      "CTE completer follow-up survey data",
      "Employer satisfaction records",
      "Program-level outcome disaggregation",
    ],
    reportType: "strong_workforce",
  },
  {
    id: "perkins-v",
    title: "Perkins V Report",
    description:
      "Generates Comprehensive Local Needs Assessment documentation aligned to Carl D. Perkins V federal requirements, including disaggregated student performance indicators and equity gap analysis across all CTE programs. Required for continued federal CTE funding eligibility.",
    requirements: [
      "CALPADS cross-match for student demographics",
      "Prior year Perkins performance indicators",
      "Equity gap analysis by population subgroup",
      "Local advisory committee meeting records",
      "Program improvement action plan data",
    ],
    reportType: "perkins_v",
  },
];

function CheckIcon({ dim }: { dim?: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0, marginTop: "1px" }}>
      <circle cx="7" cy="7" r="6.5" stroke={dim ? "#d1d5db" : "#c9a84c"} />
      <path
        d="M4.5 7l1.75 1.75L9.5 5.5"
        stroke={dim ? "#d1d5db" : "#c9a84c"}
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function GovernmentView() {
  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "56px 40px 80px",
        display: "flex",
        flexDirection: "column",
        gap: "32px",
      }}
    >
      {/* Page heading */}
      <div style={{ marginBottom: "8px" }}>
        <h1
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "24px",
            fontWeight: 600,
            color: "#111827",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
          }}
        >
          Compliance Reporting
        </h1>
        <p
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            color: "#6b7280",
            lineHeight: 1.6,
          }}
        >
          Generate workforce development reports required by California and federal mandate.
          Connect institutional data to activate each workflow.
        </p>
      </div>

      {REPORTS.map((report) => (
        <Card key={report.id} style={{ padding: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <h2
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "17px",
                fontWeight: 600,
                color: "#111827",
                letterSpacing: "-0.01em",
              }}
            >
              {report.title}
            </h2>
            <Badge variant="gold">Ready to Generate</Badge>
          </div>

          <p
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "14px",
              lineHeight: 1.65,
              color: "#374151",
              marginBottom: "24px",
            }}
          >
            {report.description}
          </p>

          {/* Data requirement checklist */}
          <div
            style={{
              background: "#fafaf9",
              border: "1px solid #f0ede6",
              borderRadius: "8px",
              padding: "16px 20px",
              marginBottom: "24px",
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "11px",
                fontWeight: 600,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "#9ca3af",
                marginBottom: "12px",
              }}
            >
              Required Data Inputs
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {report.requirements.map((req) => (
                <div key={req} style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                  <CheckIcon dim />
                  <span
                    style={{
                      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                      fontSize: "13px",
                      color: "#9ca3af",
                      lineHeight: 1.5,
                    }}
                  >
                    {req}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div
              title="Connect your institutional data submission to enable report generation"
              style={{ display: "inline-block" }}
            >
              <Button variant="solid-gold" disabled>
                Generate Report
              </Button>
            </div>
            <span
              style={{
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "12px",
                color: "#9ca3af",
              }}
            >
              Requires data connection to activate
            </span>
          </div>
        </Card>
      ))}
    </div>
  );
}
