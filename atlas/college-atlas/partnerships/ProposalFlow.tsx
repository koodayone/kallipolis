"use client";

import { AnimatePresence, motion } from "framer-motion";
import { SchoolConfig } from "@/config/schoolConfig";
import type {
  ApiEmployerOccupation,
  ApiPartnershipOpportunity,
  ApiTargetedProposal,
} from "@/college-atlas/partnerships/api";
import RisingSun from "@/ui/RisingSun";
import ProposalCard from "./ProposalCard";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  school: SchoolConfig;
  employer: ApiPartnershipOpportunity;
  phase: "draft" | "generating" | "complete";
  // Occupation picker props (only meaningful when phase === "draft")
  occupations: ApiEmployerOccupation[];
  coeRegion: string;
  selectedSocCode: string | null;
  occupationsLoading: boolean;
  occupationsError: string | null;
  onSelectSoc: (soc: string) => void;
  onGenerate: () => void;
  // Generation result handling
  onRetry: () => void;
  onReject: () => void;
  proposal: ApiTargetedProposal | null;
  proposalError: string | null;
};

// Format helpers used inside the picker cards.
function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

function formatWage(n: number | null | undefined): string {
  if (n == null) return "—";
  return `$${n.toLocaleString()}`;
}

function formatGrowth(n: number | null | undefined): string {
  if (n == null) return "—";
  const pct = (n * 100).toFixed(1);
  return `${n >= 0 ? "+" : ""}${pct}%`;
}

export default function ProposalFlow({
  school, employer, phase,
  occupations, coeRegion, selectedSocCode, occupationsLoading, occupationsError,
  onSelectSoc, onGenerate,
  onRetry, onReject, proposal, proposalError,
}: Props) {
  const brandColor = school.brandColorLight;
  return (
    <div style={{ maxWidth: "640px", margin: "0 auto", padding: "48px 40px" }}>
      <AnimatePresence mode="wait">

        {/* ── Draft: occupation picker ── */}
        {phase === "draft" && (
          <motion.div key="draft" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
            <div style={{ marginBottom: "16px" }}>
              <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.5)", lineHeight: 1.6, margin: 0 }}>
                You&apos;ve selected <span style={{ color: brandColor, fontWeight: 600 }}>{employer.name}</span>.
              </p>
            </div>

            {/* Employer overview block — description + homepage. Surfaces the
                context that used to live in the expandable Build mode row. */}
            {(employer.description || employer.website) && (
              <div style={{ marginBottom: "32px", display: "flex", flexDirection: "column", gap: "14px" }}>
                {employer.description && (
                  <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.7)", lineHeight: 1.6, margin: 0 }}>
                    {employer.description}
                  </p>
                )}
                {employer.website && (
                  <a
                    href={employer.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: "inline-flex", alignItems: "center", gap: "6px",
                      padding: "3px 10px", borderRadius: "100px",
                      fontFamily: FONT, fontSize: "11px", fontWeight: 600, letterSpacing: "0.07em",
                      textTransform: "uppercase",
                      color: "rgba(255,255,255,0.5)", background: "transparent",
                      border: "1px solid rgba(255,255,255,0.12)", textDecoration: "none",
                      transition: "border-color 0.15s, color 0.15s", width: "fit-content",
                    }}
                    onMouseEnter={(e) => { const el = e.currentTarget; el.style.borderColor = `${brandColor}4d`; el.style.color = brandColor; el.querySelectorAll("svg").forEach((s) => (s.style.stroke = brandColor)); }}
                    onMouseLeave={(e) => { const el = e.currentTarget; el.style.borderColor = "rgba(255,255,255,0.12)"; el.style.color = "rgba(255,255,255,0.5)"; el.querySelectorAll("svg").forEach((s) => (s.style.stroke = "rgba(255,255,255,0.4)")); }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ stroke: "rgba(255,255,255,0.4)", transition: "stroke 0.15s", flexShrink: 0 }} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                    </svg>
                    Employer Home Page
                  </a>
                )}
              </div>
            )}

            {/* Headline + info-icon tooltip explaining what the selection scopes. */}
            <div style={{ marginBottom: "8px" }}>
              <h3 style={{
                fontFamily: FONT, fontSize: "16px", fontWeight: 600, color: "#f0eef4",
                margin: "0 0 6px", display: "flex", alignItems: "center", gap: "8px",
              }}>
                Which role at {employer.name} are you targeting?
                <span
                  title="The selection scopes the partnership artifact's regional demand, curriculum alignment, and student impact sections."
                  style={{
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    width: "16px", height: "16px", borderRadius: "50%",
                    border: "1px solid rgba(255,255,255,0.25)",
                    fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.55)",
                    cursor: "help", lineHeight: 1,
                  }}
                  aria-label="The selection scopes the partnership artifact's regional demand, curriculum alignment, and student impact sections."
                >
                  i
                </span>
              </h3>
            </div>

            {/* Loading / error / empty / list */}
            {occupationsLoading && (
              <div style={{ padding: "32px 0", textAlign: "center" }}>
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.35)" }}>
                  Loading occupations…
                </p>
              </div>
            )}

            {!occupationsLoading && occupationsError && (
              <div style={{ padding: "24px 0" }}>
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(248,113,113,0.8)" }}>
                  Failed to load occupations: {occupationsError}
                </p>
              </div>
            )}

            {!occupationsLoading && !occupationsError && occupations.length === 0 && (
              <div style={{ padding: "24px 0" }}>
                <p style={{ fontFamily: FONT, fontSize: "13px", color: "rgba(255,255,255,0.45)" }}>
                  No occupations recorded for this employer in the {coeRegion || school.name} region.
                </p>
              </div>
            )}

            {!occupationsLoading && !occupationsError && occupations.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "20px", marginBottom: "20px" }}>
                {occupations.map((occ) => {
                  const selected = selectedSocCode === occ.soc_code;
                  return (
                    <button
                      key={occ.soc_code}
                      onClick={() => onSelectSoc(occ.soc_code)}
                      style={{
                        textAlign: "left", padding: "16px 18px", borderRadius: "10px", cursor: "pointer",
                        border: `1px solid ${selected ? brandColor + "60" : "rgba(255,255,255,0.08)"}`,
                        background: selected ? `${brandColor}10` : "rgba(255,255,255,0.02)",
                        transition: "border-color 0.15s, background 0.15s",
                      }}
                      onMouseEnter={(e) => { if (!selected) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"; e.currentTarget.style.background = "rgba(255,255,255,0.04)"; } }}
                      onMouseLeave={(e) => { if (!selected) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; e.currentTarget.style.background = "rgba(255,255,255,0.02)"; } }}
                    >
                      {/* Identity row */}
                      <div style={{ fontFamily: FONT, fontSize: "14px", fontWeight: 600, color: selected ? brandColor : "rgba(255,255,255,0.85)", marginBottom: "4px" }}>
                        {occ.title}
                      </div>

                      {/* SOC line */}
                      <div style={{ fontFamily: FONT, fontSize: "11px", color: "rgba(255,255,255,0.35)", letterSpacing: "0.04em", marginBottom: "10px" }}>
                        SOC {occ.soc_code}
                      </div>

                      {/* Demand signal */}
                      <div style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.55)", lineHeight: 1.5 }}>
                        {formatNumber(occ.annual_openings)} annual openings
                        {" · "}{formatWage(occ.annual_wage)} median
                        {" · "}{formatGrowth(occ.growth_rate)} employment growth
                      </div>

                      {/* Institutional alignment depth — surfaces the
                          PREPARES_FOR-rooted course count that drives
                          the picker's sort. The picker is filtered
                          server-side to occupations with
                          aligned_course_count > 0; this line tells
                          the coordinator the depth at a glance.
                          Hidden when the field is missing (older
                          API responses or the gather hasn't run). */}
                      {typeof occ.aligned_course_count === "number" && occ.aligned_course_count > 0 && (
                        <div style={{
                          fontFamily: FONT, fontSize: "11px", color: brandColor, opacity: 0.85,
                          marginTop: "8px", letterSpacing: "0.02em",
                        }}>
                          {occ.aligned_course_count} related course{occ.aligned_course_count === 1 ? "" : "s"} offered at {school.name}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {!occupationsLoading && !occupationsError && occupations.length > 0 && (
              <button
                onClick={onGenerate}
                disabled={!selectedSocCode}
                style={{
                  width: "100%", padding: "14px 24px", borderRadius: "8px",
                  fontFamily: FONT, fontSize: "14px", fontWeight: 600,
                  cursor: selectedSocCode ? "pointer" : "default", border: "none",
                  background: selectedSocCode ? brandColor : "rgba(255,255,255,0.06)",
                  color: selectedSocCode ? "#1a1a2e" : "rgba(255,255,255,0.25)",
                  transition: "opacity 0.15s, background 0.2s",
                }}
                onMouseEnter={(e) => { if (selectedSocCode) e.currentTarget.style.opacity = "0.85"; }}
                onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
              >
                Generate Proposal
              </button>
            )}
          </motion.div>
        )}

        {/* ── Generating ── Loading affordance reuses the rising-sun
            idiom from QueryShell so the partnership flow speaks the same
            visual vocabulary as the analytical natural-language query
            views (students, courses, occupations, employers). */}
        {phase === "generating" && (
          <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "400px", gap: "20px" }}>
            <RisingSun style={{ width: "90px", height: "auto", opacity: 0.4 }} />
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.4)", margin: 0 }}>
              Generating {employer.name} partnership proposal...
            </p>
          </motion.div>
        )}

        {/* ── Complete: Proposal ── */}
        {phase === "complete" && proposal && (
          <motion.div key="proposal" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            <ProposalCard
              proposal={proposal}
              brandColor={brandColor}
              onDismiss={onReject}
              onReject={onReject}
              collegeId={school.name}
            />
          </motion.div>
        )}

        {/* ── Complete: Error ── */}
        {phase === "complete" && proposalError && !proposal && (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "300px", gap: "16px" }}>
            <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(248,113,113,0.8)", margin: "0 0 8px" }}>
              Failed to generate proposal: {proposalError}
            </p>
            <button onClick={onRetry}
              style={{ fontFamily: FONT, fontSize: "12px", fontWeight: 600, cursor: "pointer", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "rgba(255,255,255,0.7)", borderRadius: "6px", padding: "6px 14px" }}>
              Retry
            </button>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
