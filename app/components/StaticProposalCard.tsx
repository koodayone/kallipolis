import { SAMPLE_PROPOSAL } from "../lib/sampleProposal";

const FONT = "var(--font-geist), system-ui, sans-serif";
const BRAND = "#b0a0ff";

function SectionHeader({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <span style={{
      fontFamily: FONT, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em",
      textTransform: "uppercase", color: color || "rgba(255,255,255,0.3)",
      display: "block", marginBottom: 10,
    }}>
      {children}
    </span>
  );
}

function ColumnRow({ cells, template }: { cells: React.ReactNode[]; template: string }) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: template,
      padding: "10px 16px", background: "rgba(255,255,255,0.02)",
      borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 13,
    }}>
      {cells}
    </div>
  );
}

function ColumnHeaders({ labels, template }: { labels: { text: string; align?: string }[]; template: string }) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns: template,
      padding: "8px 16px", borderBottom: `1px solid ${BRAND}20`,
    }}>
      {labels.map((l) => (
        <span key={l.text} style={{
          fontSize: 10, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.1em", color: "rgba(255,255,255,0.25)",
          textAlign: (l.align as "left" | "right") || "left",
        }}>
          {l.text}
        </span>
      ))}
    </div>
  );
}

export default function StaticProposalCard() {
  const p = SAMPLE_PROPOSAL;

  return (
    <div style={{
      padding: 28, background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8,
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h3 style={{ fontFamily: FONT, fontSize: 17, fontWeight: 600, color: "rgba(255,255,255,0.9)", margin: 0 }}>
          {p.employer}
        </h3>
        <span style={{
          padding: "4px 12px", borderRadius: 100, fontSize: 11, fontWeight: 600,
          letterSpacing: "0.05em", background: `${BRAND}20`, color: BRAND, border: `1px solid ${BRAND}40`,
        }}>
          {p.partnership_type}
        </span>
      </div>

      {/* Opportunity */}
      <div style={{ marginBottom: 24 }}>
        <SectionHeader>Opportunity</SectionHeader>
        <p style={{ fontFamily: FONT, fontSize: 14, color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
          {p.opportunity}
        </p>
        <div style={{ marginTop: 12 }}>
          <ColumnHeaders
            labels={[
              { text: "Occupation" },
              { text: "Wage", align: "right" },
              { text: "Openings", align: "right" },
              { text: "Growth", align: "right" },
            ]}
            template="1fr 100px 80px 100px"
          />
          {p.opportunity_evidence.map((occ) => (
            <ColumnRow
              key={occ.soc_code}
              template="1fr 100px 80px 100px"
              cells={[
                <span key="t" style={{ color: "rgba(255,255,255,0.7)" }}>{occ.title}</span>,
                <span key="w" style={{ color: "rgba(255,255,255,0.6)", textAlign: "right" }}>${(occ.annual_wage / 1000).toFixed(0)}k</span>,
                <span key="o" style={{ color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{occ.annual_openings.toLocaleString()}</span>,
                <span key="g" style={{ color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{occ.growth_rate}%</span>,
              ]}
            />
          ))}
        </div>
      </div>

      {/* Curriculum Alignment */}
      <div style={{ marginBottom: 24 }}>
        <SectionHeader>Curriculum Alignment</SectionHeader>
        <p style={{ fontFamily: FONT, fontSize: 14, color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
          {p.justification.curriculum_composition}
        </p>
        <div style={{ marginTop: 12 }}>
          <ColumnHeaders
            labels={[{ text: "Department" }, { text: "Courses", align: "right" }]}
            template="1fr auto"
          />
          {p.justification.curriculum_evidence.map((dept) => (
            <ColumnRow
              key={dept.department}
              template="1fr auto"
              cells={[
                <span key="d" style={{ color: "rgba(255,255,255,0.7)" }}>{dept.department}</span>,
                <span key="c" style={{ color: "rgba(255,255,255,0.5)", textAlign: "right" }}>{dept.courses.length}</span>,
              ]}
            />
          ))}
        </div>
      </div>

      {/* Student Pipeline */}
      <div style={{ marginBottom: 24 }}>
        <SectionHeader>Student Pipeline</SectionHeader>
        <p style={{ fontFamily: FONT, fontSize: 14, color: "rgba(255,255,255,0.65)", lineHeight: 1.65, margin: 0 }}>
          {p.justification.student_composition}
        </p>
        <div style={{
          marginTop: 12, background: "rgba(255,255,255,0.03)",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, padding: "16px 0" }}>
            <span style={{ fontFamily: FONT, fontSize: 20, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
              {p.justification.student_evidence.total_in_program.toLocaleString()}
            </span>
            <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
              Students in Aligned Programs
            </span>
          </div>
        </div>
      </div>

      {/* Roadmap */}
      <div>
        <SectionHeader>Roadmap</SectionHeader>
        <p style={{ fontFamily: FONT, fontSize: 14, color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
          {p.roadmap}
        </p>
      </div>
    </div>
  );
}
