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

function SectionDescription({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)",
      lineHeight: 1.5, margin: "0 0 12px 0", fontStyle: "italic",
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

// Small TOP6-prefix → industry-context heuristic. The PCAH TOP6 sector
// map lives server-side; reproducing it client-side would duplicate ~400
// rows. The first two digits of a TOP code encode its broad family
// (09 = engineering/industrial, 12 = health, 30 = business,
// 10 = arts/media, 02 = agriculture, etc.), which is enough to detect
// cross-family alignment for the principle 4 caption.
//
// When the heuristic is uncertain (the rare case where the prefix
// doesn't map cleanly to a sector family), the caption is silent —
// principle 4 is about visible honesty, not aggressive labeling.
const TOP_PREFIX_TO_SECTOR_FAMILY: Record<string, string> = {
  "01": "Agriculture, Water and Environmental Technologies",
  "02": "Agriculture, Water and Environmental Technologies",
  "03": "Energy, Construction and Utilities",
  "04": "Life Sciences",
  "05": "Information and Communication Technologies",
  "06": "Information and Communication Technologies",
  "07": "Information and Communication Technologies",
  "09": "Advanced Manufacturing",
  "10": "Retail, Hospitality, and Tourism",
  "12": "Health",
  "13": "Education",
  "21": "Energy, Construction and Utilities",
  "30": "Business and Entrepreneurship",
  "32": "Public Safety",
};

function topToSectorFamily(top: string | undefined): string | null {
  if (!top || top.length < 2) return null;
  return TOP_PREFIX_TO_SECTOR_FAMILY[top.slice(0, 2)] ?? null;
}

function inferIndustryContext(top: string | undefined): string | null {
  // Some TOPs have well-known industry-context flavors that the broad
  // sector family doesn't capture. AATA = aerospace QC apprenticeship.
  // Returning null when no specific flavor is known so the caption
  // falls back to the sector-family comparison.
  if (top === "095680") return "aerospace quality-control apprenticeship";
  return null;
}

function CrossIndustryCaption({
  proposal, brandColor,
}: {
  proposal: ApiTargetedProposal;
  brandColor: string;
}) {
  const dominantTop = (() => {
    const counts: Record<string, number> = {};
    for (const dept of proposal.curriculum_evidence ?? []) {
      for (const t of dept.via_top ?? []) {
        counts[t] = (counts[t] ?? 0) + (dept.courses?.length ?? 1);
      }
    }
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return entries[0]?.[0];
  })();

  if (!dominantTop) return null;

  const employerSector = (proposal.sector ?? "").trim();
  const dominantFamily = topToSectorFamily(dominantTop);
  if (!employerSector || !dominantFamily) return null;

  // Substring match in either direction = same family. The PCAH sector
  // names include things like "Health" and "Advanced Manufacturing"
  // which substring-match cleanly against employer SWP sector names.
  const lower = employerSector.toLowerCase();
  const dlower = dominantFamily.toLowerCase();
  const sameFamily = lower.includes(dlower) || dlower.includes(lower);
  if (sameFamily) return null;

  // Industry contexts differ. Render the partial-alignment caption.
  const programFlavor = inferIndustryContext(dominantTop);
  const programDescriptor = programFlavor
    ? `${programFlavor} (${dominantFamily})`
    : `${dominantFamily}-rooted program`;

  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: "8px",
      padding: "10px 14px", borderRadius: "6px",
      background: `${brandColor}10`,
      border: `1px solid ${brandColor}30`,
      marginBottom: "20px",
      fontFamily: FONT, fontSize: "12px", lineHeight: 1.5,
      color: "rgba(255,255,255,0.7)",
    }}>
      <span style={{
        flexShrink: 0, fontWeight: 700, letterSpacing: "0.06em",
        textTransform: "uppercase", fontSize: "10px",
        color: brandColor, marginTop: "1px",
      }}>
        Cross-industry pathway
      </span>
      <span>
        The institutional crosswalk routes this employer&apos;s occupation through a {programDescriptor}.
        The methods are transferable across industries; the {employerSector.toLowerCase()} context is
        a partnership-conversation topic, not a turnkey claim.
      </span>
    </div>
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

        {/* Cross-industry caption — visible expression of principle 4
            (name partial alignment honestly when industry contexts differ).
            Renders only when the institutional crosswalk routes the
            employer's selected occupation through a TOP whose
            apparent industry context differs from the employer's SWP
            sector. The reader sees the partial-alignment fact before
            reading the prose — visually unmissable, but small enough
            that it doesn't dominate the artifact. */}
        <CrossIndustryCaption proposal={proposal} brandColor={brandColor} />

        {/* ── Executive Summary ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Executive Summary</SectionHeader>
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.75)", lineHeight: 1.65, margin: 0 }}>
            {proposal.executive_summary}
          </p>
        </div>

        {/* ── Occupational Demand ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Occupational Demand</SectionHeader>
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
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Curriculum Alignment</SectionHeader>
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
                }))}
              />
            ))}
          </div>
        </div>

        {/* ── Student Impact ── */}
        <div style={{ marginBottom: "24px" }}>
          <SectionHeader>Student Impact</SectionHeader>
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
                {proposal.student_evidence.total_in_program.toLocaleString()}
              </span>
              <span style={{ fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
                Students in Aligned Programs
              </span>
            </div>
          </div>
          {/* Top compatible students */}
          {proposal.student_evidence.top_students.length > 0 && (
            <div style={{ marginTop: "12px" }}>
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em",
                textTransform: "uppercase", color: "rgba(255,255,255,0.25)",
                display: "block", marginBottom: "8px", paddingLeft: "16px",
              }}>
                Top 10 Candidates
              </span>
              <ColumnHeaders
                columns={[
                  { label: "Student", width: "110px" },
                  { label: "Primary Focus", width: "1fr" },
                  { label: "Skills", width: "90px" },
                  { label: "GPA", width: "60px" },
                ]}
                gridTemplateColumns="24px 110px 1fr 90px 60px"
                brandColor={brandColor}
              />
              {proposal.student_evidence.top_students.map((s, i) => (
                <StudentRow
                  key={s.uuid}
                  totalCoreSkills={proposal.core_skills.length}
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
          <div style={{ marginBottom: "24px" }}>
            <SectionHeader>Strong Workforce Evidence</SectionHeader>
            <SectionDescription>
              Regional supply-demand foundation any funding justification requires.
              {swp.coe_region ? ` Scoped to the ${swp.coe_region} COE region.` : ""}
            </SectionDescription>
            {/* Institutional source caption — borrows the artifact's authority
                from the named external publications. Per the institutional-
                deference architectural commitment (principle 2), the reader
                should be able to verify any categorical claim against one of
                these publications without trusting Kallipolis itself. The
                caption is visible but not overwhelming — small, italic, low
                opacity. The caption disappears when sources are absent
                (legacy proposals predating C1). */}
            {swp.sources && (
              <div style={{
                fontFamily: FONT, fontSize: "10px", fontStyle: "italic",
                color: "rgba(255,255,255,0.32)", lineHeight: 1.5,
                margin: "-4px 0 12px", paddingLeft: "16px", paddingRight: "8px",
              }}>
                Sources: {swp.sources.coe_demand_publication}; {swp.sources.coe_supply_publication}; {swp.sources.top_cip_crosswalk_source}; {swp.sources.cip_soc_crosswalk_source}.
              </div>
            )}

            {/* Demand sub-table — column shape mirrors the partnership-narrative
                example on the docs site: SOC Code, Occupation, Region, Wage,
                Annual Openings. The region is identical per row (the block is
                scoped to one COE region) but reads naturally on each row. */}
            {swp.occupations.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <span style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                  textTransform: "uppercase", color: "rgba(255,255,255,0.35)",
                  display: "block", marginBottom: "8px", paddingLeft: "16px",
                }}>
                  Demand: regional annual openings by SOC
                </span>
                <ColumnHeaders
                  columns={[
                    { label: "SOC", width: "90px" },
                    { label: "Occupation", width: "1fr" },
                    { label: "Region", width: "70px" },
                    { label: "Wage", width: "100px", align: "right" },
                    { label: "Annual openings", width: "130px", align: "right" },
                  ]}
                  gridTemplateColumns="24px 90px 1fr 70px 100px 130px"
                  brandColor={brandColor}
                />
                {swp.occupations.map((occ, i) => (
                  <div key={`${occ.soc_code ?? occ.title}-${i}`} style={{
                    display: "grid",
                    gridTemplateColumns: "24px 90px 1fr 70px 100px 130px",
                    alignItems: "center",
                    padding: "10px 0",
                    borderBottom: i < swp.occupations.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
                    fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)",
                  }}>
                    <span />
                    <span style={{ fontVariantNumeric: "tabular-nums", color: "rgba(255,255,255,0.5)" }}>
                      {occ.soc_code ?? "—"}
                      {/* CIP chip — surfaces the SOC↔CIP institutional link
                          (BLS/NCES crosswalk) inline next to the SOC code.
                          Truncates to first CIP with +N indicator when the
                          SOC maps to multiple CIPs. */}
                      {occ.cip_codes && occ.cip_codes.length > 0 && (
                        <span style={{
                          marginLeft: "6px", fontSize: "9px",
                          padding: "1px 5px", borderRadius: "3px",
                          background: "rgba(255,255,255,0.06)",
                          color: "rgba(255,255,255,0.45)",
                          fontFamily: FONT, fontWeight: 500,
                          fontVariantNumeric: "normal",
                        }}>
                          CIP {occ.cip_codes[0]}{occ.cip_codes.length > 1 ? ` +${occ.cip_codes.length - 1}` : ""}
                        </span>
                      )}
                    </span>
                    <span>{occ.title}</span>
                    <span style={{ color: "rgba(255,255,255,0.55)" }}>{swp.coe_region || "—"}</span>
                    <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {occ.annual_wage != null ? `$${occ.annual_wage.toLocaleString()}` : "—"}
                    </span>
                    <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {occ.annual_openings != null ? occ.annual_openings.toLocaleString() : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Supply sub-table */}
            {swp.supply_estimates.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <span style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.08em",
                  textTransform: "uppercase", color: "rgba(255,255,255,0.35)",
                  display: "block", marginBottom: "8px", paddingLeft: "16px",
                }}>
                  Supply: projected annual program completions by TOP
                </span>
                <ColumnHeaders
                  columns={[
                    { label: "TOP", width: "90px" },
                    { label: "Program", width: "1fr" },
                    { label: "Award", width: "100px" },
                    { label: "Annual supply", width: "110px", align: "right" },
                  ]}
                  gridTemplateColumns="24px 90px 1fr 100px 110px"
                  brandColor={brandColor}
                />
                {swp.supply_estimates.map((s, i) => (
                  <div key={`${s.top_code}-${s.award_level}-${i}`} style={{
                    display: "grid",
                    gridTemplateColumns: "24px 90px 1fr 100px 110px",
                    alignItems: "center",
                    padding: "10px 0",
                    borderBottom: i < swp.supply_estimates.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
                    fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)",
                  }}>
                    <span />
                    <span style={{ fontVariantNumeric: "tabular-nums", color: "rgba(255,255,255,0.5)" }}>{s.top_code}</span>
                    <span>{s.top_title}</span>
                    <span style={{ color: "rgba(255,255,255,0.55)" }}>{s.award_level}</span>
                    <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {s.annual_projected_supply.toFixed(1)}
                    </span>
                  </div>
                ))}
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
