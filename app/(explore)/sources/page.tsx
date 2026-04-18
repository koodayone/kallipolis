"use client";

import AuthorityCard from "../../components/AuthorityCard";
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
    intelligence: "Kallipolis models student populations that mirror real enrollment patterns reported by each institution. The system surfaces academic trajectories, program concentrations, and competency profiles. A coordinator can see not just how many students are in a program, but what skills they carry and how those skills align with regional employer demand.",
    methodology: "Student populations are synthetically generated and calibrated to DataMart's grade distributions by program area. Aggregate patterns — enrollment concentration, academic performance, program retention — match institutional reality by design. The methodology is a present-day commitment to privacy that the architecture is designed to outgrow through direct institutional partnership.",
  },
  {
    unitName: "Courses",
    authorityName: "College Curriculum Catalogs",
    logoPath: "/logos/colleges_combined_white.png",
    factory: createBookForm,
    demoScene: <DemoCourses />,
    authority: "Each college's course catalog is its curricular commitment — the institutional declaration of what it promises to teach, at what depth, with what outcomes. Kallipolis sources directly from the institution itself.",
    intelligence: "Every course is interpreted through a skills taxonomy that connects curriculum to labor market language. The system knows not just what courses exist, but what skills they develop and how those skills map to occupational demand. This bridge between education and industry is what makes partnership proposals empirically grounded rather than anecdotal.",
    methodology: "Course content is extracted from institutional catalog publications. Learning outcomes and course objectives are interpreted against a controlled skills vocabulary — skills are assigned from the taxonomy, not freely generated. This constraint ensures consistency across institutions and prevents the system from inventing competencies that don't exist in the curriculum.",
  },
  {
    unitName: "Occupations",
    authorityName: "Centers of Excellence",
    logoPath: "/logos/coe_logo_clean.png",
    factory: createHardhatForm,
    demoScene: <DemoOccupations />,
    authority: "The Centers of Excellence for Labor Market Research is the analytical arm of California's community college system. Its institutional purpose is to produce the labor market intelligence that workforce development decisions depend on. COE research is regionally calibrated to community college service areas.",
    intelligence: "For every region, Kallipolis surfaces the occupations that community colleges are positioned to serve — filtered to the credential range between a postsecondary certificate and a bachelor's degree. Each occupation carries regional wages, employment levels, growth projections, and annual openings.",
    methodology: "COE's regional demand data is filtered to the workforce-development band — the occupations where community college credentials are the pathway. Each occupation is assigned skills from the same controlled taxonomy used for courses, creating a shared vocabulary that makes skill gap identification possible. The system can identify not just what occupations exist, but which skills employers need that the curriculum does not yet develop.",
  },
  {
    unitName: "Employers",
    authorityName: "Employment Development Department",
    logoPath: "/logos/edd_logo_clean.png",
    factory: createSkyscraperForm,
    demoScene: <DemoEmployers />,
    authority: "The California Employment Development Department maintains employer records for every organization with payroll obligations in the state. These are verifiable, publicly maintained records that carry institutional legitimacy.",
    intelligence: "Kallipolis surfaces employers scoped to those community colleges can meaningfully engage — organizations with operational capacity for workforce partnerships. Each employer is connected to the occupations it hires for, the skills those roles require, and the curriculum that develops those skills. A coordinator sees not a list of companies, but a ranked landscape of partnership-ready organizations with empirical alignment scores.",
    methodology: "Employer records are filtered to organizations above a size threshold that ensures partnership capacity. Each employer is validated to have an active web presence and connected to relevant occupations through industry classification. The result is a curated set of real, verifiable organizations — a workforce development lens on the employers that matter for institutional action.",
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
            Students. Courses. Occupations. Employers.<br />Each unit of analysis traces to one authoritative institution.
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

      {/* ── Section 3: Pipeline (component-led) ── */}
      <section style={{ paddingTop: 48, paddingBottom: 0, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 48 }}>
          <Eyebrow>Unified Knowledge</Eyebrow>
          <GoldDivider />
          <SectionHeading>Uniting fragmented institutional data<br />into a single knowledge graph</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 20 }}>
            Students, courses, occupations, and employers exist in separate data sources across the ecosystem. Kallipolis connects them in a single graph — making relationships visible that no individual source can surface alone.
          </p>
        </div>

        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <UnifiedKnowledgeDiagram />
        </div>
      </section>

      {/* ── Section 4: Forward Deployment (prose-led) ── */}
      <section style={{ paddingTop: 48, paddingBottom: 48, paddingLeft: 64, paddingRight: 64, marginTop: -260 }}>
        <div className="max-w-2xl mx-auto text-center">
          <Eyebrow>Forward Deployment</Eyebrow>
          <GoldDivider />
          <SectionHeading>Limitations become invitations</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 24 }}>
            Student data is synthetic, not real enrollments. Catalog PDFs lag behind live curricula. Regional classifications don't always match a college's local reality. Public datasets don't offer a complete view of each employer.
          </p>
          <p style={{ fontSize: 16, lineHeight: 1.65, color: "rgba(255,255,255,0.55)", marginTop: 16 }}>
            Each of these limitations is an invitation to collaborate. The system is architected for institutional partnership. Direct MIS feeds replace synthetic students. Curriculum API access makes courses real-time. Local industry contacts validate employer readiness. Forward-deployment into the institution closes the gaps that distance creates.
          </p>
        </div>
      </section>

      {/* ── Section 5: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Atlas" neonColor="#f0425e" opacity={1} icon="cube" inline href="/atlas" invertHover />
        <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline href="/partnerships" invertHover />
      </section>
    </>
  );
}
