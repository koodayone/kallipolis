"use client";

import dynamic from "next/dynamic";
import PartnershipJourney from "../../components/PartnershipJourney";
import ActionBadge from "../../components/ActionBadge";

const ConvergenceFlowDiagram = dynamic(() => import("../../components/ConvergenceFlowDiagram"), { ssr: false });
const StateMap = dynamic(() => import("../../components/StateMap"), { ssr: false });

// ── Section primitives ───────────────────────────────────────────────────────

const BRAND = "#4fd1fd";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
      {children}
    </p>
  );
}

function BlueDivider() {
  return <div style={{ width: 64, height: 2, background: BRAND, borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2
      className="text-[24px] md:text-[32px] leading-[1.12] tracking-[-0.02em] text-white"
      style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}
    >
      {children}
    </h2>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExplorePartnershipsPage() {
  return (
    <>
      {/* ── Section 1: Convergence ── */}
      <section style={{ paddingTop: 120, paddingBottom: 0, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center">
          <Eyebrow>Intelligent Partnerships</Eyebrow>
          <BlueDivider />
          <SectionHeading>
            Build a Strong Workforce<br />by building strong partnerships.
          </SectionHeading>
          <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.6)", marginTop: 24, maxWidth: 640, marginLeft: "auto", marginRight: "auto" }}>
            Students, courses, occupations, and employers converge into a single partnership proposal — every claim grounded in evidence, every partnership positioned to advance a Strong Workforce.
          </p>
        </div>

        <div style={{ maxWidth: 1100, margin: "0 auto", marginTop: -16 }}>
          <ConvergenceFlowDiagram />
        </div>
      </section>

      {/* ── Section 2: Anatomy ── */}
      <section style={{ paddingTop: 32, paddingBottom: 0, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 0 }}>
          <Eyebrow>Regional Alignment</Eyebrow>
          <BlueDivider />
          <SectionHeading>Data-driven partnerships<br />that supply regional demand</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 24, maxWidth: 460, marginLeft: "auto", marginRight: "auto" }}>
            Craft partnership proposals that answer the questions workforce development demands — backed by trusted data from trusted institutions.
          </p>
        </div>

        <PartnershipJourney />

      </section>

      {/* ── Section 3: Regional Alignment ── */}
      <section style={{ paddingTop: 48, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div style={{ display: "flex", gap: 48, alignItems: "flex-start", maxWidth: 1100, margin: "0 auto" }}>

          {/* Left — Map */}
          <div style={{ flex: "0 0 50%", minHeight: 400 }}>
            <StateMap brightenAll />
          </div>

          {/* Right — Prose */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 32, paddingTop: 16 }}>
            <div style={{ textAlign: "center" }}>
              <Eyebrow>Regional Alignment</Eyebrow>
              <BlueDivider />
              <SectionHeading>Data-driven partnerships<br />that supply regional demand</SectionHeading>
            </div>

            <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)" }}>
              California&apos;s community colleges operate within eight regional consortia, each with a Strong Workforce Program development plan that names priority sectors and commits to advancing career technical education.
            </p>
            <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)" }}>
              Kallipolis knows which sectors each region prioritizes. When a partnership aligns with a regional priority, the system surfaces that alignment automatically — connecting the proposal to the institutional mandate the consortium has already committed to.
            </p>
          </div>
        </div>
      </section>

      {/* ── Section 4: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Atlas" neonColor="#f0425e" opacity={1} icon="cube" inline href="/atlas" invertHover />
        <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" inline href="/sources" invertHover />
      </section>
    </>
  );
}
