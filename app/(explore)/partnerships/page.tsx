import ConvergenceDiagram from "../../components/ConvergenceDiagram";
import PipelineStageCard from "../../components/PipelineStageCard";
import StaticProposalCard from "../../components/StaticProposalCard";
import EngagementTypeCards from "../../components/EngagementTypeCards";
import ActionBadge from "../../components/ActionBadge";

// ── Section primitives ───────────────────────────────────────────────────────

const BRAND = "#b0a0ff";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
      {children}
    </p>
  );
}

function PurpleDivider() {
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
      {/* ── Section 1: Hero ── */}
      <section style={{ paddingTop: 120, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center">
          <Eyebrow>Intelligent Partnerships</Eyebrow>
          <PurpleDivider />
          <SectionHeading>
            From data convergence<br />to actionable proposals
          </SectionHeading>
          <p style={{ fontSize: 18, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24, maxWidth: 600, marginLeft: "auto", marginRight: "auto" }}>
            Partnership proposals are not templates. They emerge from the convergence of all four units of analysis — students, courses, occupations, and employers — queried simultaneously against a unified knowledge graph.
          </p>
        </div>
      </section>

      {/* ── Section 2: Convergence ── */}
      <section style={{ paddingTop: 0, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 24 }}>
          <Eyebrow>The Convergence</Eyebrow>
          <PurpleDivider />
          <SectionHeading>Four units in.<br />One proposal out.</SectionHeading>
        </div>

        <ConvergenceDiagram />

        <div className="max-w-2xl mx-auto" style={{ marginTop: 24 }}>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", textAlign: "center" }}>
            Each proposal draws on employer metadata, regional occupation demand, aligned curriculum, and student pipeline data. The system queries across all four simultaneously, ensuring that every claim in the proposal is grounded in evidence from the graph.
          </p>
        </div>
      </section>

      {/* ── Section 3: Three-Stage Pipeline ── */}
      <section style={{ paddingTop: 48, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 40 }}>
          <Eyebrow>The Pipeline</Eyebrow>
          <PurpleDivider />
          <SectionHeading>Gather. Filter. Narrate.</SectionHeading>
        </div>

        <div style={{ display: "flex", gap: 20, maxWidth: 960, margin: "0 auto" }}>
          <PipelineStageCard
            number="1"
            name="Gather"
            methodology="Graph queries retrieve the full context for a partnership: employer metadata, the occupations it hires for, regional demand evidence, curriculum aligned to core skills, and the student pipeline with matching competency profiles."
            inputs="Employer name, college identity, engagement type"
            outputs="Employer context, occupation evidence, curriculum alignment, student pipeline data"
          />
          <PipelineStageCard
            number="2"
            name="Filter"
            methodology="LLM-based intelligence applies domain judgment to the gathered context. It selects the primary occupation, identifies the core skills, narrows to the most relevant departments, and — for curriculum co-design — identifies one gap skill the curriculum does not yet develop."
            inputs="Full gathered context from Stage 1"
            outputs="Selected occupation, core skills, relevant departments, gap skill (if applicable)"
          />
          <PipelineStageCard
            number="3"
            name="Narrate"
            methodology="Claude generates proposal prose constrained to evidence from the gather stage. The narrative cannot hallucinate — it can only reference data that was retrieved from the graph. A post-generation faithfulness check verifies that every claim is supported."
            inputs="Filtered context with selected occupation and core skills"
            outputs="Four-section proposal: opportunity, curriculum alignment, student pipeline, roadmap"
          />
        </div>
      </section>

      {/* ── Section 4: Anatomy of a Proposal ── */}
      <section style={{ paddingTop: 48, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 40 }}>
          <Eyebrow>The Proposal</Eyebrow>
          <PurpleDivider />
          <SectionHeading>Anatomy of a<br />data-driven partnership</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 20 }}>
            Every proposal follows the same structure: an opportunity grounded in labor market evidence, curriculum alignment verified against institutional course records, a student pipeline quantified from enrollment data, and a concrete roadmap. Narrative prose is always accompanied by its underlying evidence.
          </p>
        </div>

        <div style={{ maxWidth: 800, margin: "0 auto", position: "relative" }}>
          {/* Annotations */}
          <div style={{
            position: "absolute", left: -220, top: 40, width: 180,
            display: "flex", flexDirection: "column", gap: 120,
          }}>
            {[
              { label: "Labor market evidence", note: "Wages, openings, and growth rates from Centers of Excellence regional data" },
              { label: "Institutional curriculum", note: "Course records from the college's own catalog, parsed and skill-mapped" },
              { label: "Student pipeline", note: "Enrollment counts and competency profiles calibrated to DataMart" },
            ].map((ann) => (
              <div key={ann.label} style={{ textAlign: "right" }}>
                <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, display: "block", marginBottom: 4 }}>
                  {ann.label}
                </span>
                <p style={{ fontSize: 12, lineHeight: 1.5, color: "rgba(255,255,255,0.35)", margin: 0 }}>
                  {ann.note}
                </p>
              </div>
            ))}
          </div>

          <StaticProposalCard />
        </div>
      </section>

      {/* ── Section 5: Engagement Types ── */}
      <section style={{ paddingTop: 48, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 40 }}>
          <Eyebrow>Three Engagement Types</Eyebrow>
          <PurpleDivider />
          <SectionHeading>One pipeline, three modes<br />of institutional engagement</SectionHeading>
        </div>

        <EngagementTypeCards />
      </section>

      {/* ── Section 6: Strong Workforce Connection ── */}
      <section style={{ paddingTop: 48, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-2xl mx-auto text-center">
          <Eyebrow>Strong Workforce</Eyebrow>
          <PurpleDivider />
          <SectionHeading>From partnership<br />to funded project</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 24 }}>
            A discovered partnership is not an endpoint — it is feedstock for institutional action. The same occupation evidence, curriculum alignment, and student pipeline data that justifies a partnership also supplies the labor market information context required for a NOVA-compatible Strong Workforce Program application. The proposal becomes a fundable project.
          </p>

          <div style={{
            marginTop: 32, padding: "20px 28px",
            background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8, textAlign: "left",
          }}>
            <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: 12 }}>
              NOVA Application Sections
            </span>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                "Vision for Success alignment",
                "Regional labor market demand",
                "Supply and capacity analysis",
                "Student impact justification",
                "Curriculum alignment",
                "Employer engagement strategy",
                "Outcome metrics and evaluation",
              ].map((section) => (
                <div key={section} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 4, height: 4, borderRadius: "50%", background: `${BRAND}60`, flexShrink: 0 }} />
                  <span style={{ fontSize: 14, color: "rgba(255,255,255,0.55)" }}>{section}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 7: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Atlas" neonColor="#c9a84c" opacity={1} icon="cube" inline href="/atlas" />
        <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" inline href="/sources" />
      </section>
    </>
  );
}
