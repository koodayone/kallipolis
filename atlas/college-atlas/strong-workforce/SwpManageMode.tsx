"use client";

import { motion } from "framer-motion";
import type { SchoolConfig } from "@/config/schoolConfig";
import {
  getSavedSwpProjects,
  removeSwpProject,
  type SavedSwpProject,
} from "@/college-atlas/strong-workforce/savedSwpProjects";
import SwpArtifact from "./SwpArtifact";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  savedSwpProjects: SavedSwpProject[];
  setSavedSwpProjects: (projects: SavedSwpProject[]) => void;
  manageQuery: string;
  setManageQuery: (q: string) => void;
  expandedSwpId: string | null;
  toggleExpanded: (id: string) => void;
};

export default function SwpManageMode({
  school,
  savedSwpProjects,
  setSavedSwpProjects,
  manageQuery,
  setManageQuery,
  expandedSwpId,
  toggleExpanded,
}: Props) {
  if (savedSwpProjects.length === 0) {
    return (
      <div style={{ padding: "40px", textAlign: "center", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" }}>
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", margin: "0 0 8px" }}>No saved SWP projects yet.</p>
        <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)", margin: 0 }}>Generate and save an SWP document from the Build tab.</p>
      </div>
    );
  }

  const filtered = manageQuery.trim()
    ? savedSwpProjects.filter((s) => s.project.employer.toLowerCase().includes(manageQuery.toLowerCase()))
    : savedSwpProjects;

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* Search bar */}
      <div style={{ position: "relative", marginBottom: "16px" }}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"
          style={{ position: "absolute", left: "18px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
          <circle cx="7.5" cy="7.5" r="5.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" />
          <path d="M11.5 11.5L15.5 15.5" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          type="text"
          value={manageQuery}
          onChange={(e) => setManageQuery(e.target.value)}
          placeholder="Search Strong Workforce Program projects for NOVA..."
          style={{
            width: "100%", padding: "18px 24px 18px 48px", fontFamily: FONT, fontSize: "15px",
            color: "#f0eef4", background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.10)", borderRadius: "6px",
            outline: "none",
          }}
        />
      </div>

      {/* Column headers */}
      <div style={{ display: "grid", gridTemplateColumns: "24px 1fr 160px", padding: "12px 16px", gap: "10px", alignItems: "center" }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6 }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: school.brandColorLight, opacity: 0.6, textAlign: "right" }}>Partnership Type</span>
      </div>

      {/* Rows */}
      {filtered.map((saved) => {
        const isExpanded = expandedSwpId === saved.id;
        return (
          <div key={saved.id}>
            <button
              onClick={() => toggleExpanded(saved.id)}
              style={{
                width: "100%", textAlign: "left", cursor: "pointer",
                display: "grid", gridTemplateColumns: "24px 1fr 160px",
                padding: "12px 16px", gap: "10px", alignItems: "center",
                background: isExpanded ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
                border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                style={{ transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
                <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>
                {saved.project.employer}
              </span>
              <span style={{ textAlign: "right", fontFamily: FONT, fontSize: "11px", fontWeight: 600, color: school.brandColorLight }}>
                {saved.project.partnership_type}
              </span>
            </button>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                transition={{ duration: 0.25 }}
                style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
              >
                <div style={{ padding: "16px 20px 24px" }}>
                  <SwpArtifact
                    project={saved.project}
                    streamedSections={saved.project.sections}
                    lmiContext={saved.project.lmi_context}
                    brandColor={school.brandColorLight}
                    isStreaming={false}
                  />
                  <button
                    onClick={() => {
                      removeSwpProject(school.name, saved.id);
                      setSavedSwpProjects(getSavedSwpProjects(school.name));
                    }}
                    style={{
                      marginTop: "16px", fontFamily: FONT, fontSize: "11px", cursor: "pointer",
                      border: "1px solid rgba(255,255,255,0.08)", borderRadius: "4px",
                      background: "transparent", color: "rgba(255,255,255,0.3)", padding: "4px 10px",
                    }}
                  >Remove</button>
                </div>
              </motion.div>
            )}
          </div>
        );
      })}
    </div>
  );
}
