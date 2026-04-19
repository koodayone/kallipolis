"use client";

import dynamic from "next/dynamic";
import PartnershipJourney from "../../components/PartnershipJourney";
import ActionBadge from "../../components/ActionBadge";

const ConvergenceFlowDiagram = dynamic(() => import("../../components/ConvergenceFlowDiagram"), {
  ssr: false,
  loading: () => <div style={{ width: "100%", height: 600 }} />,
});
const RegionalUnificationMap = dynamic(() => import("../../components/RegionalUnificationMap"), {
  ssr: false,
  loading: () => <div style={{ width: "100%", minHeight: 400 }} />,
});

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
            Students, courses, occupations, and employers converge into a single partnership proposal. Every claim is grounded in evidence, and every partnership is positioned to advance a Strong Workforce.
          </p>
        </div>

        <div style={{ maxWidth: 1100, margin: "0 auto", marginTop: -16 }}>
          <ConvergenceFlowDiagram />
        </div>
      </section>

      {/* ── Section 2: Anatomy ── */}
      <section style={{ paddingTop: 32, paddingBottom: 0, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 0 }}>
          <Eyebrow>Anatomy of a Partnership</Eyebrow>
          <BlueDivider />
          <SectionHeading>Data-driven partnerships<br />that supply regional demand</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 24, maxWidth: 460, marginLeft: "auto", marginRight: "auto" }}>
            Craft partnership proposals that answer the questions workforce development demands. Let&apos;s journey through the layers of a partnership proposal for Golden State Solar, an imaginary company in the renewable energy sector.
          </p>
        </div>

        <PartnershipJourney />

      </section>

      {/* ── Section 3: Regional Alignment ── */}
      <section style={{ paddingTop: 0, paddingBottom: 64, paddingLeft: 64, paddingRight: 64, marginTop: -24 }}>
        <div style={{ display: "flex", gap: 48, alignItems: "flex-start", maxWidth: 1100, margin: "0 auto" }}>

          {/* Left — Map */}
          <div style={{ flex: "0 0 55%", minHeight: 400, paddingRight: 24 }}>
            <RegionalUnificationMap />
          </div>

          {/* Right — Prose */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 36, paddingTop: 0 }}>
            <div style={{ textAlign: "center" }}>
              <Eyebrow>Regional Alignment</Eyebrow>
              <BlueDivider />
              <SectionHeading>Coordinate across<br />Regional Consortia</SectionHeading>
            </div>

            <div>
              <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: BRAND, display: "block", marginBottom: 8 }}>
                Eight Regional Consortia
              </span>
              <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", margin: 0 }}>
                Partnerships that promote regional priorities require effective coordination. Collaborate on partnerships based on a shared surface.
              </p>
            </div>

            <div>
              <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: BRAND, display: "block", marginBottom: 8 }}>
                Strong Workforce
              </span>
              <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", margin: 0 }}>
                Every California Community College shares the common goal of Strong Workforce. Lead partnerships that move the vision forward.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 4: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "0 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Home" neonColor="#f5e6c8" opacity={1} icon="sun" inline href="/#partnerships" invertHover />
        <ActionBadge label="Explore Atlas" neonColor="#f0425e" opacity={1} icon="cube" inline href="/atlas" invertHover />
        <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" inline href="/sources" invertHover />
      </section>
    </>
  );
}
