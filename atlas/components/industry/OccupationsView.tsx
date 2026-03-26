"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getLaborMarketOverview, getOccupationDetail } from "@/lib/api";
import type { ApiOccupationMatch, ApiLaborMarketOverview, ApiOccupationDetail } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import Badge from "@/components/ui/Badge";
import LoadingDots from "@/components/ui/LoadingDots";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type ViewState = "list" | "detail";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

function formatWage(wage: number | null): string {
  if (!wage) return "—";
  return `$${wage.toLocaleString()}`;
}

function formatEmployment(n: number | null): string {
  if (!n) return "—";
  return `${n.toLocaleString()} jobs`;
}

export default function OccupationsView({ school, onBack }: Props) {
  const [view, setView] = useState<ViewState>("list");
  const [overview, setOverview] = useState<ApiLaborMarketOverview | null>(null);
  const [detail, setDetail] = useState<ApiOccupationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLaborMarketOverview(school.name)
      .then(setOverview)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleOccupationClick = (soc_code: string) => {
    setDetailLoading(true);
    getOccupationDetail(soc_code, school.name)
      .then((d) => {
        setDetail(d);
        setView("detail");
      })
      .catch((e) => setError(e.message))
      .finally(() => setDetailLoading(false));
  };

  const handleDetailBack = () => {
    setView("list");
    setDetail(null);
  };

  return (
    <>
      <LeafHeader school={school} onBack={onBack} parentShape="tetrahedron" />

      <div style={{ display: "flex", justifyContent: "center", paddingTop: "32px", paddingBottom: "16px" }}>
        <img src={school.logoPath} alt={school.name} style={{ height: "100px", width: "auto", objectFit: "contain" }} />
      </div>

      <div style={{ maxWidth: "800px", margin: "0 auto", padding: "32px 40px 80px" }}>
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", paddingTop: "60px" }}>
            <LoadingDots color={school.brandColorLight} />
          </div>
        )}

        {error && (
          <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,100,100,0.8)", textAlign: "center", paddingTop: "40px" }}>
            {error}
          </p>
        )}

        {!loading && !error && overview && view === "list" && (
          <OccupationList
            overview={overview}
            school={school}
            onSelect={handleOccupationClick}
            detailLoading={detailLoading}
          />
        )}

        {view === "detail" && detail && (
          <OccupationDetailView
            detail={detail}
            school={school}
            onBack={handleDetailBack}
          />
        )}
      </div>
    </>
  );
}

/* ── Occupation List ───────────────────────────────────────────────────────── */

function OccupationList({
  overview,
  school,
  onSelect,
  detailLoading,
}: {
  overview: ApiLaborMarketOverview;
  school: SchoolConfig;
  onSelect: (soc: string) => void;
  detailLoading: boolean;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      {overview.regions.map((region) => (
        <div key={region.region}>
          <div style={{ marginBottom: "20px" }}>
            <h1
              style={{
                fontFamily: FONT,
                fontSize: "24px",
                fontWeight: 600,
                color: "#f0eef4",
                letterSpacing: "-0.02em",
                marginBottom: "6px",
              }}
            >
              Occupations
            </h1>
            <p
              style={{
                fontFamily: FONT,
                fontSize: "14px",
                color: "rgba(255,255,255,0.5)",
                lineHeight: 1.6,
              }}
            >
              {region.region} — {region.occupations.length} occupations aligned with {overview.college} curriculum
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            {region.occupations.map((occ, i) => (
              <motion.div
                key={occ.soc_code}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(i * 0.02, 0.5) }}
              >
                <button
                  onClick={() => onSelect(occ.soc_code)}
                  disabled={detailLoading}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    background: "rgba(255,255,255,0.03)",
                    border: "none",
                    borderBottom: "1px solid rgba(255,255,255,0.06)",
                    padding: "16px 20px",
                    cursor: detailLoading ? "wait" : "pointer",
                    transition: "background 0.15s",
                    display: "grid",
                    gridTemplateColumns: "1fr auto",
                    gap: "16px",
                    alignItems: "center",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.06)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontFamily: FONT,
                        fontSize: "14px",
                        fontWeight: 500,
                        color: "#f0eef4",
                        marginBottom: "4px",
                      }}
                    >
                      {occ.title}
                    </div>
                    <div
                      style={{
                        fontFamily: FONT,
                        fontSize: "12px",
                        color: "rgba(255,255,255,0.4)",
                        display: "flex",
                        gap: "16px",
                      }}
                    >
                      <span>{formatWage(occ.annual_wage)}</span>
                      <span>{formatEmployment(occ.employment)}</span>
                    </div>
                  </div>
                  <Badge
                    style={{
                      color: school.brandColorLight,
                      background: `${school.brandColorLight}20`,
                      border: `1px solid ${school.brandColorLight}30`,
                      fontSize: "11px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {occ.matching_skills} skills
                  </Badge>
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Occupation Detail ─────────────────────────────────────────────────────── */

function OccupationDetailView({
  detail,
  school,
  onBack,
}: {
  detail: ApiOccupationDetail;
  school: SchoolConfig;
  onBack: () => void;
}) {
  const aligned = detail.skills.filter((s) => s.developed);
  const gaps = detail.skills.filter((s) => !s.developed);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      style={{ display: "flex", flexDirection: "column", gap: "28px" }}
    >
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "6px",
          fontFamily: FONT,
          fontSize: "13px",
          color: "rgba(255,255,255,0.4)",
          padding: 0,
          transition: "color 0.2s",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)";
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M9 3L5 7l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Back to occupations
      </button>

      {/* Header */}
      <div>
        <h2
          style={{
            fontFamily: FONT,
            fontSize: "22px",
            fontWeight: 600,
            color: "#f0eef4",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
          }}
        >
          {detail.title}
        </h2>
        {detail.description && (
          <p
            style={{
              fontFamily: FONT,
              fontSize: "14px",
              color: "rgba(255,255,255,0.5)",
              lineHeight: 1.6,
              marginBottom: "12px",
            }}
          >
            {detail.description}
          </p>
        )}
        <div
          style={{
            fontFamily: FONT,
            fontSize: "13px",
            color: "rgba(255,255,255,0.4)",
            display: "flex",
            gap: "20px",
          }}
        >
          <span>Annual Wage: <span style={{ color: "#f0eef4" }}>{formatWage(detail.annual_wage)}</span></span>
          {detail.regions.length > 0 && (
            <span>
              Regional Employment:{" "}
              <span style={{ color: "#f0eef4" }}>
                {detail.regions.map((r) => `${r.region}: ${r.employment.toLocaleString()}`).join(" · ")}
              </span>
            </span>
          )}
        </div>
      </div>

      {/* Aligned Skills */}
      {aligned.length > 0 && (
        <div>
          <h3
            style={{
              fontFamily: FONT,
              fontSize: "13px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.3)",
              marginBottom: "14px",
            }}
          >
            Aligned Skills ({aligned.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {aligned.map((skill) => (
              <div
                key={skill.skill}
                style={{
                  background: "rgba(255,255,255,0.04)",
                  borderRadius: "8px",
                  padding: "14px 18px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: skill.courses.length > 0 ? "10px" : 0 }}>
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <circle cx="7" cy="7" r="6" stroke={school.brandColorLight} strokeWidth="1.2" />
                    <path d="M4.5 7l1.75 1.75L9.5 5.5" stroke={school.brandColorLight} strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 500, color: school.brandColorLight }}>
                    {skill.skill}
                  </span>
                </div>
                {skill.courses.length > 0 && (
                  <div style={{ paddingLeft: "24px", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {skill.courses.slice(0, 5).map((c) => (
                      <span
                        key={c.code}
                        style={{
                          fontFamily: FONT,
                          fontSize: "12px",
                          color: "rgba(255,255,255,0.4)",
                        }}
                      >
                        {c.code} — {c.name}
                      </span>
                    ))}
                    {skill.courses.length > 5 && (
                      <span style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.3)" }}>
                        +{skill.courses.length - 5} more courses
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gap Skills */}
      {gaps.length > 0 && (
        <div>
          <h3
            style={{
              fontFamily: FONT,
              fontSize: "13px",
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "rgba(255,255,255,0.3)",
              marginBottom: "14px",
            }}
          >
            Skill Gaps ({gaps.length})
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {gaps.map((skill) => (
              <span
                key={skill.skill}
                style={{
                  fontFamily: FONT,
                  fontSize: "12px",
                  color: "rgba(255,255,255,0.35)",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "100px",
                  padding: "5px 12px",
                }}
              >
                {skill.skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
