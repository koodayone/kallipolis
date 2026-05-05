"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useParams } from "next/navigation";
import { SchoolConfig } from "@/config/schoolConfig";
import { getPartnershipSectors } from "@/college-atlas/partnerships/api";
import type {
  ApiSectorEntry,
  ApiSectorIndex,
  ApiOpportunityRow,
} from "@/college-atlas/partnerships/api";
import AtlasHeader from "@/ui/AtlasHeader";
import KallipolisBrand from "@/ui/KallipolisBrand";
import FormHeader from "@/ui/FormHeader";
import RisingSun from "@/ui/RisingSun";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

type Props = { school: SchoolConfig; onBack: () => void };

export default function PartnershipsView({ school, onBack }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const params = useParams<{ collegeId: string }>();
  const collegeId = params?.collegeId ?? "";
  const [index, setIndex] = useState<ApiSectorIndex | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSectors, setExpandedSectors] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState("");

  useEffect(() => {
    getPartnershipSectors(school.name)
      .then((data) => setIndex(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [school.name]);

  const handleSectorToggle = useCallback((sector: string) => {
    setExpandedSectors((prev) => {
      const next = new Set(prev);
      if (next.has(sector)) next.delete(sector);
      else next.add(sector);
      return next;
    });
  }, []);

  const opportunityHref = useCallback((socCode: string) => {
    return `/${collegeId}/partnerships/opportunity?soc=${encodeURIComponent(socCode)}`;
  }, [collegeId]);

  // Filter sectors and occupations by the query (case-insensitive title
  // contains). Sectors with zero matching occupations drop out. When a
  // query is active, sectors with matches are auto-expanded so the user
  // sees every match without having to click each accordion.
  const trimmedQuery = query.trim().toLowerCase();
  const isSearching = trimmedQuery.length > 0;

  const filteredSectors = useMemo(() => {
    if (!index) return [];
    if (!isSearching) return index.sectors;
    const result: ApiSectorEntry[] = [];
    for (const s of index.sectors) {
      const matches = s.occupations.filter((o) =>
        o.title.toLowerCase().includes(trimmedQuery) ||
        o.soc_code.toLowerCase().includes(trimmedQuery)
      );
      if (matches.length > 0) {
        result.push({ ...s, occupations: matches });
      }
    }
    return result;
  }, [index, isSearching, trimmedQuery]);

  const totalOccupations = useMemo(() => {
    // Distinct SOCs across the (possibly filtered) sector set.
    const all = new Set<string>();
    for (const s of filteredSectors) {
      for (const o of s.occupations) all.add(o.soc_code);
    }
    return all.size;
  }, [filteredSectors]);

  const hasPriority = useMemo(() => {
    return filteredSectors.some((s) => s.is_priority);
  }, [filteredSectors]);

  // Compute the effective expanded set: while searching, every matching
  // sector is treated as open; otherwise the user's manual toggle state
  // is authoritative.
  const effectiveExpandedSectors = useMemo(() => {
    if (!isSearching) return expandedSectors;
    return new Set(filteredSectors.map((s) => s.sector));
  }, [isSearching, expandedSectors, filteredSectors]);

  return (
    <div ref={rootRef}>
      <AtlasHeader
        school={school}
        onBack={onBack}
        title={school.name}
        rightSlot={<KallipolisBrand />}
      />

      <div style={{ maxWidth: "880px", margin: "0 auto", padding: "32px 40px 80px" }}>
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "80px" }}>
            <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
          </div>
        )}

        {!loading && error && (
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "#f87171", padding: "40px 0", textAlign: "center" }}>
            {error}
          </p>
        )}

        {!loading && !error && index && (
          <>
            <div style={{ marginBottom: "24px" }}>
              <FormHeader formName="Partnerships" />
            </div>

            {/* Occupation search — title or SOC-code substring filter.
                Layout matches the QueryShell pattern: magnifying glass
                on the left, full-width text input, soft-shadowed pill. */}
            <div
              style={{
                display: "flex", alignItems: "center", gap: "10px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "10px",
                padding: "12px 16px",
                marginBottom: "32px",
                transition: "border-color 0.15s, background 0.15s",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ color: "rgba(255,255,255,0.4)", flexShrink: 0 }}>
                <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.5" />
                <path d="M10.5 10.5L14.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search occupations..."
                style={{
                  flex: 1,
                  fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.85)",
                  background: "transparent",
                  border: "none",
                  outline: "none",
                }}
              />
            </div>

            <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.45)", marginBottom: "16px" }}>
              {isSearching
                ? `${totalOccupations} ${totalOccupations === 1 ? "occupation matches" : "occupations match"} "${query.trim()}"`
                : `${totalOccupations} occupations with partnership opportunities`}
            </p>

            {/* Header row matching EmployersView column language */}
            <div style={{
              display: "grid", gridTemplateColumns: "24px 1fr auto",
              padding: "12px 16px", gap: "10px", alignItems: "center",
            }}>
              <span />
              <span style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                <span style={{
                  fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                  letterSpacing: "0.1em", textTransform: "uppercase",
                  color: school.brandColorLight, opacity: 0.6,
                }}>
                  Sector
                </span>
                {hasPriority && (
                  <span style={{ display: "inline-flex", alignItems: "baseline", gap: "5px" }}>
                    <span style={{
                      width: "5px", height: "5px", borderRadius: "50%",
                      background: school.brandColorLight, opacity: 0.7,
                      position: "relative", top: "-1px",
                    }} />
                    <span style={{
                      fontFamily: FONT, fontSize: "10px", fontWeight: 500,
                      letterSpacing: "0.1em", textTransform: "uppercase",
                      color: school.brandColorLight, opacity: 0.4,
                    }}>
                      Regional priority
                    </span>
                  </span>
                )}
              </span>
              <span style={{
                fontFamily: FONT, fontSize: "10px", fontWeight: 600,
                letterSpacing: "0.1em", textTransform: "uppercase",
                color: school.brandColorLight, opacity: 0.6,
                textAlign: "right",
              }}>
                Occupations
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {filteredSectors.length === 0 && isSearching && (
                <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
                  No occupations match that search. Try a different query.
                </p>
              )}
              {filteredSectors.map((sector, i) => (
                <SectorGroup
                  key={sector.sector}
                  entry={sector}
                  index={i}
                  isOpen={effectiveExpandedSectors.has(sector.sector)}
                  brandColor={school.brandColorLight}
                  onToggle={() => handleSectorToggle(sector.sector)}
                  hrefForSoc={opportunityHref}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Sector Group ─────────────────────────────────────────────────────── */

function SectorGroup({
  entry, index, isOpen, brandColor, onToggle, hrefForSoc,
}: {
  entry: ApiSectorEntry;
  index: number;
  isOpen: boolean;
  brandColor: string;
  onToggle: () => void;
  hrefForSoc: (socCode: string) => string;
}) {
  const hasMounted = useRef(false);
  useEffect(() => { hasMounted.current = true; }, []);
  const count = entry.occupations.length;
  return (
    <div>
      <motion.button
        initial={hasMounted.current ? false : { opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, delay: hasMounted.current ? 0 : Math.min(index * 0.01, 0.2) }}
        onClick={onToggle}
        style={{
          width: "100%", textAlign: "left",
          display: "grid", gridTemplateColumns: "24px 1fr auto",
          padding: "18px 16px", gap: "12px", alignItems: "center",
          background: isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.035)",
          border: "none", borderBottom: `1px solid ${isOpen ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.05)"}`,
          borderTop: isOpen ? `2px solid ${brandColor}80` : "2px solid transparent",
          cursor: "pointer", transition: "background 0.15s, border-color 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.055)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.035)"; }}
      >
        <svg width="14" height="14" viewBox="0 0 12 12" fill="none"
          style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
          <span style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            textTransform: "uppercase", color: "rgba(255,255,255,0.98)",
            lineHeight: 1.4,
          }}>
            {entry.sector}
          </span>
          {entry.is_priority && (
            <span
              title="Regional priority sector"
              style={{
                display: "inline-block", width: "7px", height: "7px",
                borderRadius: "50%", background: brandColor, flexShrink: 0,
                boxShadow: `0 0 6px ${brandColor}80`,
              }}
            />
          )}
        </span>
        <span style={{ fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.45)" }}>
          {count} {count === 1 ? "occupation" : "occupations"}
        </span>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden", background: "rgba(255,255,255,0.02)" }}
          >
            <div>
              {entry.occupations.map((occ) => (
                <OccupationOpportunityRow
                  key={occ.soc_code}
                  occ={occ}
                  brandColor={brandColor}
                  hrefForSoc={hrefForSoc}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ── Occupation Opportunity Row ───────────────────────────────────────── */

function OccupationOpportunityRow({
  occ, brandColor, hrefForSoc,
}: {
  occ: ApiOpportunityRow;
  brandColor: string;
  hrefForSoc: (socCode: string) => string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  // Per-row triage signal: regional demand minus this college's TOP-
  // program supply. Negative values indicate the college's pipeline
  // already outpaces demand for the SOC, so the row dims to recede in
  // scan order without disappearing.
  const gap = occ.gap;
  const hasGap = gap !== null && gap !== undefined;
  const isOversupplied = hasGap && gap < 0;
  const gapColor = !hasGap
    ? "rgba(255,255,255,0.4)"
    : gap >= 0 ? "#4ade80" : "#f87171";
  return (
    <div style={{ opacity: isOversupplied ? 0.55 : 1 }}>
      <button
        onClick={() => setIsOpen((o) => !o)}
        style={{
          width: "100%", textAlign: "left",
          display: "flex", alignItems: "center", gap: "12px",
          padding: "12px 16px 12px 44px",
          background: isOpen ? "rgba(255,255,255,0.04)" : "transparent",
          border: "none",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          cursor: "pointer", transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.025)"; }}
        onMouseLeave={(e) => { if (!isOpen) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
      >
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none"
          style={{
            transform: isOpen ? "rotate(90deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            flexShrink: 0,
            marginLeft: "-18px", marginRight: "8px",
          }}>
          <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: "10px", flex: 1, minWidth: 0, flexWrap: "wrap" }}>
          <span style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.82)", lineHeight: 1.45 }}>
            {occ.title}
          </span>
          <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 500, letterSpacing: "0.05em", color: "rgba(255,255,255,0.4)", fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
            SOC {occ.soc_code}
          </span>
        </span>
        {hasGap && (
          <span
            title={
              gap >= 0
                ? "Regional demand exceeds this college's projected pipeline by this many positions per year"
                : "This college's projected pipeline exceeds regional demand for this occupation"
            }
            style={{
              fontFamily: MONO, fontSize: "11px", fontWeight: 500,
              letterSpacing: "0.04em",
              color: gapColor,
              fontVariantNumeric: "tabular-nums",
              whiteSpace: "nowrap",
              flexShrink: 0,
              marginLeft: "8px",
            }}
          >
            {gap >= 0 ? "+" : ""}{gap.toLocaleString()} / yr
          </span>
        )}
        <a
          href={hrefForSoc(occ.soc_code)}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          style={{
            fontFamily: FONT, fontSize: "11px", fontWeight: 600,
            letterSpacing: "0.07em", textTransform: "uppercase",
            color: brandColor,
            background: "transparent",
            border: `1px solid ${brandColor}55`,
            borderRadius: "100px",
            padding: "6px 14px",
            cursor: "pointer",
            whiteSpace: "nowrap",
            textDecoration: "none",
            transition: "background 0.15s, border-color 0.15s",
            flexShrink: 0,
            marginLeft: "8px",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = `${brandColor}15`;
            (e.currentTarget as HTMLElement).style.borderColor = brandColor;
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "transparent";
            (e.currentTarget as HTMLElement).style.borderColor = `${brandColor}55`;
          }}
        >
          Draft Partnerships
        </a>
      </button>

      {isOpen && (
        <div style={{
          background: "rgba(255,255,255,0.02)",
          padding: "14px 16px 16px 56px",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          // Single 3-column grid spanning both rows so each column's
          // left edge stays anchored regardless of value width. Row 1
          // frames the demand (what the regional labor market needs);
          // row 2 answers it with the partnership impact at this college
          // (what the institutional pipeline has to offer).
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          rowGap: "10px",
          columnGap: "16px",
          alignItems: "center",
        }}>
          {/* Row 1 — occupational demand (COE projections) */}
          <LabeledStat
            label="annual salary"
            value={occ.annual_wage != null ? `$${occ.annual_wage.toLocaleString()}` : "—"}
          >
            <DollarIcon />
          </LabeledStat>
          <LabeledStat
            label={`annual ${occ.annual_openings === 1 ? "opening" : "openings"}`}
            value={occ.annual_openings != null ? occ.annual_openings.toLocaleString() : "—"}
          >
            <ChairIcon />
          </LabeledStat>
          <LabeledStat
            label="5yr growth"
            value={
              occ.growth_rate != null
                ? `${occ.growth_rate >= 0 ? "+" : ""}${(occ.growth_rate * 100).toFixed(1)}%`
                : "—"
            }
            valueColor={
              occ.growth_rate != null
                ? (occ.growth_rate >= 0 ? "#4ade80" : "#f87171")
                : undefined
            }
          >
            <TrendIcon up={(occ.growth_rate ?? 0) >= 0} />
          </LabeledStat>

          {/* Row 2 — partnership impact at this college */}
          <LabeledStat label={`${occ.student_count === 1 ? "student" : "students"} impacted`} value={occ.student_count.toLocaleString()}>
            <PersonIcon />
          </LabeledStat>
          <LabeledStat label={`aligned ${occ.course_count === 1 ? "course" : "courses"}`} value={occ.course_count.toLocaleString()}>
            <BookIcon />
          </LabeledStat>
          <LabeledStat label={`${occ.employer_count === 1 ? "employer" : "employers"} hiring`} value={occ.employer_count.toLocaleString()}>
            <SkyscraperIcon />
          </LabeledStat>
        </div>
      )}
    </div>
  );
}

/* ── Per-row stat primitive (icon + value + label) ────────────────────── */

function LabeledStat({
  children, value, label, valueColor,
}: {
  children: React.ReactNode;
  value: string | number;
  label: string;
  valueColor?: string;
}) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: "8px",
      color: "rgba(255,255,255,0.5)", whiteSpace: "nowrap",
    }}>
      {children}
      <span style={{
        fontFamily: FONT, fontSize: "12px", fontVariantNumeric: "tabular-nums",
        color: valueColor ?? "rgba(255,255,255,0.75)", fontWeight: 500,
      }}>
        {value}
      </span>
      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>
        {label}
      </span>
    </span>
  );
}

function PersonIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M3 13c0-2.5 2.2-4 5-4s5 1.5 5 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function BookIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <path d="M2.5 3h11v10h-11z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      <path d="M2.5 3v10M5 3v10" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

// Generic skyscraper — tapered tower with a spire on top. Same silhouette
// as the platonic form, minus the WTC-specific center crease, so it
// reads as "tall building" without committing to a particular real-world
// tower.
function SkyscraperIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <path d="M8 1 L8 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M4 14 L5.5 3.5 L10.5 3.5 L12 14 Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

// Dollar sign in a circle — annual salary marker.
function DollarIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.2" stroke="currentColor" strokeWidth="1.4" />
      <path d="M10 5.5 Q9 4.5 7.5 4.5 Q5.5 4.5 5.5 6 Q5.5 7.3 7.5 7.5 Q9.7 7.7 10 9.2 Q10 11 8 11 Q6 11 5.5 9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none" />
      <path d="M8 3.5 L8 12.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

// Front-facing chair — annual openings (open seats / positions). The back
// rises above a wider seat with two visible front legs underneath, the
// canonical "chair facing the viewer" silhouette that reads instantly
// as a chair without needing a side-view mental rotation.
function ChairIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      {/* Back — three-sided, open at the bottom (the seat's top edge
          closes the back implicitly) */}
      <path d="M5 8 L5 3 L11 3 L11 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      {/* Seat — wider rectangle below the back */}
      <path d="M3 8 L3 11 L13 11 L13 8 Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
      {/* Front legs */}
      <path d="M4 11 L4 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M12 11 L12 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// Trend arrow — clean diagonal with the arrowhead at the corner. The
// universal "growth/decline" glyph used in stock charts and dashboards.
// Up-and-to-the-right for growth >= 0, mirrored to down-and-to-the-right
// for growth < 0. Used for 5-yr employment growth.
function TrendIcon({ up }: { up: boolean }) {
  if (up) {
    return (
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
        <path
          d="M3 13 L13 3 M8 3 L13 3 L13 8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
    );
  }
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
      <path
        d="M3 3 L13 13 M8 13 L13 13 L13 8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
