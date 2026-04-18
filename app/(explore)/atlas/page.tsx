"use client";

import FormCard from "../../components/FormCard";
import StateAtlasDemo from "../../components/StateAtlasDemo";
import ActionBadge from "../../components/ActionBadge";
import {
  createMortarboardForm,
  createBookForm,
  createChainlinkForm,
  createHardhatForm,
  createSkyscraperForm,
  createDumbbellForm,
} from "../../lib/formFactories";


// ── Section primitives ───────────────────────────────────────────────────────

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
      {children}
    </p>
  );
}

function GoldDivider() {
  return <div style={{ width: 64, height: 2, background: "#f0425e", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
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

// ── Form definitions ─────────────────────────────────────────────────────────

const FORMS = [
  // Top row
  { factory: createMortarboardForm, label: "Students",         source: "Chancellor's Office DataMart",   description: "The people the college system serves. Simulated academic journeys calibrated to state data." },
  { factory: createChainlinkForm,   label: "Partnerships",     source: "Generated Through Analysis", description: "Data-driven partnership proposals that connect institutional capacity to employer need." },
  { factory: createSkyscraperForm,  label: "Employers",        source: "Employment Development Dept.",    description: "Real organizations from state labor records, scoped to those community colleges can meaningfully engage." },
  // Bottom row
  { factory: createBookForm,        label: "Courses",          source: "College Curriculum Catalogs",     description: "The institution's curricular commitment. The courses that are taught, and the skills they teach." },
  { factory: createDumbbellForm,    label: "Strong Workforce", source: "Derived from partnerships",      description: "Partnership proposals translated into NOVA-compatible Strong Workforce Program applications." },
  { factory: createHardhatForm,     label: "Occupations",      source: "Centers of Excellence",          description: "Regional labor demand signals of relevant occupations grounded in workforce-oriented research." },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExploreAtlasPage() {
  return (
    <>
      {/* ── Section 1: Hero ── */}
      <section style={{ paddingTop: 120, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center">
          <Eyebrow>The Atlas</Eyebrow>
          <GoldDivider />
          <SectionHeading>Each college is a world</SectionHeading>
          <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24 }}>
            Selecting a college opens a three-dimensional space of six rotating forms. Each form is an entry point into a dimension of institutional reality — click to explore, and the atlas dissolves into a natural language interface native to the form.
          </p>
          <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 16 }}>
            Four of these forms are analytical — students, courses, occupations, and employers — each grounded in a public data authority. The remaining two are action-driven: partnerships and strong workforce proposals formulated from the four analytical forms.
          </p>
        </div>
      </section>

      {/* ── Section 2: The Six Forms ── */}
      <section style={{ paddingTop: 16, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 20,
            maxWidth: 960,
            margin: "0 auto",
          }}
        >
          {FORMS.map((form) => (
            <FormCard
              key={form.label}
              factory={form.factory}
              label={form.label}
              source={form.source}
              description={form.description}
            />
          ))}
        </div>
      </section>

      {/* ── Section 3: Two Scales ── */}
      <section style={{ paddingTop: 48, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <StateAtlasDemo />
      </section>

      {/* ── Section 4: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" inline href="/sources" invertHover />
        <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline href="/partnerships" invertHover />
      </section>
    </>
  );
}
