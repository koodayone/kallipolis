"use client";

import AuthorityCard from "../../components/AuthorityCard";
import DemoStudents from "../../components/DemoStudents";
import DemoCourses from "../../components/DemoCourses";
import DemoOccupations from "../../components/DemoOccupations";
import DemoEmployers from "../../components/DemoEmployers";
import PipelineDiagram from "../../components/PipelineDiagram";
import ActionBadge from "../../components/ActionBadge";
import {
  createMortarboardForm,
  createBookForm,
  createHardhatForm,
  createSkyscraperForm,
} from "../../lib/formFactories";

const ACCENT = "#c9a84c";

// ── Section primitives ───────────────────────────────────────────────────────

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
      {children}
    </p>
  );
}

function GoldDivider() {
  return <div style={{ width: 64, height: 2, background: ACCENT, borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
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

// ── Authority data ──────────────────────────────────────────────────────────

const AUTHORITIES = [
  {
    unitName: "Students",
    authorityName: "Chancellor's Office DataMart",
    logoPath: "/logos/chancellors_logo.png",
    factory: createMortarboardForm,
    demoScene: <DemoStudents />,
    whatData: "Four-digit TOP code grade distributions, enrollment shares by program area, and term calendar patterns from the statewide Management Information Systems.",
    transformation: "Synthetic student populations calibrated to real grade distributions and enrollment stickiness patterns. Each student receives a deterministic UUID and a competency portrait derived from their course history.",
    whyThisSource: "The Chancellor's Office DataMart is the canonical record of who enrolled, what they studied, and how they performed across the entire California Community College system.",
  },
  {
    unitName: "Courses",
    authorityName: "College Curriculum Catalogs",
    logoPath: "/logos/colleges_combined_white.png",
    factory: createBookForm,
    demoScene: <DemoCourses />,
    whatData: "Course names, codes, departments, unit counts, descriptions, prerequisites, learning outcomes, and course objectives extracted from institutional catalog PDFs.",
    transformation: "PDF extraction recovers structured course records. Each course's learning outcomes are interpreted through a skills taxonomy, producing graph edges that bridge curriculum to labor market demand.",
    whyThisSource: "The college's own catalog is its curricular commitment. The official declaration of what it promises to teach, at what depth, with what outcomes.",
  },
  {
    unitName: "Occupations",
    authorityName: "Centers of Excellence",
    logoPath: "/logos/coe_logo_clean.png",
    factory: createHardhatForm,
    demoScene: <DemoOccupations />,
    whatData: "SOC-coded occupation records with annual wages, employment counts, five-year growth rates, annual openings, and education level requirements organized by COE region.",
    transformation: "A workforce-development band filter retains only occupations in the credential range community colleges serve. Regional demand signals are aggregated by COE region, aligning with the system's own geographic logic.",
    whyThisSource: "Centers of Excellence research is regionally calibrated to CCC service areas. More relevant than national BLS or O*NET data for workforce development planning.",
  },
  {
    unitName: "Employers",
    authorityName: "Employment Development Department",
    logoPath: "/logos/edd_logo_clean.png",
    factory: createSkyscraperForm,
    demoScene: <DemoEmployers />,
    whatData: "Employer records from the EDD ALMIS database, including organization names, NAICS industry codes, county-level location, and employee counts.",
    transformation: "Filtered to organizations with 100 or more employees. A NAICS-to-SOC crosswalk connects each employer to the occupations it hires for. Names and descriptions normalized through an LLM pass.",
    whyThisSource: "EDD maintains the state's authoritative employer records. Verifiable, comprehensive, and publicly maintained. Institutional legitimacy that matters in public-sector procurement.",
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExploreSourcesPage() {
  return (
    <>
      {/* ── Section 1: Hero (prose-led) ── */}
      <section style={{ paddingTop: 120, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center">
          <Eyebrow>The Epistemology</Eyebrow>
          <GoldDivider />
          <SectionHeading>
            Every claim has a public source.<br />Every source has a public institution.
          </SectionHeading>
          <p style={{ fontSize: 18, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24, maxWidth: 600, marginLeft: "auto", marginRight: "auto" }}>
            Four analytical forms. Four public data authorities. Each unit of analysis traces to one institution whose data grounds every claim.
          </p>
        </div>
      </section>

      {/* ── Section 2: Authority deep dives — each with its graph row ── */}
      <section style={{ paddingTop: 32, paddingBottom: 32, paddingLeft: 64, paddingRight: 64 }}>
        <div>
          {AUTHORITIES.map((auth) => (
            <AuthorityCard key={auth.unitName} {...auth} />
          ))}
        </div>
      </section>

      {/* ── Section 3: Forward Deployment (prose-led) ── */}
      <section style={{ paddingTop: 48, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-2xl mx-auto text-center">
          <Eyebrow>Forward Deployment</Eyebrow>
          <GoldDivider />
          <SectionHeading>Limitations become invitations</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 24 }}>
            Student data is synthetic, not real enrollments. Catalog PDFs lag behind live curricula. COE granularity varies by region. EDD captures registered employers, not hiring intent.
          </p>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 16 }}>
            Each of these limitations is an invitation to collaborate. The pipeline is architected for institutional partnership. Direct MIS feeds replace synthetic students. Curriculum API access makes courses real-time. Local industry contacts validate employer readiness. Forward-deployment into the institution closes the gaps that distance creates.
          </p>
        </div>
      </section>

      {/* ── Section 4: Pipeline (component-led) ── */}
      <section style={{ paddingTop: 48, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 48 }}>
          <Eyebrow>The Pipeline</Eyebrow>
          <GoldDivider />
          <SectionHeading>From institutional data<br />to a unified knowledge graph</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 20 }}>
            Each data authority feeds a dedicated pipeline stage. The stages converge in a single graph where curriculum, labor market, and institutional data connect through a shared skills vocabulary.
          </p>
        </div>

        <PipelineDiagram />
      </section>

      {/* ── Section 5: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Atlas" neonColor="#f0425e" opacity={1} icon="cube" inline href="/atlas" invertHover />
        <ActionBadge label="Explore Partnerships" neonColor="#b0a0ff" opacity={1} icon="chainlink" inline href="/partnerships" invertHover />
      </section>
    </>
  );
}
