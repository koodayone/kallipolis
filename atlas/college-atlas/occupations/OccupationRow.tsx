"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import DataCitation from "@/ui/DataCitation";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

// Visible cap on the TOP-group list within Curriculum Alignment. Above
// this count, the surface shows the first GROUP_CAP groups + a "Show
// all N program areas" affordance. Trigger fires for SOCs with broad
// TOP fan-in (rare).
const GROUP_CAP = 4;

// Visible cap on courses within a single TOP group. Mirrors the course
// view's per-list cap. Trigger fires for program areas where the
// college offers many courses under one TOP (e.g., a Biology SOC with
// 15+ aligned BIOL courses).
const COURSE_CAP = 8;

function formatWage(wage: number | null): string {
  if (!wage) return "—";
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
  aligned_course_count?: number;
  aligned_department_count?: number;
  // "aligned" (default) — college has aligned curriculum
  // "gap"               — no curriculum at this college; surfaced
  //                       honestly with dim row + minimal message
  alignment_status?: "aligned" | "gap";
};

export type OccupationDetail = {
  soc_code: string;
  title: string;
  description?: string | null;
  aligned_top_groups: Array<{
    top_code: string;
    top_title: string;
    courses: Array<{ code: string; name: string; department: string; via_top: string | null }>;
  }>;
  aligned_course_count: number;
  aligned_program_area_count: number;
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
  // Region context for detail view
  regionNames?: string[];
  collegeName?: string;
  // Context-mode flag — when this row is rendered inside a partnership
  // opportunity report that has its own dedicated Curriculum Alignment
  // section, suppress the inner CA block to avoid surfacing the same
  // material twice.
  hideCurriculumAlignment?: boolean;
};

export default function OccupationRow({ occ, index, brandColor, isOpen: controlledOpen, onToggle, detail, isLoading, onExpand, regionNames, collegeName, hideCurriculumAlignment }: Props) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [showAllGroups, setShowAllGroups] = useState(false);
  const isOpen = controlledOpen ?? internalOpen;

  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);

  // Reset the show-all state whenever a new detail is loaded so the
  // affordance doesn't carry over between SOC expansions.
  useEffect(() => { setShowAllGroups(false); }, [detail?.soc_code]);

  const handleClick = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalOpen(!internalOpen);
    }
    onExpand?.();
  };

  // Gap rows: regionally demanded, CTE-reachable, but no aligned
  // curriculum at this college. Dimmed + badged so they sit in the
  // honest list without dominating scan attention. Same visual story
  // as the gap rows in the partnerships sector accordion.
  const isGap = occ.alignment_status === "gap";

  return (
    <div style={{ opacity: isGap ? 0.55 : 1 }}>
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
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: "8px", flexWrap: "wrap", minWidth: 0 }}>
          <span style={{ fontFamily: FONT, fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4 }}>
            {occ.title}
          </span>
          {isGap && (
            <span
              title="No aligned curriculum at this college"
              style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 500,
                letterSpacing: "0.06em", textTransform: "uppercase",
                color: "rgba(255,255,255,0.5)",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "3px",
                padding: "2px 6px",
                whiteSpace: "nowrap",
              }}
            >
              no current pathway
            </span>
          )}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)", textAlign: "right" }}>
          {formatWage(occ.annual_wage ?? null)}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.45)", textAlign: "right" }}>
          {occ.annual_openings != null ? `${occ.annual_openings.toLocaleString()}/yr` : "—"}
        </span>
        <span style={{
          fontFamily: FONT, fontSize: "12px", fontWeight: 500, textAlign: "right",
          color: occ.growth_rate != null ? (occ.growth_rate >= 0 ? "#4ade80" : "#f87171") : "rgba(255,255,255,0.25)",
        }}>
          {occ.growth_rate != null ? `${occ.growth_rate >= 0 ? "+" : ""}${(occ.growth_rate * 100).toFixed(1)}%` : "—"}
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
            <div style={{ padding: "16px 20px 24px 50px" }}>
              {isLoading && <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>Loading...</p>}

              {/* Full detail view (analytical view mode) */}
              {detail && (() => {
                const localRegions = regionNames
                  ? detail.regions.filter((r) => regionNames.includes(r.region))
                  : detail.regions;
                const primaryRegion = localRegions[0] ?? detail.regions[0] ?? null;

                const visibleGroups = showAllGroups
                  ? detail.aligned_top_groups
                  : detail.aligned_top_groups.slice(0, GROUP_CAP);
                const hiddenGroups = showAllGroups
                  ? []
                  : detail.aligned_top_groups.slice(GROUP_CAP);
                const isCapped = hiddenGroups.length > 0;

                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                    {/* SOC attribution line — folds in regional employment so the
                        orphaned "Regional Employment" section can dissolve. */}
                    {detail.soc_code && (
                      <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
                        <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 500, letterSpacing: "0.05em", color: "rgba(255,255,255,0.4)", fontVariantNumeric: "tabular-nums" }}>
                          SOC {detail.soc_code}
                        </span>
                        {primaryRegion && (
                          <>
                            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>·</span>
                            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.55)" }}>
                              <span style={{ color: "rgba(255,255,255,0.75)", fontWeight: 500 }}>{primaryRegion.employment.toLocaleString()}</span>{" currently employed in "}{primaryRegion.region}
                            </span>
                          </>
                        )}
                      </div>
                    )}

                    {detail.description && (
                      <div>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.7, display: "block", marginBottom: "10px" }}>
                          Description
                        </span>
                        <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.55)", lineHeight: 1.6, margin: 0 }}>
                          {detail.description}
                        </p>
                      </div>
                    )}

                    {!hideCurriculumAlignment && (
                      <div>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.7, display: "block", marginBottom: "10px" }}>
                          Curriculum Alignment
                        </span>

                        {detail.aligned_top_groups.length === 0 ? (
                          // Gap case — make the lack of alignment explicit and minimal.
                          // No crosswalk visualization here (that lives in the
                          // partnership opportunity report); just a one-liner.
                          <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.45)", lineHeight: 1.5, margin: 0 }}>
                            No curriculum at {collegeName || "this college"} aligned with this occupation.
                          </p>
                        ) : (
                          <>
                            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                              {visibleGroups.map((group) => (
                                <TopGroupBlock key={group.top_code || "unknown"} group={group} brandColor={brandColor} />
                              ))}
                              {showAllGroups && hiddenGroups.map((group, i) => (
                                <motion.div
                                  key={group.top_code || `hidden-${i}`}
                                  initial={{ opacity: 0, y: -4 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{ duration: 0.18, delay: Math.min(i * 0.04, 0.2) }}
                                >
                                  <TopGroupBlock group={group} brandColor={brandColor} />
                                </motion.div>
                              ))}
                            </div>

                            {isCapped && (
                              <button
                                onClick={() => setShowAllGroups(true)}
                                style={{
                                  fontFamily: FONT, fontSize: "11px", fontWeight: 500,
                                  color: brandColor, opacity: 0.65,
                                  background: "transparent", border: "none",
                                  padding: "10px 8px 0 0",
                                  cursor: "pointer", textAlign: "left",
                                  transition: "opacity 0.15s",
                                }}
                                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; }}
                                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.65"; }}
                              >
                                Show all {detail.aligned_program_area_count} program areas
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}

                    <DataCitation source="Centers of Excellence for Labor Market Research" />
                  </div>
                );
              })()}

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

export function TopGroupBlock({ group, brandColor }: {
  group: {
    top_code: string;
    top_title: string;
    courses: Array<{ code: string; name: string }>;
  };
  brandColor: string;
}) {
  const [showAllCourses, setShowAllCourses] = useState(false);
  const topDisplay = group.top_code && /^\d{6}$/.test(group.top_code)
    ? `${group.top_code.slice(0, 4)}.${group.top_code.slice(4, 6)}`
    : group.top_code;

  const visible = group.courses.slice(0, COURSE_CAP);
  const hidden = group.courses.slice(COURSE_CAP);
  const isCapped = !showAllCourses && hidden.length > 0;

  return (
    <div>
      <div style={{
        display: "flex", alignItems: "baseline", gap: "8px",
        padding: "0 0 6px",
      }}>
        <span style={{
          display: "inline-block",
          width: "4px", height: "4px", borderRadius: "50%",
          background: "rgba(255,255,255,0.3)", flexShrink: 0,
          alignSelf: "center",
        }} />
        <span style={{
          fontFamily: MONO, fontSize: "11px", fontWeight: 500,
          color: "rgba(255,255,255,0.5)", flexShrink: 0, whiteSpace: "nowrap",
          letterSpacing: "0.02em",
        }}>
          TOP {topDisplay || "—"}
        </span>
        {group.top_title && (
          <>
            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)", flexShrink: 0 }}>·</span>
            <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.7)" }}>
              {group.top_title}
            </span>
          </>
        )}
      </div>
      <div style={{
        display: "flex", flexDirection: "column", gap: "2px",
        paddingLeft: "13px",
        borderLeft: "1px solid rgba(255,255,255,0.08)",
        marginLeft: "2px",
      }}>
        {visible.map((c) => (
          <CourseRowEl key={c.code} course={c} />
        ))}
        {showAllCourses && hidden.map((c, i) => (
          <motion.div
            key={c.code}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, delay: Math.min(i * 0.02, 0.2) }}
          >
            <CourseRowEl course={c} />
          </motion.div>
        ))}
        {isCapped && (
          <button
            onClick={() => setShowAllCourses(true)}
            style={{
              fontFamily: FONT, fontSize: "11px", fontWeight: 500,
              color: brandColor, opacity: 0.65,
              background: "transparent", border: "none",
              padding: "6px 8px 0",
              cursor: "pointer", textAlign: "left",
              transition: "opacity 0.15s",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.65"; }}
          >
            Show {hidden.length} more course{hidden.length === 1 ? "" : "s"}
          </button>
        )}
      </div>
    </div>
  );
}

function CourseRowEl({ course }: { course: { code: string; name: string } }) {
  return (
    <div style={{
      display: "flex", alignItems: "baseline", gap: "10px",
      padding: "3px 8px",
      fontSize: "11px", lineHeight: 1.4,
    }}>
      <span style={{
        fontFamily: FONT, fontWeight: 600,
        color: "rgba(255,255,255,0.55)",
        flexShrink: 0, whiteSpace: "nowrap",
      }}>
        {course.code}
      </span>
      <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.7)", flex: 1 }}>
        {course.name}
      </span>
    </div>
  );
}
