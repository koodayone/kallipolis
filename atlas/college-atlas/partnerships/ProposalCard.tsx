"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import type { ApiTargetedProposal } from "@/college-atlas/partnerships/api";
import { getOccupationDetail, type ApiOccupationDetail } from "@/college-atlas/occupations/api";
import { saveProposal, removeProposal, updateProposalStatus, type SavedProposal } from "@/college-atlas/partnerships/savedProposals";
import OccupationRow from "@/college-atlas/occupations/OccupationRow";
import DepartmentRow from "@/college-atlas/courses/DepartmentRow";
import StudentRow from "@/college-atlas/students/StudentRow";
import ColumnHeaders from "@/ui/ColumnHeaders";
import { PREVIEW_MODE } from "@/preview/mode";
import { reportFlag } from "@/preview/reportFlag";

const SAVE_PREVIEW_TOOLTIP =
  "Saving is available to pilot partners — contact us to activate for your college.";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type CardState = "default" | "saved" | "dismissed" | "flagged";

type Props = {
  proposal: ApiTargetedProposal;
  brandColor: string;
  onDismiss: () => void;
  onReject?: () => void;
  onRefine?: () => void;
  collegeId?: string;
  onSaved?: (saved: SavedProposal) => void;
  // Override preview detection for tests or special-case rendering. Defaults
  // to the build-time PREVIEW_MODE flag.
  isPreviewMode?: boolean;
};

function SectionHeader({ children, color }: { children: React.ReactNode; color?: string }) {
  // Section headers are the proposal's primary landmarks. They sit
  // above body prose and well above the column-label register the
  // tables use (10px uppercase brand-pink labels). To keep the
  // hierarchy legible:
  //   - bright white title-cased text (a heading idiom, not a label)
  //   - a brand-colored vertical bar to the left (brand presence
  //     without painting the heading text pink and competing with
  //     the column-label register)
  //   - 15px / weight 600 — clearly larger than column labels (10px)
  //     and body prose (14px), but smaller than the artifact title.
  const accent = color || "currentColor";
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "12px", marginBottom: "14px",
    }}>
      <div style={{
        width: "3px", height: "16px", background: accent, borderRadius: "2px",
        flexShrink: 0,
      }} />
      <h3 style={{
        fontFamily: FONT, fontSize: "15px", fontWeight: 600,
        color: "rgba(255,255,255,0.95)", letterSpacing: "-0.005em",
        margin: 0, lineHeight: 1.2,
      }}>
        {children}
      </h3>
    </div>
  );
}

function SectionDescription({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)",
      lineHeight: 1.65, margin: "0 0 12px 0",
    }}>
      {children}
    </p>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function FlagIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <path d="M2 1v10M2 1h7.5L8 4.5 9.5 8H2" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// Workforce-gap bar visualization. Visual idiom is the partnership-narrative
// example on the marketing site (app/components/PartnershipAnatomyCard.tsx,
// SupplyDemandBridgeBand). We re-implement here rather than import because
// the marketing component is locked to its demo data and per-school brand
// theming threads through the atlas, not the marketing site.
//
// Layout: two equal-length horizontal "lanes" — the Openings lane is
// rendered at full width (the demand reference); the Supply lane fills
// proportionally within the same lane width. The gap callout overlays the
// supply terminus, using the brand color and a soft drop-shadow glow to
// pull the eye to the integrative figure.
//
// Surplus case (gap < 0): the supply bar visually exceeds the demand bar's
// implied capacity. We clamp the supply width to 100% so layout stays
// stable, drop the gap overlay, and still surface the negative gap as a
// neutral text callout — the artifact still answers "what's the gap?"
// honestly without misleading visualization.
function GapVisualization({
  totalDemand,
  totalSupply,
  gap,
  brandColor,
}: {
  totalDemand: number;
  totalSupply: number;
  gap: number;
  brandColor: string;
}) {
  const supplyPct = Math.min(100, (totalSupply / totalDemand) * 100);
  const isSurplus = gap < 0;
  const gapDisplay = `${gap >= 0 ? "+" : ""}${Math.round(gap).toLocaleString()}`;

  return (
    <div style={{ padding: "20px 16px 16px" }}>
      {/* Openings bar — full-width neutral, the demand reference. */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 5 }}>
        <span style={{
          fontFamily: FONT, fontSize: 9, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)",
          width: 70, flexShrink: 0,
        }}>
          Openings
        </span>
        <div style={{
          flex: 1, height: 24, background: "rgba(255,255,255,0.06)",
          borderRadius: 4, position: "relative", overflow: "hidden",
        }}>
          <div style={{
            width: "100%", height: "100%",
            background: "rgba(255,255,255,0.12)", borderRadius: 4,
          }} />
        </div>
        <span style={{
          fontFamily: FONT, fontSize: 13, fontWeight: 700,
          color: "rgba(255,255,255,0.75)", fontVariantNumeric: "tabular-nums",
          minWidth: 56, textAlign: "right", flexShrink: 0,
        }}>
          {totalDemand.toLocaleString()}
        </span>
      </div>

      {/* Supply bar — proportional, brand-tinted, with soft glow. */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 5 }}>
        <span style={{
          fontFamily: FONT, fontSize: 9, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.1em", color: `${brandColor}90`,
          width: 70, flexShrink: 0,
        }}>
          Supply
        </span>
        <div style={{
          flex: 1, height: 24, background: "rgba(255,255,255,0.06)",
          borderRadius: 4, position: "relative", overflow: "hidden",
        }}>
          <div style={{
            width: `${supplyPct}%`, height: "100%",
            background: brandColor,
            borderRadius: supplyPct >= 100 ? 4 : "4px 0 0 4px",
            boxShadow: `0 0 12px ${brandColor}30`,
            transition: "width 0.4s ease-out",
          }} />
        </div>
        <span style={{
          fontFamily: FONT, fontSize: 13, fontWeight: 700,
          color: brandColor, fontVariantNumeric: "tabular-nums",
          minWidth: 56, textAlign: "right", flexShrink: 0,
        }}>
          {Math.round(totalSupply).toLocaleString()}
        </span>
      </div>

      {/* Gap callout — overlays the supply terminus when there is a deficit;
          falls back to a neutral text row when supply meets or exceeds demand
          (the visualization is misleading there; honest text is better). */}
      {!isSurplus && supplyPct < 100 && (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ width: 70, flexShrink: 0 }} />
          <div style={{ flex: 1, position: "relative" }}>
            <div style={{
              position: "absolute",
              left: `${supplyPct}%`,
              right: 0,
              top: 0,
              display: "flex", flexDirection: "column", alignItems: "center",
            }}>
              <div style={{ width: "100%", height: 2, background: `${brandColor}40`, borderRadius: 1 }} />
              <div style={{ marginTop: 4, textAlign: "center" }}>
                <span style={{
                  fontFamily: FONT, fontSize: 9, fontWeight: 600, textTransform: "uppercase",
                  letterSpacing: "0.1em", color: `${brandColor}cc`,
                  display: "block", marginBottom: 1,
                }}>
                  Workforce Gap
                </span>
                <span style={{
                  fontFamily: FONT, fontSize: 20, fontWeight: 700, color: brandColor,
                  filter: `drop-shadow(0 0 10px ${brandColor}50)`,
                  lineHeight: 1, fontVariantNumeric: "tabular-nums",
                }}>
                  {gapDisplay}
                </span>
              </div>
            </div>
          </div>
          <span style={{ minWidth: 56, flexShrink: 0 }} />
        </div>
      )}

      {(isSurplus || supplyPct >= 100) && (
        <div style={{
          marginTop: 14, paddingTop: 10,
          borderTop: "1px solid rgba(255,255,255,0.06)",
          fontFamily: FONT, fontSize: 12,
          color: "rgba(255,255,255,0.55)",
          textAlign: "center", fontVariantNumeric: "tabular-nums",
        }}>
          Workforce gap: <span style={{ fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>{gapDisplay}</span>
          {isSurplus && (
            <span style={{ marginLeft: 8, color: "rgba(255,255,255,0.4)", fontStyle: "italic" }}>
              (supply exceeds demand)
            </span>
          )}
        </div>
      )}

      {/* Bottom spacer keeps the gap callout from clipping when it sits at
          the visual baseline. Mirrors the docs-page band's tail spacing. */}
      <div style={{ height: 24 }} />
    </div>
  );
}

export default function ProposalCard({ proposal, brandColor, onDismiss, onReject, onRefine, collegeId, onSaved, isPreviewMode = PREVIEW_MODE }: Props) {
  const [state, setState] = useState<CardState>("default");
  const [savedId, setSavedId] = useState<string | null>(null);

  // Occupation detail loading for expand
  const [occDetails, setOccDetails] = useState<Record<string, ApiOccupationDetail>>({});
  const [loadingOccs, setLoadingOccs] = useState<Set<string>>(new Set());

  const handleOccExpand = useCallback(async (socCode: string) => {
    if (occDetails[socCode] || !collegeId || !socCode) return;
    setLoadingOccs(prev => new Set(prev).add(socCode));
    try {
      const detail = await getOccupationDetail(socCode, collegeId);
      setOccDetails(prev => ({ ...prev, [socCode]: detail }));
    } catch {}
    finally { setLoadingOccs(prev => { const next = new Set(prev); next.delete(socCode); return next; }); }
  }, [occDetails, collegeId]);



  if (state === "dismissed") return null;

  const isSaved = state === "saved";
  const isFlagged = state === "flagged";
  const swp = proposal.swp_evidence;

  return (
    <motion.div layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{
        padding: "28px", background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", position: "relative",
      }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h3 style={{ fontFamily: FONT, fontSize: "17px", fontWeight: 600, color: "rgba(255,255,255,0.9)", letterSpacing: "-0.01em", lineHeight: 1.3, margin: 0 }}>
            {proposal.employer}
          </h3>
          {proposal.sector && (
            <span style={{
              flexShrink: 0, marginLeft: "16px", padding: "4px 12px", borderRadius: "100px",
              fontFamily: FONT, fontSize: "11px", fontWeight: 500, letterSpacing: "0.02em",
              background: "rgba(255,255,255,0.04)", color: "rgba(255,255,255,0.55)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}>
              {proposal.sector}
            </span>
          )}
        </div>

        {/* ── Executive Summary ── */}
        <div style={{ marginBottom: "36px" }}>
          <SectionHeader color={brandColor}>Executive Summary</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.75)", lineHeight: 1.65, margin: 0 }}>
            {proposal.executive_summary}
          </p>
        </div>

        {/* ── Occupational Demand ── */}
        <div style={{ marginBottom: "36px" }}>
          <SectionHeader color={brandColor}>Occupational Demand</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
            {proposal.occupational_demand}
          </p>
          <div style={{ marginTop: "12px" }}>
            <ColumnHeaders
              columns={[
                { label: "Occupation", width: "1fr" },
                { label: "Wage", width: "100px", align: "right" },
                { label: "Openings", width: "80px", align: "right" },
                { label: "Growth", width: "110px", align: "right" },
              ]}
              gridTemplateColumns="24px 1fr 100px 80px 110px"
              brandColor={brandColor}
            />
            {proposal.opportunity_evidence.map((occ, i) => (
              <OccupationRow
                key={occ.title}
                occ={occ}
                index={i}
                brandColor={brandColor}
                detail={occ.soc_code ? occDetails[occ.soc_code] ?? null : null}
                isLoading={occ.soc_code ? loadingOccs.has(occ.soc_code) : false}
                onExpand={occ.soc_code ? () => handleOccExpand(occ.soc_code!) : undefined}
                filterSkills={proposal.core_skills}
                regionNames={proposal.regions}
                collegeName={collegeId}
              />
            ))}
          </div>
        </div>

        {/* ── Curriculum Alignment ── */}
        <div style={{ marginBottom: "36px" }}>
          <SectionHeader color={brandColor}>Curriculum Alignment</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.curriculum_alignment}
          </p>
          <div style={{ marginTop: "12px" }}>
            <ColumnHeaders
              columns={[
                { label: "Department", width: "1fr" },
                { label: "Courses", width: "auto", align: "right" },
              ]}
              gridTemplateColumns="24px 1fr auto"
              brandColor={brandColor}
            />
            {proposal.curriculum_evidence.map((dept, i) => (
              <DepartmentRow
                key={dept.department}
                department={dept.department}
                courseCount={dept.courses.length}
                index={i}
                brandColor={brandColor}
                schoolName={collegeId}
                courses={dept.courses.map(c => ({
                  code: c.code, name: c.name, description: c.description,
                  learningOutcomes: c.learning_outcomes, skillMappings: c.skills,
                  topCode: c.top_code ?? null,
                }))}
              />
            ))}
          </div>
        </div>

        {/* ── Student Impact ── */}
        <div style={{ marginBottom: "36px" }}>
          <SectionHeader color={brandColor}>Student Impact</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
            {proposal.student_impact}
          </p>
          {/* Stats bar */}
          <div style={{
            marginTop: "12px",
            background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.05)",
          }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", padding: "16px 0" }}>
              <span style={{ fontFamily: FONT, fontSize: "20px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
                {(proposal.student_evidence.total_in_aligned_departments ?? proposal.student_evidence.total_in_program).toLocaleString()}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
                Students in Aligned Programs
              </span>
            </div>
          </div>
          {/* Top compatible students */}
          {proposal.student_evidence.top_students.length > 0 && (
            <div style={{ marginTop: "12px" }}>
              <ColumnHeaders
                columns={[
                  { label: "Student", width: "110px" },
                  { label: "Primary Focus", width: "1fr" },
                  { label: "Courses", width: "90px" },
                  { label: "GPA", width: "60px" },
                ]}
                gridTemplateColumns="24px 110px 1fr 90px 60px"
                brandColor={brandColor}
              />
              {proposal.student_evidence.top_students.map((s, i) => (
                <StudentRow
                  key={s.uuid}
                  student={{
                    uuid: s.uuid,
                    displayNumber: s.display_number,
                    primaryFocus: s.primary_focus,
                    coursesCompleted: s.courses_completed,
                    gpa: s.gpa,
                    matchingSkills: s.matching_skills,
                  }}
                  index={i}
                  brandColor={brandColor}
                  detail={{
                    enrollments: (s.enrollments || []).map(e => ({
                      courseCode: e.code, courseName: e.name,
                      grade: e.grade, term: e.term,
                      department: "", status: "",
                    })),
                    skills: s.relevant_skills || [],
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Strong Workforce Evidence (tabular) ── */}
        {swp && (swp.occupations.length > 0 || swp.supply_estimates.length > 0) && (
          <div style={{ marginBottom: "36px" }}>
            <SectionHeader color={brandColor}>Strong Workforce Evidence</SectionHeader>
            {(() => {
              // Templated thesis prose. Every value here is a structured
              // field — no LLM call is needed to compose this. The
              // sentence triplet (demand fact → supply fact → gap as
              // partnership opportunity) generalizes across every
              // (employer, college, SOC) combination.
              const occ = swp.occupations[0];
              const regionName = swp.sources?.coe_region_display || swp.coe_region;
              const hasFullData = (
                occ != null &&
                occ.annual_openings != null &&
                swp.total_supply != null &&
                swp.gap > 0
              );
              if (hasFullData && occ) {
                const openings = occ.annual_openings!.toLocaleString();
                const supply = swp.total_supply.toLocaleString();
                const gap = Math.round(swp.gap).toLocaleString();
                return (
                  <SectionDescription>
                    According to the Centers of Excellence, the SOC {occ.soc_code} occupation demands {openings} annual openings in the {regionName} region.
                    On the supply side, {collegeId ?? "the college"} projects {supply} annual program completions for all related TOP codes.
                    This presents a partnership opportunity with {proposal.employer} that addresses a workforce gap of {gap} for {occ.title}.
                  </SectionDescription>
                );
              }
              return (
                <SectionDescription>
                  Regional supply-demand foundation any funding justification requires.
                  {swp.coe_region ? ` Scoped to the ${swp.coe_region} COE region.` : ""}
                </SectionDescription>
              );
            })()}

            {/* Demand sub-table — SWP tables don't have expandable rows, so
                no chevron column. Headers are inlined here (rather than via
                ColumnHeaders) so the grid has no leading empty slot and the
                section captions, column labels, and row data all share the
                same 16px left edge. */}
            {swp.occupations.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <span style={{
                  fontFamily: FONT, fontSize: "12px", fontWeight: 600,
                  color: "rgba(255,255,255,0.7)",
                  display: "block", marginBottom: "10px",
                }}>
                  Demand: regional annual openings by SOC
                </span>
                {(() => {
                  const grid = "90px 1fr 100px 130px";
                  const rowPadding = "12px 20px";
                  return (
                    <>
                      <div style={{
                        display: "grid", gridTemplateColumns: grid,
                        gap: "10px", padding: rowPadding, alignItems: "center",
                      }}>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>SOC</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>Occupation</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, textAlign: "right" }}>Wage</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, textAlign: "right" }}>Annual openings</span>
                      </div>
                      {swp.occupations.map((occ, i) => (
                        <div key={`${occ.soc_code ?? occ.title}-${i}`} style={{
                          display: "grid", gridTemplateColumns: grid,
                          gap: "10px", padding: rowPadding, alignItems: "center",
                          background: "rgba(255,255,255,0.035)",
                          borderRadius: "4px",
                          marginBottom: i < swp.occupations.length - 1 ? "2px" : "0",
                          fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)",
                        }}>
                          <span style={{ fontVariantNumeric: "tabular-nums", color: "rgba(255,255,255,0.5)" }}>
                            {occ.soc_code ?? "—"}
                          </span>
                          <span>{occ.title}</span>
                          <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                            {occ.annual_wage != null ? `$${occ.annual_wage.toLocaleString()}` : "—"}
                          </span>
                          <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                            {occ.annual_openings != null ? occ.annual_openings.toLocaleString() : "—"}
                          </span>
                        </div>
                      ))}
                    </>
                  );
                })()}
              </div>
            )}

            {/* Supply sub-table */}
            {swp.supply_estimates.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <span style={{
                  fontFamily: FONT, fontSize: "12px", fontWeight: 600,
                  color: "rgba(255,255,255,0.7)",
                  display: "block", marginBottom: "10px",
                }}>
                  Supply: projected annual program completions by TOP
                </span>
                {(() => {
                  const grid = "80px 1fr 220px 110px";
                  const rowPadding = "12px 20px";
                  return (
                    <>
                      <div style={{
                        display: "grid", gridTemplateColumns: grid,
                        gap: "10px", padding: rowPadding, alignItems: "center",
                      }}>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>TOP</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>Program</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6 }}>Award</span>
                        <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: brandColor, opacity: 0.6, textAlign: "right" }}>Annual supply</span>
                      </div>
                      {swp.supply_estimates.map((s, i) => (
                        <div key={`${s.top_code}-${s.award_level}-${i}`} style={{
                          display: "grid", gridTemplateColumns: grid,
                          gap: "10px", padding: rowPadding, alignItems: "center",
                          background: "rgba(255,255,255,0.035)",
                          borderRadius: "4px",
                          marginBottom: i < swp.supply_estimates.length - 1 ? "2px" : "0",
                          fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)",
                        }}>
                          <span style={{ fontVariantNumeric: "tabular-nums", color: "rgba(255,255,255,0.5)" }}>{s.top_code}</span>
                          <span>{s.top_title}</span>
                          <span style={{ color: "rgba(255,255,255,0.55)" }}>{s.award_level}</span>
                          <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                            {s.annual_projected_supply.toFixed(1)}
                          </span>
                        </div>
                      ))}
                    </>
                  );
                })()}
              </div>
            )}

            {/* Workforce-gap visualization — mirrors the partnership-narrative
                example on the docs site. Two horizontal bars (Openings and
                Supply) with the gap visualized as a brand-tinted overlay
                anchored at the supply-bar terminus, captioned "Workforce
                Gap" with the integer gap value. The visualization only
                renders when total_demand > 0; otherwise the data is too
                degenerate to bar-chart honestly. */}
            {swp.total_demand > 0 && (
              <GapVisualization
                totalDemand={swp.total_demand}
                totalSupply={swp.total_supply}
                gap={swp.gap}
                brandColor={brandColor}
              />
            )}

            {/* Institutional source caption — placed at the bottom of the
                section so the data reads first. The reader should be able to
                verify any categorical claim against one of these publications
                without trusting Kallipolis itself. */}
            {swp.sources && (
              <div style={{
                fontFamily: FONT, fontSize: "10px", fontStyle: "italic",
                color: "rgba(255,255,255,0.32)", lineHeight: 1.5,
                marginTop: "16px", paddingRight: "24px",
              }}>
                Sources: {swp.sources.coe_demand_publication}; {swp.sources.coe_supply_publication}; {swp.sources.top_cip_crosswalk_source}; {swp.sources.cip_soc_crosswalk_source}.
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "16px" }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => {
                if (isPreviewMode) return;
                if (isSaved) {
                  if (collegeId && savedId) removeProposal(collegeId, savedId);
                  setSavedId(null);
                  setState("default");
                } else {
                  if (collegeId) {
                    const saved = saveProposal(collegeId, proposal, "saved");
                    setSavedId(saved.id);
                    onSaved?.(saved);
                  }
                  setState("saved");
                }
              }}
              disabled={isPreviewMode}
              title={isPreviewMode ? SAVE_PREVIEW_TOOLTIP : undefined}
              style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 600,
                cursor: isPreviewMode ? "not-allowed" : "pointer", border: "none",
                opacity: isPreviewMode ? 0.45 : 1,
                background: isSaved ? "rgba(74,222,128,0.15)" : `${brandColor}20`,
                color: isSaved ? "rgba(74,222,128,0.9)" : brandColor,
              }}
            >
              <CheckIcon />
              {isSaved ? "Saved" : "Save"}
            </button>
            <button
              onClick={() => { onDismiss(); setState("dismissed"); }}
              style={{
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)",
                background: "transparent", color: "rgba(255,255,255,0.5)",
              }}
            >
              Dismiss
            </button>
            <button
              onClick={() => {
                if (isPreviewMode) {
                  if (isFlagged) {
                    setState("default");
                  } else {
                    void reportFlag({
                      collegeId: collegeId ?? "",
                      artifactKind: "partnership",
                      artifactId: proposal.employer,
                      snapshot: proposal,
                    });
                    setState("flagged");
                  }
                  return;
                }
                if (isFlagged) {
                  if (collegeId && savedId) updateProposalStatus(collegeId, savedId, "saved");
                  setState("default");
                } else {
                  if (collegeId) {
                    if (savedId) {
                      updateProposalStatus(collegeId, savedId, "flagged");
                    } else {
                      const saved = saveProposal(collegeId, proposal, "flagged");
                      setSavedId(saved.id);
                    }
                  }
                  setState("flagged");
                }
              }}
              style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                cursor: "pointer",
                border: `1px solid ${isFlagged ? "rgba(251,191,36,0.4)" : "rgba(255,255,255,0.12)"}`,
                background: isFlagged ? "rgba(251,191,36,0.1)" : "transparent",
                color: isFlagged ? "rgba(251,191,36,0.9)" : "rgba(255,255,255,0.5)",
              }}
            >
              <FlagIcon />
              Flag
            </button>
          </div>

          {onReject && (
            <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
              <button
                onClick={onReject}
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: "pointer", border: "1px solid rgba(248,113,113,0.3)",
                  background: "rgba(248,113,113,0.06)", color: "rgba(248,113,113,0.8)",
                }}
              >
                Reject &amp; Revise
              </button>
              <button
                onClick={onRefine}
                disabled={!onRefine}
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: onRefine ? "pointer" : "default",
                  border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                Refine
              </button>
              <button
                disabled
                title="Coming soon — Google Docs export via MCP"
                style={{
                  padding: "6px 14px", borderRadius: "6px", fontFamily: FONT, fontSize: "12px", fontWeight: 500,
                  cursor: "default", border: "1px solid rgba(255,255,255,0.08)", background: "transparent",
                  color: "rgba(255,255,255,0.2)",
                }}
              >
                Export to Docs
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
