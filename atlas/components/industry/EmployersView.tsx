"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { SchoolConfig } from "@/lib/schoolConfig";
import { getEmployers, getEmployerDetail } from "@/lib/api";
import type { ApiEmployerMatch, ApiEmployerDetail } from "@/lib/api";
import LeafHeader from "@/components/ui/LeafHeader";
import Badge from "@/components/ui/Badge";
import LoadingDots from "@/components/ui/LoadingDots";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type ViewState = "list" | "detail";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function EmployersView({ school, onBack }: Props) {
  const [view, setView] = useState<ViewState>("list");
  const [employers, setEmployers] = useState<ApiEmployerMatch[]>([]);
  const [detail, setDetail] = useState<ApiEmployerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getEmployers(school.name)
      .then(setEmployers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleEmployerClick = (name: string) => {
    setDetailLoading(true);
    getEmployerDetail(name, school.name)
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
      <LeafHeader school={school} onBack={onBack} parentShape="dodecahedron" />

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

        {!loading && !error && view === "list" && (
          <EmployerList
            employers={employers}
            school={school}
            onSelect={handleEmployerClick}
            detailLoading={detailLoading}
          />
        )}

        {view === "detail" && detail && (
          <EmployerDetailView
            detail={detail}
            school={school}
            onBack={handleDetailBack}
          />
        )}
      </div>
    </>
  );
}

/* ── Employer List ─────────────────────────────────────────────────────────── */

function EmployerList({
  employers,
  school,
  onSelect,
  detailLoading,
}: {
  employers: ApiEmployerMatch[];
  school: SchoolConfig;
  onSelect: (name: string) => void;
  detailLoading: boolean;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div>
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
          Employers
        </h1>
        <p
          style={{
            fontFamily: FONT,
            fontSize: "14px",
            color: "rgba(255,255,255,0.5)",
            lineHeight: 1.6,
          }}
        >
          {employers.length} regional employers ranked by curriculum skill alignment
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        {employers.map((emp, i) => (
          <motion.div
            key={emp.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: Math.min(i * 0.03, 0.5) }}
          >
            <button
              onClick={() => onSelect(emp.name)}
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
                  {emp.name}
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
                  <span>{emp.sector}</span>
                  <span>{emp.occupations.length} occupation{emp.occupations.length !== 1 ? "s" : ""}</span>
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
                {emp.matching_skills} skills
              </Badge>
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/* ── Employer Detail ───────────────────────────────────────────────────────── */

function EmployerDetailView({
  detail,
  school,
  onBack,
}: {
  detail: ApiEmployerDetail;
  school: SchoolConfig;
  onBack: () => void;
}) {
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
        Back to employers
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
            marginBottom: "6px",
          }}
        >
          {detail.name}
        </h2>
        <div
          style={{
            fontFamily: FONT,
            fontSize: "13px",
            color: "rgba(255,255,255,0.4)",
            display: "flex",
            gap: "20px",
          }}
        >
          {detail.sector && <span>{detail.sector}</span>}
          <span>{detail.regions.join(" · ")}</span>
        </div>
      </div>

      {/* Occupations */}
      {detail.occupations.map((occ) => {
        const aligned = occ.skills.filter((s: any) => s.developed);
        const gaps = occ.skills.filter((s: any) => !s.developed);

        return (
          <div
            key={occ.soc_code}
            style={{
              background: "rgba(255,255,255,0.03)",
              borderRadius: "10px",
              padding: "20px 24px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <div style={{ fontFamily: FONT, fontSize: "15px", fontWeight: 500, color: "#f0eef4" }}>
                  {occ.title}
                </div>
                {occ.annual_wage && (
                  <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.4)", marginTop: "2px" }}>
                    ${occ.annual_wage.toLocaleString()} annual
                  </div>
                )}
              </div>
              <Badge
                style={{
                  color: school.brandColorLight,
                  background: `${school.brandColorLight}20`,
                  border: `1px solid ${school.brandColorLight}30`,
                  fontSize: "11px",
                }}
              >
                {aligned.length}/{occ.skills.length} skills
              </Badge>
            </div>

            {/* Aligned skills */}
            {aligned.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: gaps.length > 0 ? "14px" : 0 }}>
                {aligned.map((skill: any) => (
                  <div key={skill.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <circle cx="6" cy="6" r="5" stroke={school.brandColorLight} strokeWidth="1" />
                      <path d="M4 6l1.5 1.5L8 5" stroke={school.brandColorLight} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span style={{ fontFamily: FONT, fontSize: "13px", color: school.brandColorLight }}>
                      {skill.skill}
                    </span>
                    {skill.courses.length > 0 && (
                      <span style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                        — {skill.courses.slice(0, 3).map((c: any) => c.code).join(", ")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Gap skills */}
            {gaps.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {gaps.map((skill: any) => (
                  <span
                    key={skill.skill}
                    style={{
                      fontFamily: FONT,
                      fontSize: "11px",
                      color: "rgba(255,255,255,0.3)",
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.06)",
                      borderRadius: "100px",
                      padding: "3px 10px",
                    }}
                  >
                    {skill.skill}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </motion.div>
  );
}
