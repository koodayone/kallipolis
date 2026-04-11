"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import DataCitation from "@/ui/DataCitation";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

function formatWage(wage: number | null): string {
  if (!wage) return "\u2014";
  return `$${wage.toLocaleString()}`;
}

export type OccupationData = {
  title: string;
  soc_code?: string | null;
  annual_wage?: number | null;
  employment?: number | null;
  growth_rate?: number | null;
  annual_openings?: number | null;
  description?: string | null;
  matching_skills?: number;
  skills?: string[];
};

export type OccupationDetail = {
  soc_code: string;
  title: string;
  description?: string | null;
  skills: Array<{ skill: string; developed: boolean; courses: Array<{ code: string; name: string }> }>;
  regions: Array<{ region: string; employment: number; annual_wage?: number | null; growth_rate?: number | null; annual_openings?: number | null }>;
};

type Props = {
  occ: OccupationData;
  index: number;
  brandColor: string;
  // Controlled mode (analytical view)
  isOpen?: boolean;
  onToggle?: () => void;
  // Detail data
  detail?: OccupationDetail | null;
  isLoading?: boolean;
  onExpand?: () => void;
  // Filter aligned skills to only these (proposal context)
  filterSkills?: string[];
  // Region context for detail view
  regionNames?: string[];
  collegeName?: string;
};

export default function OccupationRow({ occ, index, brandColor, isOpen: controlledOpen, onToggle, detail, isLoading, onExpand, filterSkills, regionNames, collegeName }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen = controlledOpen ?? internalOpen;

  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);

  const handleClick = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalOpen(!internalOpen);
    }
    onExpand?.();
  };

  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={handleClick}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr 100px 80px 110px",
          padding: "12px 16px", gap: "10px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
          border: "none", borderBottom: "1px solid rgba(255,255,255,0.05)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)"; }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4 }}>
          {occ.title}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "right" }}>
          {formatWage(occ.annual_wage ?? null)}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>
          {occ.annual_openings != null ? `${occ.annual_openings.toLocaleString()}/yr` : "\u2014"}
        </span>
        <span style={{
          fontFamily: FONT, fontSize: "12px", fontWeight: 500, textAlign: "right",
          color: occ.growth_rate != null ? (occ.growth_rate >= 0 ? "#4ade80" : "#f87171") : "rgba(255,255,255,0.25)",
        }}>
          {occ.growth_rate != null ? `${occ.growth_rate >= 0 ? "+" : ""}${(occ.growth_rate * 100).toFixed(1)}%` : "\u2014"}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div style={{ padding: "16px 20px 24px" }}>
              {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}

              {/* Full detail view (analytical view mode) */}
              {detail && (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {detail.description && (
                    <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: 0 }}>
                      {detail.description}
                    </p>
                  )}
                  {(() => {
                    const developed = detail.skills.filter((s) => s.developed);
                    const aligned = filterSkills
                      ? developed.filter((s) => filterSkills.includes(s.skill))
                      : developed;
                    if (aligned.length === 0) return null;
                    return (
                      <div>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "10px", position: "relative" }}
                          onMouseEnter={(e) => { const tip = e.currentTarget.querySelector("[data-tooltip]") as HTMLElement; if (tip) tip.style.opacity = "1"; }}
                          onMouseLeave={(e) => { const tip = e.currentTarget.querySelector("[data-tooltip]") as HTMLElement; if (tip) tip.style.opacity = "0"; }}
                        >
                          <span style={{
                            fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
                            color: brandColor, opacity: 0.6,
                          }}>
                            Aligned Skills ({aligned.length})
                          </span>
                          <svg width="13" height="13" viewBox="0 0 16 16" fill="none"
                            style={{ cursor: "help", opacity: 0.4, transition: "opacity 0.15s" }}
                            onMouseEnter={(e) => { (e.currentTarget as SVGSVGElement).style.opacity = "0.7"; }}
                            onMouseLeave={(e) => { (e.currentTarget as SVGSVGElement).style.opacity = "0.4"; }}
                          >
                            <circle cx="8" cy="8" r="7" stroke={brandColor} strokeWidth="1" />
                            <circle cx="8" cy="4.5" r="0.8" fill={brandColor} />
                            <rect x="7.2" y="6.5" width="1.6" height="5" rx="0.8" fill={brandColor} />
                          </svg>
                          <span data-tooltip style={{
                            position: "absolute", left: 0, bottom: "calc(100% + 6px)", zIndex: 10,
                            background: "rgba(20,18,28,0.95)", border: `1px solid ${brandColor}20`,
                            borderRadius: "8px", padding: "10px 14px", width: "260px",
                            fontFamily: FONT, fontSize: "11px", fontWeight: 400, letterSpacing: "0",
                            textTransform: "none", color: "rgba(255,255,255,0.55)", lineHeight: 1.5,
                            opacity: 0, pointerEvents: "none", transition: "opacity 0.15s",
                          }}>
                            Skills this occupation requires that {collegeName || "the college"}&apos;s courses develop.
                          </span>
                        </span>
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {aligned.map((skill) => (
                            <div key={skill.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                <circle cx="6" cy="6" r="5" stroke={brandColor} strokeWidth="1" />
                                <path d="M4 6l1.5 1.5L8 5" stroke={brandColor} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                              <span style={{ fontFamily: FONT, fontSize: "13px", color: brandColor }}>{skill.skill}</span>
                              {skill.courses.length > 0 && (
                                <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                                  — {skill.courses.slice(0, 3).map((c) => c.code).join(", ")}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                  {detail.regions.length > 0 && (() => {
                    const localRegions = regionNames
                      ? detail.regions.filter((r) => regionNames.includes(r.region))
                      : detail.regions;
                    if (localRegions.length === 0) return null;
                    return (
                      <div>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: "8px" }}>
                          Regional Employment
                        </span>
                        <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", lineHeight: 1.8 }}>
                          {localRegions.map((r) => (
                            <div key={r.region}>{r.region}: <span style={{ color: "rgba(255,255,255,0.65)", fontWeight: 500 }}>{r.employment.toLocaleString()}</span> currently employed</div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                  <DataCitation source="Centers of Excellence for Labor Market Research" />
                </div>
              )}

              {/* Minimal detail (proposal card mode — no detail prop) */}
              {!detail && !isLoading && (
                <div style={{ display: "flex", gap: "24px" }}>
                  {occ.employment != null && (
                    <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>
                      {occ.employment.toLocaleString()} employed regionally
                    </span>
                  )}
                  {occ.soc_code && (
                    <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)" }}>
                      SOC {occ.soc_code}
                    </span>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
