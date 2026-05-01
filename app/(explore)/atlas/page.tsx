"use client";

import FormCard from "../../components/FormCard";
import StateAtlasDemo from "../../components/StateAtlasDemo";
import ActionBadge from "../../components/ActionBadge";
import FadeUp from "../../components/FadeUp";
import {
  createMortarboardForm,
  createBookForm,
  createChainlinkForm,
  createHardhatForm,
  createSkyscraperForm,
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

// Five forms in a pyramid: top row carries the active layer
// (people + the partnership unit of action), bottom row carries the
// curricular and labor-market substrates that feed them. Mirrors the
// atlas product (atlas/college-atlas/scene.ts).
const FORMS = [
  // Top row — supply-side person | unit of action | demand-side person
  { factory: createMortarboardForm, label: "Students",     source: "Chancellor's Office DataMart", description: "The people the college system serves. Simulated academic journeys calibrated to state data." },
  { factory: createChainlinkForm,   label: "Partnerships", source: "Generated Through Analysis",   description: "Data-driven partnership proposals that connect institutional capacity to employer need." },
  { factory: createSkyscraperForm,  label: "Employers",    source: "Employment Development Dept.", description: "Real organizations from state labor records, scoped to those community colleges can meaningfully engage." },
  // Bottom row — curricular substrate | labor-market substrate
  { factory: createBookForm,        label: "Courses",      source: "College Curriculum Catalogs",  description: "The institution's curricular commitment. The courses that are taught, and the skills they teach." },
  { factory: createHardhatForm,     label: "Occupations",  source: "Centers of Excellence",        description: "Regional labor demand signals of relevant occupations grounded in workforce-oriented research." },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExploreAtlasPage() {
  return (
    <>
      {/* ── Section 1: Hero ── */}
      <section className="md:pt-[120px] md:pb-12 md:px-16 max-md:pt-24 max-md:pb-8 max-md:px-6">
        <FadeUp className="max-w-3xl mx-auto text-center">
          <SectionHeading>Each college is a world</SectionHeading>
          <div style={{ width: 64, height: 2, background: "#f0425e", borderRadius: 1, opacity: 0.9, margin: "24px auto 0" }} />
          <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24 }}>
            Selecting a college opens a three-dimensional space of five rotating forms. Each form is an entry point into a dimension of institutional reality — click to explore, and the atlas dissolves into a natural language interface native to the form.
          </p>
          <p style={{ fontSize: 17, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 16 }}>
            Four of these forms are analytical — students, courses, occupations, and employers — each grounded in a public data authority. The fifth is the unit of action that integrates them: partnership proposals formulated from the four analytical forms.
          </p>
        </FadeUp>
      </section>

      {/* ── Section 2: The Five Forms (pyramid) ── */}
      <section className="md:pt-4 md:pb-16 md:px-16 max-md:pt-4 max-md:pb-10 max-md:px-6">
        {/* Desktop: top row of 3 cards, bottom row of 2 cards centered
            under the gaps — same pyramid shape as the atlas product.
            Mobile: single-column stack. */}
        <FadeUp className="flex flex-col gap-5 max-w-[960px] mx-auto">
          <div className="flex md:flex-row md:gap-5 max-md:flex-col max-md:gap-4">
            {FORMS.slice(0, 3).map((form) => (
              <div key={form.label} className="md:flex-1 max-md:w-full">
                <FormCard
                  factory={form.factory}
                  label={form.label}
                  source={form.source}
                  description={form.description}
                />
              </div>
            ))}
          </div>
          <div className="flex md:flex-row md:gap-5 md:justify-center max-md:flex-col max-md:gap-4">
            {FORMS.slice(3).map((form) => (
              <div key={form.label} className="md:basis-[calc((100%-2.5rem)/3)] md:grow-0 md:shrink-0 max-md:w-full">
                <FormCard
                  factory={form.factory}
                  label={form.label}
                  source={form.source}
                  description={form.description}
                />
              </div>
            ))}
          </div>
        </FadeUp>
      </section>

      {/* ── Section 3: Two Scales ── */}
      <section className="md:pt-12 md:pb-16 md:px-16 max-md:pt-10 max-md:pb-10 max-md:px-6">
        <FadeUp>
          <StateAtlasDemo />
        </FadeUp>
      </section>

      {/* ── Section 4: Cross-links ── */}
      <FadeUp className="bg-[#060d1f] flex justify-center md:pt-6 md:pb-12 md:px-16 md:gap-4 max-md:pt-6 max-md:pb-10 max-md:px-4 max-md:gap-3 max-md:flex-wrap">
        <ActionBadge label="Home" neonColor="#f5e6c8" opacity={1} icon="sun" inline href="/#atlas" invertHover />
        <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline href="/partnerships" invertHover />
        <ActionBadge label="Explore Sources" neonColor="#c9a84c" opacity={1} icon="lightbulb" inline href="/sources" invertHover />
      </FadeUp>
    </>
  );
}
