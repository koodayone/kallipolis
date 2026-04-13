import EpistemologySection from "../../components/EpistemologySection";
import DataAuthoritySection from "../../components/DataAuthoritySection";
import PipelineDiagram from "../../components/PipelineDiagram";
import ActionBadge from "../../components/ActionBadge";

// ── Section primitives ───────────────────────────────────────────────────────

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.4)", marginBottom: 16 }}>
      {children}
    </p>
  );
}

function GoldDivider() {
  return <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
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

// ── Data authority content ───────────────────────────────────────────────────

const AUTHORITIES = [
  {
    unitName: "Students",
    authorityName: "Chancellor's Office DataMart",
    logoPath: "/logos/chancellors_logo.png",
    whatData: "Four-digit TOP code grade distributions, enrollment shares by program area, term calendar patterns, and demographic breakdowns from the statewide Management Information Systems.",
    whatTransformation: "Synthetic student populations generated through a calibration model that reproduces real grade distributions, enrollment stickiness patterns (60% primary area retention), and program-level proportions. Each student receives a deterministic UUID and a competency portrait derived from their course history.",
    whyThisSource: "The Chancellor's Office DataMart is the canonical record of who enrolled, what they studied, and how they performed across the entire California Community College system. No other source has this scope or institutional authority.",
    limitation: "Student data is currently synthetic — calibrated to real distributions but not drawn from actual enrollment records.",
    invitation: "Direct MIS integration would replace synthetic records with actual enrollment data. This requires only a data-sharing agreement between Kallipolis and the participating institution, and the pipeline is already architected for this transition.",
  },
  {
    unitName: "Courses",
    authorityName: "College Curriculum Catalogs",
    logoPath: undefined,
    whatData: "Course names, codes, departments, unit counts, descriptions, prerequisites, learning outcomes, and course objectives extracted from institutional catalog PDFs.",
    whatTransformation: "PDF extraction recovers structured course records from unstructured catalog documents. Each course's learning outcomes are then interpreted through the unified skills taxonomy, producing skill graph edges that bridge curriculum to labor market demand.",
    whyThisSource: "The college's own catalog is its curricular commitment — the official declaration of what it promises to teach, at what depth, with what outcomes. No third-party source can substitute for this institutional self-description.",
    limitation: "Catalog PDFs lag behind live curricula. New courses, revised learning outcomes, and program changes may not appear until the next catalog publication cycle.",
    invitation: "API access to live curriculum management systems would make course data real-time. Several CMS platforms in use across the CCC system support structured exports — a partnership with the institution's curriculum office closes this gap directly.",
  },
  {
    unitName: "Occupations",
    authorityName: "Centers of Excellence",
    logoPath: "/logos/coe_logo_clean.png",
    whatData: "SOC-coded occupation records with annual wages, employment counts, five-year growth rates, annual openings, and education level requirements — organized by Centers of Excellence region.",
    whatTransformation: "A workforce-development band filter retains only occupations requiring education between a postsecondary certificate and a bachelor's degree — the credential range that community colleges serve. Regional demand signals are aggregated by COE region rather than by county, aligning with the system's own geographic logic.",
    whyThisSource: "Centers of Excellence research is regionally calibrated to CCC service areas, making it more relevant than national BLS or O*NET data. COE analysts interpret labor market data through a workforce development lens that mirrors the institutional perspective Kallipolis serves.",
    limitation: "COE regional granularity varies across the state. Some regions publish more detailed demand data than others, and update cycles differ.",
    invitation: "Collaboration with individual COE offices could refine demand signals with college-specific labor market intelligence — local employer relationships, advisory board insights, and regional economic development context that published data alone cannot capture.",
  },
  {
    unitName: "Employers",
    authorityName: "Employment Development Department",
    logoPath: "/logos/edd_logo_clean.png",
    whatData: "Employer records from the EDD ALMIS database, including organization names, NAICS industry codes, county-level location, and employee counts.",
    whatTransformation: "Employers are filtered to organizations with 100 or more employees — a size threshold that ensures operational capacity for workforce partnerships. A NAICS-to-SOC crosswalk connects each employer to the occupations it plausibly hires for. Organization names and descriptions are cleaned through an LLM pass to normalize formatting and fill descriptive gaps.",
    whyThisSource: "EDD maintains the state's authoritative employer records — verifiable, comprehensive, and publicly maintained. Unlike commercial databases, EDD data carries institutional legitimacy that matters in public-sector procurement contexts.",
    limitation: "EDD records capture registered employers, not hiring intent. An employer's presence in the database does not guarantee active recruitment or partnership readiness.",
    invitation: "Validation with local industry contacts — career services offices, advisory board members, workforce development boards — would surface which employers are actively engaged. Forward-deployment into the institution makes this validation a shared activity rather than a remote inference.",
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ExploreSourcesPage() {
  return (
    <>
      {/* ── Section 1: Hero ── */}
      <section style={{ paddingTop: 120, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center">
          <Eyebrow>The Epistemology</Eyebrow>
          <GoldDivider />
          <SectionHeading>
            Every claim has a public source.<br />Every source has a public institution.
          </SectionHeading>
          <p style={{ fontSize: 18, lineHeight: 1.6, color: "rgba(255,255,255,0.65)", marginTop: 24, maxWidth: 600, marginLeft: "auto", marginRight: "auto" }}>
            Kallipolis makes no claim it cannot ground in data from a named public institution. The four units of analysis — students, courses, occupations, employers — each trace to a specific institutional authority.
          </p>
        </div>
      </section>

      {/* ── Section 2: Epistemology Overview ── */}
      <EpistemologySection />

      {/* ── Sections 3-6: Data Authority Deep Dives ── */}
      <section style={{ paddingTop: 64, paddingBottom: 48, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 48 }}>
          <Eyebrow>The Four Authorities</Eyebrow>
          <GoldDivider />
          <SectionHeading>One institution per unit.<br />No exceptions.</SectionHeading>
        </div>

        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          {AUTHORITIES.map((auth) => (
            <DataAuthoritySection key={auth.unitName} {...auth} />
          ))}
        </div>
      </section>

      {/* ── Section 7: Pipeline Synthesis ── */}
      <section style={{ paddingTop: 48, paddingBottom: 64, paddingLeft: 64, paddingRight: 64 }}>
        <div className="max-w-3xl mx-auto text-center" style={{ marginBottom: 48 }}>
          <Eyebrow>The Pipeline</Eyebrow>
          <GoldDivider />
          <SectionHeading>From institutional data<br />to a unified knowledge graph</SectionHeading>
          <p style={{ fontSize: 16, lineHeight: 1.6, color: "rgba(255,255,255,0.55)", marginTop: 20 }}>
            Each data authority feeds a dedicated pipeline stage. The five stages converge in a single Neo4j graph where curriculum, labor market, and institutional data are connected through a shared skills vocabulary.
          </p>
        </div>

        <PipelineDiagram />
      </section>

      {/* ── Section 8: Cross-links ── */}
      <section style={{ background: "#060d1f", padding: "24px 64px 48px", display: "flex", justifyContent: "center", gap: 16 }}>
        <ActionBadge label="Explore Atlas" neonColor="#c9a84c" opacity={1} icon="cube" inline href="/atlas" />
        <ActionBadge label="Explore Partnerships" neonColor="#b0a0ff" opacity={1} icon="chainlink" inline href="/partnerships" />
      </section>
    </>
  );
}
