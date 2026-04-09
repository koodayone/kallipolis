"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ApiSwpProject, ApiSwpSection, ApiLmiContext } from "@/lib/api";
import Badge from "@/components/ui/Badge";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

const NOVA_LABELS: Record<string, string> = {
  project_name: "NOVA Part I/III",
  rationale: "NOVA Part III",
  sector: "NOVA Part III",
  employer_narrative: "NOVA Part V",
  metrics_narrative: "NOVA Part VII",
  workplan_activities: "NOVA Part VIII",
  workplan_outcomes: "NOVA Part VIII",
  risks: "NOVA Part III",
};

type Props = {
  project: ApiSwpProject | null;
  streamedSections: ApiSwpSection[];
  lmiContext: ApiLmiContext | null;
  brandColor: string;
  isStreaming: boolean;
};

export default function SwpArtifact({ project, streamedSections, lmiContext, brandColor, isStreaming }: Props) {
  // Use complete project sections if available, otherwise streamed sections
  const sections = project?.sections ?? streamedSections;
  const lmi = project?.lmi_context ?? lmiContext;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* LMI section — structured data, rendered immediately */}
      {lmi && <LmiSection lmi={lmi} brandColor={brandColor} />}

      {/* Claude-generated narrative sections — animate in as they arrive */}
      <AnimatePresence>
        {sections.map((section, i) => (
          <motion.div
            key={section.key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <SectionCard index={i + 1} section={section} brandColor={brandColor} />
          </motion.div>
        ))}
      </AnimatePresence>

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
            Generating section {sections.length + 1} of 8...
          </span>
        </div>
      )}
    </div>
  );
}

function SectionCard({ index, section, brandColor }: {
  index: number;
  section: { key: string; title: string; content: string; char_limit: number | null };
  brandColor: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(section.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [section.content]);

  const novaLabel = NOVA_LABELS[section.key] || "";
  const charCount = section.content.length;
  const overLimit = section.char_limit && charCount > section.char_limit;

  return (
    <div style={{
      padding: "20px", background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px",
    }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 700, color: brandColor,
            background: `${brandColor}15`, borderRadius: "4px", padding: "2px 6px",
          }}>{index}</span>
          <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
            {section.title}
          </span>
          {novaLabel && (
            <span style={{ fontFamily: FONT, fontSize: "10px", color: "rgba(255,255,255,0.25)" }}>
              {novaLabel}
            </span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {section.char_limit && (
            <span style={{
              fontFamily: FONT, fontSize: "10px",
              color: overLimit ? "rgba(248,113,113,0.8)" : "rgba(255,255,255,0.2)",
            }}>
              {charCount.toLocaleString()}/{section.char_limit.toLocaleString()}
            </span>
          )}
          <button
            onClick={handleCopy}
            style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 500, cursor: "pointer",
              border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px",
              background: copied ? "rgba(74,222,128,0.1)" : "transparent",
              color: copied ? "rgba(74,222,128,0.8)" : "rgba(255,255,255,0.4)",
              padding: "3px 8px",
            }}
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{
        fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.65)",
        lineHeight: 1.7, whiteSpace: "pre-wrap",
      }}>
        {section.content}
      </div>
    </div>
  );
}

function LmiSection({ lmi, brandColor }: { lmi: ApiLmiContext; brandColor: string }) {
  const [copied, setCopied] = useState(false);

  const lmiText = [
    "Occupational Cluster — Demand & Supply Analysis",
    "",
    "Demand (Centers of Excellence Projections):",
    ...lmi.occupations.map(o =>
      `  ${o.soc_code} ${o.title} — ${o.region}: ${o.annual_wage ? `$${o.annual_wage.toLocaleString()}/yr` : "wage N/A"}, ${o.annual_openings ? `${o.annual_openings.toLocaleString()} annual openings` : "openings N/A"}`
    ),
    "",
    "Supply (COE Projected Annual, by TOP Code):",
    ...lmi.supply_estimates.map(s =>
      `  ${s.top_title} (${s.award_level}): ${s.annual_projected_supply}`
    ),
    "",
    `Total Demand (Annual Openings): ${lmi.total_demand.toLocaleString()}`,
    `Total Supply (Annual Projected): ${Math.round(lmi.total_supply).toLocaleString()}`,
    `Gap: ${lmi.gap > 0 ? "+" : ""}${Math.round(lmi.gap).toLocaleString()}`,
    `Eligibility: ${lmi.gap_eligible ? "Demand Exceeded — Eligible for Funding" : "Supply Exceeds Demand"}`,
  ].join("\n");

  const handleCopy = () => {
    navigator.clipboard.writeText(lmiText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={{
      padding: "20px",
      background: lmi.gap_eligible ? "rgba(74,222,128,0.03)" : "rgba(248,113,113,0.03)",
      border: `1px solid ${lmi.gap_eligible ? "rgba(74,222,128,0.1)" : "rgba(248,113,113,0.1)"}`,
      borderRadius: "8px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 700, color: brandColor,
            background: `${brandColor}15`, borderRadius: "4px", padding: "2px 6px",
          }}>LMI</span>
          <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>
            Occupational Cluster — Demand &amp; Supply
          </span>
          <span style={{ fontFamily: FONT, fontSize: "10px", color: "rgba(255,255,255,0.25)" }}>
            NOVA Part VI
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Badge style={{
            color: lmi.gap_eligible ? "rgba(74,222,128,0.9)" : "rgba(248,113,113,0.9)",
            background: lmi.gap_eligible ? "rgba(74,222,128,0.15)" : "rgba(248,113,113,0.15)",
            border: `1px solid ${lmi.gap_eligible ? "rgba(74,222,128,0.3)" : "rgba(248,113,113,0.3)"}`,
          }}>
            {lmi.gap_eligible ? "Eligible" : "Not Eligible"}
          </Badge>
          <button
            onClick={handleCopy}
            style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 500, cursor: "pointer",
              border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px",
              background: copied ? "rgba(74,222,128,0.1)" : "transparent",
              color: copied ? "rgba(74,222,128,0.8)" : "rgba(255,255,255,0.4)",
              padding: "3px 8px",
            }}
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>

      {/* Demand table */}
      <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "12px" }}>
        <thead>
          <tr>
            {["SOC Code", "Occupation", "Region", "Wage", "Annual Openings"].map((h) => (
              <th key={h} style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                textAlign: "left", padding: "5px 6px",
                borderBottom: "1px solid rgba(255,255,255,0.06)",
              }}>{h}</th>
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
                <th key={h} style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                  textTransform: "uppercase", color: "rgba(255,255,255,0.3)",
                  textAlign: h === "Annual Supply" ? "right" : "left", padding: "5px 6px",
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                }}>{h}</th>
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
    </div>
  );
}

const tCellStyle: React.CSSProperties = {
  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
  fontSize: "11px",
  color: "rgba(255,255,255,0.55)",
  padding: "5px 6px",
  borderBottom: "1px solid rgba(255,255,255,0.03)",
};
