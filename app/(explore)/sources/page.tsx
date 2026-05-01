"use client";

import AuthorityCard from "../../components/AuthorityCard";
import FadeUp from "../../components/FadeUp";
import DemoStudents from "../../components/DemoStudents";
import DemoCourses from "../../components/DemoCourses";
import DemoOccupations from "../../components/DemoOccupations";
import DemoEmployers from "../../components/DemoEmployers";
import UnifiedKnowledgeDiagram from "../../components/UnifiedKnowledgeDiagram";
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
    authority: "The California Community Colleges Chancellor's Office maintains the Management Information System Data Mart — the statewide system of record for enrollment, course-taking, and academic outcomes across all 116 colleges. Every student who enrolls in a California community college is represented in this system.",
    intelligence: "Kallipolis models student populations that mirror real enrollment patterns reported by each institution. The system surfaces academic trajectories, program concentrations, and competency profiles. A coordinator can see not just how many students are in a program, but what coursework they've completed and how that prepares them for the occupations regional employers hire for.",
    methodology: "Student populations are synthetically generated and calibrated to DataMart's grade distributions by program area. Aggregate patterns — enrollment concentration, academic performance, program retention — match institutional reality by design. The methodology is a present-day commitment to privacy that the architecture is designed to outgrow through direct institutional partnership.",
  },
  {
    unitName: "Courses",
    authorityName: "College Curriculum Catalogs",
    logoPath: "/logos/colleges_combined_white.png",
    factory: createBookForm,
    demoScene: <DemoCourses />,
    authority: "Each college's course catalog is its curricular commitment — the institutional declaration of what it promises to teach, at what depth, with what outcomes. Kallipolis sources directly from the institution itself.",
    intelligence: "Every course carries a TOP code — the Chancellor's Office's program taxonomy — that crosswalks to the SOC occupations its curriculum prepares students for. This institutional bridge is what grounds partnership proposals in the same evidence workforce-development funding already requires.",
    methodology: "Each course is assigned a TOP code from the program record the college reports to the Chancellor's Office, and a set of skills extracted from its catalog description against a controlled vocabulary. Skills come from a fixed taxonomy rather than freely generated — preventing the system from inventing competencies that don't exist in the curriculum.",
  },
  {
    unitName: "Occupations",
    authorityName: "Centers of Excellence",
    logoPath: "/logos/coe_logo_clean.png",
    factory: createHardhatForm,
    demoScene: <DemoOccupations />,
    authority: "The Centers of Excellence for Labor Market Research is the analytical arm of California's community college system. Its institutional purpose is to produce the labor market intelligence that workforce development decisions depend on. COE research is regionally calibrated to community college service areas.",
    intelligence: "Each occupation carries a SOC code — the federal occupational classification — that crosswalks to the TOP programs whose courses prepare students to enter it. Regional wages, employment, growth, and annual openings make demand legible against the curriculum that supplies it.",
    methodology: "COE's regional demand data is filtered to the workforce-development band — occupations where community college credentials are the pathway. Skills are drawn from the same controlled taxonomy used for courses, creating a shared vocabulary that aligns occupational demand with curricular supply.",
  },
  {
    unitName: "Employers",
    authorityName: "Employment Development Department",
    logoPath: "/logos/edd_logo_clean.png",
    factory: createSkyscraperForm,
    demoScene: <DemoEmployers />,
    authority: "The California Employment Development Department maintains employer records for every organization with payroll obligations in the state. These are verifiable, publicly maintained records that carry institutional legitimacy.",
    intelligence: "Kallipolis surfaces employers scoped to those community colleges can meaningfully engage — organizations with operational capacity for workforce partnerships. Each employer is connected to the occupations it hires for and to the courses that prepare students to enter those occupations. A coordinator sees not a list of companies, but a landscape of partnership-ready organizations.",
    methodology: "Employer records are filtered to organizations above a size threshold that ensures partnership capacity. Each employer is validated to have an active web presence and connected to relevant occupations through industry classification. The result is a curated set of real, verifiable organizations — a workforce development lens on the employers that matter for institutional action.",
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExploreSourcesPage() {
  return (
    <>
      {/* ── Section 1: Hero (prose-led) ── */}
      <section className="md:pt-[120px] md:pb-12 md:px-16 max-md:pt-24 max-md:pb-8 max-md:px-6">
        <FadeUp className="max-w-3xl mx-auto text-center">
          <SectionHeading>
            Every claim has a public source.<br />Every source has a public institution.
          </SectionHeading>
          <div style={{ width: 64, height: 2, background: ACCENT, borderRadius: 1, opacity: 0.9, margin: "24px auto 0" }} />
          <p style={{ fontSize: 18, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24, maxWidth: 600, marginLeft: "auto", marginRight: "auto" }}>
            Students. Courses. Occupations. Employers.<br />Each unit of analysis traces to one authoritative institution.<br />Query each domain via natural language.
          </p>
        </FadeUp>
      </section>

      {/* ── Section 2: Authority deep dives — each with its graph row ── */}
      <section className="md:pt-8 md:pb-8 md:px-16 max-md:pt-6 max-md:pb-6 max-md:px-6">
        <div>
          {AUTHORITIES.map((auth) => (
            <FadeUp key={auth.unitName}>
              <AuthorityCard {...auth} />
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ── Section 3: Pipeline (component-led) ── */}
      <section className="md:pt-12 md:pb-0 md:px-16 max-md:pt-10 max-md:pb-0 max-md:px-6">
        <FadeUp className="max-w-3xl mx-auto text-center" style={{ marginBottom: 48 }}>
          <Eyebrow>Unified Knowledge</Eyebrow>
          <GoldDivider />
          <SectionHeading>Uniting fragmented institutional data<br />into a single knowledge graph</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 20 }}>
            Students, courses, occupations, and employers exist in separate data sources across the ecosystem. Kallipolis connects them in a single graph — making relationships visible that no individual source can surface alone.
          </p>
        </FadeUp>

        <FadeUp delay={0.1} style={{ maxWidth: 1200, margin: "0 auto" }}>
          <UnifiedKnowledgeDiagram />
        </FadeUp>
      </section>

      {/* ── Section 4: Forward Deployment (prose-led) ── */}
      <section className="md:pt-12 md:pb-12 md:px-16 md:-mt-[260px] max-md:pt-2 max-md:pb-10 max-md:px-6 max-md:-mt-[80px]">
        <FadeUp className="max-w-2xl mx-auto text-center">
          <Eyebrow>Forward Deployment</Eyebrow>
          <GoldDivider />
          <SectionHeading>Limitations become invitations</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 24 }}>
            Student data is synthetic, not real enrollments. Catalog PDFs lag behind live curricula. Regional classifications don't always match a college's local reality. Public datasets don't offer a complete view of each employer.
          </p>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 16 }}>
            Each of these limitations is an invitation to collaborate. The system is architected for institutional partnership. Direct MIS feeds replace synthetic students. Curriculum API access makes courses real-time. Local industry contacts validate employer readiness. Forward-deployment into the institution closes the gaps that distance creates.
          </p>
        </FadeUp>
      </section>

      {/* ── Section 5: Cross-links ── */}
      <FadeUp className="bg-[#060d1f] flex justify-center md:pt-6 md:pb-12 md:px-16 md:gap-4 max-md:pt-6 max-md:pb-10 max-md:px-4 max-md:gap-3 max-md:flex-wrap">
        <ActionBadge label="Home" neonColor="#f5e6c8" opacity={1} icon="sun" inline href="/#methodology" invertHover />
        <ActionBadge label="Explore Atlas" neonColor="#f0425e" opacity={1} icon="cube" inline href="/atlas" invertHover />
        <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline href="/partnerships" invertHover />
      </FadeUp>
    </>
  );
}
