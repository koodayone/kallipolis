"use client";

import { memo, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getCourseOccupations } from "@/college-atlas/courses/api";
import type { ApiCourseOccupations, ApiOccupationLink, ApiCipCode } from "@/college-atlas/courses/api";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, monospace";

// Visible cap on the SOC list. Above this count, the surface shows the
// first CAP rows alphabetically + a "Show all N" affordance that
// reveals the rest in place. Picked to convey enough of the SOC family
// to inform the at-a-glance reading without dominating the surrounding
// course-detail sections (description, learning outcomes, objectives).
const CAP = 8;

type Props = {
  courseCode: string;
  collegeName: string;
  brandColor: string;
  // When the surrounding context is scoped to a specific SOC (e.g. the
  // partnership opportunity report), the per-course Occupational
  // Pathways section is suppressed to avoid surfacing redundant SOC
  // info. The Federal Curriculum Codes section is always shown
  // regardless — CIPs are the federal curriculum identity of the
  // course, invariant of which SOC anchors the report.
  hideOccupationPathways?: boolean;
  // SOC filter for the CIP list. When provided, the server returns
  // only CIPs that bridge from this course's TOP6 to the given SOC,
  // keeping the per-course CIP list consistent with the Curriculum
  // Pathway hero (which is scoped to one SOC). Omit for unfiltered
  // use outside a report context.
  socFilter?: string;
};

/**
 * Renders the institutional Course→Occupation pathway in the expanded
 * course detail. Surfaces the course's TOP6 code with its program-area
 * title, then the SOC-coded occupations the course institutionally
 * prepares students for, sorted alphabetically. Long lists (above
 * `CAP`) start collapsed to a representative sample with a "Show all N"
 * affordance — solves the visual-proportion problem only where it
 * exists, stays invisible the rest of the time.
 *
 * Visual language matches the student competency profile's TOP groups:
 * a small white dot, mono code, and regular title for the TOP header,
 * then a faint white left border anchoring the indented SOC list.
 * Hidden when the course has no PREPARES_FOR edges (typical for
 * non-CTE academic courses outside the institutional crosswalk).
 */
const CourseOccupationsCallout = memo(function CourseOccupationsCallout({
  courseCode, collegeName, brandColor, hideOccupationPathways, socFilter,
}: Props) {
  const [data, setData] = useState<ApiCourseOccupations | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setShowAll(false);
    getCourseOccupations(courseCode, collegeName, socFilter)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [courseCode, collegeName, socFilter]);

  if (loading || !data) return null;
  const cips = data.cips ?? [];
  // hideOccupationPathways suppresses only the Occupational Pathways
  // section; the Federal Curriculum Codes section is independent of
  // the report's anchoring SOC.
  const hasOccupations = data.occupations.length > 0 && !hideOccupationPathways;
  const hasCips = cips.length > 0;
  if (!hasOccupations && !hasCips) return null;

  const topDisplay = data.top_code && /^\d{6}$/.test(data.top_code)
    ? `${data.top_code.slice(0, 4)}.${data.top_code.slice(4, 6)}`
    : data.top_code;

  const visible = data.occupations.slice(0, CAP);
  const hidden = data.occupations.slice(CAP);
  const isCapped = !showAll && hidden.length > 0;

  return (
    <div>
      {hasOccupations && (
        <>
          <span style={{
            fontFamily: FONT, fontSize: "10px", fontWeight: 600,
            letterSpacing: "0.1em", textTransform: "uppercase",
            color: brandColor, opacity: 0.6,
            display: "block", marginBottom: "10px",
          }}>
            Occupational Pathways
          </span>

          {data.top_code && (
            <div style={{
              display: "flex", alignItems: "baseline", gap: "8px",
              padding: "0 0 8px",
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
                TOP {topDisplay}
              </span>
              {data.top_title && (
                <>
                  <span style={{
                    fontFamily: FONT, fontSize: "11px",
                    color: "rgba(255,255,255,0.3)", flexShrink: 0,
                  }}>·</span>
                  <span style={{
                    fontFamily: FONT, fontSize: "11px",
                    color: "rgba(255,255,255,0.7)",
                  }}>
                    {data.top_title}
                  </span>
                </>
              )}
            </div>
          )}

          <div style={{
            display: "flex", flexDirection: "column", gap: "2px",
            paddingLeft: "13px",
            borderLeft: "1px solid rgba(255,255,255,0.08)",
            marginLeft: "2px",
          }}>
            {visible.map((o) => <SocRow key={o.soc_code} occ={o} />)}
            {showAll && hidden.map((o, i) => (
              <motion.div
                key={o.soc_code}
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.18, delay: Math.min(i * 0.02, 0.2) }}
              >
                <SocRow occ={o} />
              </motion.div>
            ))}
          </div>

          {isCapped && (
            <button
              onClick={() => setShowAll(true)}
              style={{
                fontFamily: FONT, fontSize: "11px", fontWeight: 500,
                color: brandColor, opacity: 0.65,
                background: "transparent", border: "none",
                padding: "10px 8px 0 21px",
                cursor: "pointer", textAlign: "left",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.65"; }}
            >
              Show all {data.occupations.length} occupations
            </button>
          )}
        </>
      )}

      {hasCips && (
        <div style={{ marginTop: hasOccupations ? "20px" : 0 }}>
          {/* Federal-taxonomy view — the same course's TOP read through
              the NCES CIP layer. Sibling section to Occupational
              Pathways: same brand-color section header, neutral mono
              code styling matching the SOC rows above. The TOP isn't
              repeated here because it's already named in the section
              above; CIP rows alone read as "this is the federal
              curriculum identity of that TOP". */}
          <span style={{
            fontFamily: FONT, fontSize: "10px", fontWeight: 600,
            letterSpacing: "0.1em", textTransform: "uppercase",
            color: brandColor, opacity: 0.6,
            display: "block", marginBottom: "10px",
          }}>
            Federal Curriculum Codes
          </span>
          <div style={{
            display: "flex", flexDirection: "column", gap: "2px",
            paddingLeft: "13px",
            borderLeft: "1px solid rgba(255,255,255,0.08)",
            marginLeft: "2px",
          }}>
            {cips.map((c) => <CipRow key={c.code} cip={c} />)}
          </div>
        </div>
      )}
    </div>
  );
});

function SocRow({ occ }: { occ: ApiOccupationLink }) {
  return (
    <div style={{
      display: "flex", alignItems: "baseline", gap: "10px",
      padding: "3px 8px",
      fontSize: "11px", lineHeight: 1.4,
    }}>
      <span style={{
        fontFamily: MONO, fontSize: "11px",
        color: "rgba(255,255,255,0.4)",
        flexShrink: 0, whiteSpace: "nowrap",
      }}>
        SOC {occ.soc_code}
      </span>
      <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.7)", flex: 1 }}>
        {occ.title}
      </span>
    </div>
  );
}

function CipRow({ cip }: { cip: ApiCipCode }) {
  return (
    <div style={{
      display: "flex", alignItems: "baseline", gap: "10px",
      padding: "3px 8px",
      fontSize: "11px", lineHeight: 1.4,
    }}>
      <span style={{
        fontFamily: MONO, fontSize: "11px",
        color: "rgba(255,255,255,0.4)",
        flexShrink: 0, whiteSpace: "nowrap",
      }}>
        CIP {cip.code}
      </span>
      <span style={{ fontFamily: FONT, color: "rgba(255,255,255,0.7)", flex: 1 }}>
        {cip.title}
      </span>
    </div>
  );
}

export default CourseOccupationsCallout;
