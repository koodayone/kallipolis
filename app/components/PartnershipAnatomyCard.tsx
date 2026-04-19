const BRAND = "#4fd1fd";

// ── Shared helpers ───────────────────────────────────────────────────────

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      padding: "20px 24px", background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8,
    }}>
      {children}
    </div>
  );
}

function Chevron({ open = false }: { open?: boolean }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
      style={{ opacity: open ? 0.5 : 0.2, transform: open ? "rotate(90deg)" : "none", transition: "transform 0.3s ease, opacity 0.3s ease" }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SkillCheckmark() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="6" cy="6" r="5" stroke={BRAND} strokeWidth="1" />
      <path d="M4 6l1.5 1.5L8 5" stroke={BRAND} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function GridHeaders({ labels, template }: { labels: { text: string; primary?: boolean; align?: string }[]; template: string }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: template, padding: "8px 12px", borderBottom: `1px solid ${BRAND}20` }}>
      {labels.map((l) => (
        <span key={l.text || "spacer"} style={{
          fontSize: 9, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.1em",
          color: l.primary ? BRAND : `${BRAND}90`,
          textAlign: (l.align as "left" | "right" | "center") || "left",
        }}>
          {l.text}
        </span>
      ))}
    </div>
  );
}

function SkillPill({ count }: { count: number }) {
  return (
    <span style={{
      fontSize: 10, color: BRAND, background: `${BRAND}20`,
      border: `1px solid ${BRAND}30`, borderRadius: 100,
      padding: "3px 8px", textAlign: "center", whiteSpace: "nowrap",
      textTransform: "uppercase", letterSpacing: "0.05em",
    }}>
      {count} Skills
    </span>
  );
}

function DerivedSkillPill({ name }: { name: string }) {
  return (
    <span style={{
      padding: "4px 10px", border: `1px solid ${BRAND}60`,
      borderRadius: 6, fontSize: 11, fontWeight: 500, color: BRAND,
    }}>
      {name}
    </span>
  );
}

function expandState(progress: number) {
  const expanded = progress > 0.35;
  const opacity = expanded ? Math.min(1, (progress - 0.35) / 0.15) : 0;
  return { expanded, opacity };
}

// ── Step 01: Employer Landscape ──────────────────────────────────────────

const EMPLOYERS = [
  { name: "Golden State Solar", sector: "Renewable Energy", roles: 11, skills: 15 },
  { name: "Sierra Grid Electric", sector: "Energy & Utilities", roles: 14, skills: 18 },
  { name: "Central Valley Mechanical", sector: "Construction", roles: 9, skills: 12 },
  { name: "Pacific Infrastructure Group", sector: "Construction", roles: 7, skills: 10 },
];

const EXPANDED_EMPLOYER = {
  description: "Residential and commercial solar installation and maintenance provider operating across Central California.",
  occupation: {
    title: "Solar Photovoltaic Installers",
    wage: 47670,
    description: "Assemble, install, and maintain solar photovoltaic systems on rooftops and other structures.",
    skills: [
      { skill: "Solar Installation", course: "ENRG 201, ENRG 210" },
      { skill: "Photovoltaic Systems", course: "ENRG 145, ENRG 150" },
      { skill: "Electrical Safety", course: "ELEC 101, CNST 110" },
    ],
  },
};

export function EmployerLandscapeBand({ expandProgress = 0 }: { expandProgress?: number }) {
  const { expanded, opacity: accordionOpacity } = expandState(expandProgress);
  const GRID = "24px 1.2fr 1fr 50px 85px";

  return (
    <Card>
      <GridHeaders template={GRID} labels={[
        { text: "", primary: false },
        { text: "Employer", primary: true },
        { text: "Sector" },
        { text: "Roles", align: "center" },
        { text: "Skills", align: "right" },
      ]} />

      {EMPLOYERS.map((e, i) => {
        const isTarget = i === 0;
        const isDimmed = expanded && !isTarget;
        return (
          <div key={e.name} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
            <div style={{
              display: "grid", gridTemplateColumns: GRID, alignItems: "center",
              padding: "10px 12px",
              background: expanded && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
              boxShadow: expanded && isTarget ? `0 0 12px 2px ${BRAND}30, inset 0 0 0 1px ${BRAND}25` : "none",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
              borderRadius: expanded && isTarget ? 4 : 0,
              transition: "background 0.3s ease, box-shadow 0.5s ease",
            }}>
              <Chevron open={isTarget && expanded} />
              <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.85)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.name}</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.sector}</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>{e.roles}</span>
              <SkillPill count={e.skills} />
            </div>

            {isTarget && (
              <div style={{ maxHeight: expanded ? 700 : 0, opacity: accordionOpacity, overflow: "hidden", transition: "max-height 0.3s ease, opacity 0.3s ease" }}>
                <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                  <p style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", lineHeight: 1.55, margin: "0 0 12px" }}>{EXPANDED_EMPLOYER.description}</p>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 10px", borderRadius: 100, fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.12)", marginBottom: 12 }}>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
                    Employer Home Page
                  </span>
                  <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)", display: "block", marginBottom: 8 }}>Employer Occupations (1)</span>
                  <div style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: "14px 16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: "#f0eef4" }}>{EXPANDED_EMPLOYER.occupation.title}</span>
                      <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.55)" }}>${EXPANDED_EMPLOYER.occupation.wage.toLocaleString()} annual</span>
                    </div>
                    <p style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", lineHeight: 1.5, margin: "6px 0 10px" }}>{EXPANDED_EMPLOYER.occupation.description}</p>
                    <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}99`, display: "block", marginBottom: 6 }}>Aligned Skills ({EXPANDED_EMPLOYER.occupation.skills.length})</span>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {EXPANDED_EMPLOYER.occupation.skills.map((s) => (
                        <div key={s.skill} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                          <SkillCheckmark />
                          <span style={{ fontSize: 12, color: BRAND }}>{s.skill}</span>
                          <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginLeft: "auto" }}>{s.course}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </Card>
  );
}

// ── Step 02: Occupational Demand ─────────────────────────────────────────

const OCCUPATIONS = [
  { title: "Solar Photovoltaic Installers", wage: "$47,670", openings: "280/yr", growth: "+22.3%" },
  { title: "Electricians", wage: "$82,340", openings: "340/yr", growth: "+8.2%" },
  { title: "Construction Managers", wage: "$105,640", openings: "180/yr", growth: "+7.1%" },
];

const EXPANDED_OCCUPATION = {
  soc: "47-2231",
  description: "Assemble, install, and maintain solar photovoltaic systems on rooftops and other structures.",
  skills: [
    { skill: "Solar Installation", course: "ENRG 201, ENRG 210" },
    { skill: "Photovoltaic Systems", course: "ENRG 145, ENRG 150" },
    { skill: "Electrical Safety", course: "ELEC 101, CNST 110" },
  ],
  region: "Central Valley / Mother Lode",
  employed: "1,840",
};

export function OccupationalDemandBand({ expandProgress = 0 }: { expandProgress?: number }) {
  const { expanded, opacity: accordionOpacity } = expandState(expandProgress);
  const GRID = "24px 1fr 80px 60px 70px";

  return (
    <Card>
      <GridHeaders template={GRID} labels={[
        { text: "", primary: false },
        { text: "Occupation", primary: true },
        { text: "Wage", align: "right" },
        { text: "Openings", align: "right" },
        { text: "Growth", align: "right" },
      ]} />

      {OCCUPATIONS.map((o, i) => {
        const isTarget = i === 0;
        const isDimmed = expanded && !isTarget;
        return (
          <div key={o.title} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
            <div style={{
              display: "grid", gridTemplateColumns: GRID, alignItems: "center",
              padding: "10px 12px",
              background: expanded && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
              boxShadow: expanded && isTarget ? `0 0 12px 2px ${BRAND}30, inset 0 0 0 1px ${BRAND}25` : "none",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
              borderRadius: expanded && isTarget ? 4 : 0,
              transition: "background 0.3s ease, box-shadow 0.5s ease",
            }}>
              <Chevron open={isTarget && expanded} />
              <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{o.title}</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", textAlign: "right" }}>{o.wage}</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{o.openings}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: "#4ade80", textAlign: "right" }}>{o.growth}</span>
            </div>

            {isTarget && (
              <div style={{ maxHeight: expanded ? 700 : 0, opacity: accordionOpacity, overflow: "hidden", transition: "max-height 0.3s ease, opacity 0.3s ease" }}>
                <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                  <p style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", margin: "0 0 4px" }}>SOC {EXPANDED_OCCUPATION.soc}</p>
                  <p style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: "0 0 14px" }}>{EXPANDED_OCCUPATION.description}</p>
                  <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}99`, display: "block", marginBottom: 6 }}>Aligned Skills ({EXPANDED_OCCUPATION.skills.length})</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 14 }}>
                    {EXPANDED_OCCUPATION.skills.map((s) => (
                      <div key={s.skill} style={{ display: "flex", alignItems: "center", gap: 7 }}>
                        <SkillCheckmark />
                        <span style={{ fontSize: 12, color: BRAND }}>{s.skill}</span>
                        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginLeft: "auto" }}>{s.course}</span>
                      </div>
                    ))}
                  </div>
                  <p style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", margin: 0 }}>
                    Regional Employment: {EXPANDED_OCCUPATION.region} — <strong style={{ color: "rgba(255,255,255,0.65)" }}>{EXPANDED_OCCUPATION.employed}</strong> currently employed
                  </p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </Card>
  );
}

// ── Step 03: Curriculum Alignment ────────────────────────────────────────

const DEPARTMENTS = [
  { name: "Energy Systems Technology", courses: 8 },
  { name: "Electrical Technology", courses: 10 },
  { name: "Construction Technology", courses: 5 },
];

const EXPANDED_COURSES = [
  {
    code: "ENRG 201", name: "Solar System Design & Installation",
    description: "Design, size, and install residential and commercial photovoltaic systems including panel layout, inverter selection, and grid interconnection. Emphasis on NEC Article 690 compliance and Cal/OSHA safety requirements.",
    skills: ["Solar Installation", "Photovoltaic Systems", "Electrical Safety"],
  },
  { code: "ENRG 145", name: "Photovoltaic Fundamentals", description: "Principles of photovoltaic energy conversion, solar cell technology, and system components.", skills: ["Photovoltaic Systems"] },
  { code: "ENRG 150", name: "Energy Storage & Grid Integration", description: "Battery storage systems, grid-tie inverters, and utility interconnection standards.", skills: ["Photovoltaic Systems"] },
  { code: "ENRG 101", name: "Introduction to Renewable Energy", description: "Survey of renewable energy technologies including solar, wind, and geothermal applications.", skills: ["Solar Installation"] },
];

export function CurriculumAlignmentBand({ expandProgress = 0 }: { expandProgress?: number }) {
  const { expanded, opacity: accordionOpacity } = expandState(expandProgress);
  const GRID = "24px 1fr auto";

  return (
    <Card>
      <GridHeaders template={GRID} labels={[
        { text: "", primary: false },
        { text: "Department", primary: true },
        { text: "Courses", align: "right" },
      ]} />

      {DEPARTMENTS.map((d, i) => {
        const isTarget = i === 0;
        const isDimmed = expanded && !isTarget;
        return (
          <div key={d.name} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
            <div style={{
              display: "grid", gridTemplateColumns: GRID, alignItems: "center",
              padding: "12px 12px",
              background: expanded && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.06)",
              boxShadow: expanded && isTarget ? `0 0 12px 2px ${BRAND}30, inset 0 0 0 1px ${BRAND}25` : "none",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
              borderRadius: expanded && isTarget ? 4 : 0,
              transition: "background 0.3s ease, box-shadow 0.5s ease",
            }}>
              <Chevron open={isTarget && expanded} />
              <span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{d.name}</span>
              <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textAlign: "right" }}>{d.courses} courses</span>
            </div>

            {isTarget && (
              <div style={{ maxHeight: expanded ? 900 : 0, opacity: accordionOpacity, overflow: "hidden", transition: "max-height 0.3s ease, opacity 0.3s ease" }}>
                {EXPANDED_COURSES.map((c, ci) => (
                  <div key={c.code}>
                    <div style={{
                      display: "flex", alignItems: "center", gap: 8,
                      padding: "9px 12px 9px 36px",
                      background: ci === 0 && expanded ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.02)",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                    }}>
                      <Chevron open={ci === 0 && expanded} />
                      <span style={{ fontSize: 11, fontWeight: 600, color: BRAND, flexShrink: 0 }}>{c.code}</span>
                      <span style={{ fontSize: 12, color: "rgba(255,255,255,0.75)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
                    </div>

                    {ci === 0 && expanded && (
                      <div style={{ padding: "14px 16px 18px 48px", background: "rgba(255,255,255,0.03)" }}>
                        <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, display: "block", marginBottom: 4 }}>Description</span>
                        <p style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6, margin: "0 0 12px" }}>{c.description}</p>
                        <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, display: "block", marginBottom: 6 }}>Derived Skills</span>
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          {c.skills.map((s) => <DerivedSkillPill key={s} name={s} />)}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </Card>
  );
}

// ── Step 04: Student Impact ──────────────────────────────────────────────

const STUDENTS = [
  { id: "#412", focus: "Energy Systems Technology", courses: 9, gpa: 3.72 },
  { id: "#738", focus: "Electrical Technology", courses: 11, gpa: 3.45 },
  { id: "#1055", focus: "Energy Systems Technology", courses: 8, gpa: 3.38 },
];

const EXPANDED_STUDENT_COURSES = [
  { code: "ENRG 201", name: "Solar System Design & Installation", grade: "A", term: "2025-Fall" },
  { code: "ENRG 150", name: "Energy Storage & Grid Integration", grade: "A", term: "2025-Spring" },
  { code: "ENRG 145", name: "Photovoltaic Fundamentals", grade: "B", term: "2025-Spring" },
  { code: "ELEC 101", name: "Fundamentals of Electricity", grade: "A", term: "2024-Fall" },
  { code: "ENRG 101", name: "Introduction to Renewable Energy", grade: "A", term: "2024-Fall" },
];

function gradeColor(grade: string) {
  if (grade === "A") return "#4ade80";
  if (grade === "B") return BRAND;
  return "#facc15";
}

function gpaColor(gpa: number) {
  if (gpa >= 3.5) return "#4ade80";
  if (gpa >= 2.5) return BRAND;
  return "#facc15";
}

export function StudentImpactBand({ expandProgress = 0 }: { expandProgress?: number }) {
  const { expanded, opacity: accordionOpacity } = expandState(expandProgress);
  const GRID = "24px 60px 1fr 60px 44px";

  return (
    <Card>
      <GridHeaders template={GRID} labels={[
        { text: "", primary: false },
        { text: "Student", primary: true },
        { text: "Primary Focus" },
        { text: "Courses", align: "right" },
        { text: "GPA", align: "right" },
      ]} />

      {STUDENTS.map((s, i) => {
        const isTarget = i === 0;
        const isDimmed = expanded && !isTarget;
        return (
          <div key={s.id} style={{ opacity: isDimmed ? 0.35 : 1, transition: "opacity 0.4s ease" }}>
            <div style={{
              display: "grid", gridTemplateColumns: GRID, alignItems: "center",
              padding: "10px 12px",
              background: expanded && isTarget ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
              boxShadow: expanded && isTarget ? `0 0 12px 2px ${BRAND}30, inset 0 0 0 1px ${BRAND}25` : "none",
              borderBottom: "1px solid rgba(255,255,255,0.05)",
              borderRadius: expanded && isTarget ? 4 : 0,
              transition: "background 0.3s ease, box-shadow 0.5s ease",
            }}>
              <Chevron open={isTarget && expanded} />
              <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>{s.id}</span>
              <span style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.focus}</span>
              <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{s.courses}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: gpaColor(s.gpa), textAlign: "right" }}>{s.gpa.toFixed(2)}</span>
            </div>

            {isTarget && (
              <div style={{ maxHeight: expanded ? 700 : 0, opacity: accordionOpacity, overflow: "hidden", transition: "max-height 0.3s ease, opacity 0.3s ease" }}>
                <div style={{ padding: "14px 16px 18px", background: "rgba(255,255,255,0.02)" }}>
                  <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: 12 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em",
                      color: BRAND, padding: "6px 14px",
                      borderBottom: `2px solid ${BRAND}`, marginBottom: -1,
                    }}>Course History</span>
                    <span style={{
                      fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em",
                      color: "rgba(255,255,255,0.3)", padding: "6px 14px",
                      borderBottom: "2px solid transparent", marginBottom: -1,
                    }}>Skill Profile</span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    {EXPANDED_STUDENT_COURSES.map((c) => (
                      <div key={c.code} style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 0" }}>
                        <span style={{ fontSize: 10, fontWeight: 600, color: BRAND, flexShrink: 0, width: 65 }}>{c.code}</span>
                        <span style={{ fontSize: 11, fontWeight: 500, color: "rgba(255,255,255,0.7)", flex: 1 }}>{c.name}</span>
                        <span style={{ fontSize: 11, fontWeight: 700, color: gradeColor(c.grade) }}>{c.grade}</span>
                        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", width: 60, textAlign: "right" }}>{c.term}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </Card>
  );
}

// ── Step 05: Supply-Demand Bridge ────────────────────────────────────────

export function SupplyDemandBridgeBand({ expandProgress = 0 }: { expandProgress?: number }) {
  const showBridge = expandProgress > 0.30;
  const bridgeOpacity = showBridge ? Math.min(1, (expandProgress - 0.30) / 0.12) : 0;

  return (
    <Card>
      {/* Phase 1: Narrative — always visible */}
      <div style={{ marginBottom: 20 }}>
        <span style={{
          fontSize: 9, fontWeight: 600, textTransform: "uppercase",
          letterSpacing: "0.1em", color: BRAND,
          display: "block", marginBottom: 10,
        }}>
          Partnership Narrative
        </span>
        <p style={{ fontSize: 13, color: "rgba(255,255,255,0.6)", lineHeight: 1.7, margin: 0 }}>
          Golden State Solar&apos;s residential and commercial installation operations position it as a strong partnership candidate. The Central Valley has accelerating demand for solar photovoltaic installers driven by California&apos;s clean energy mandates. The Energy Systems Technology department develops the core competencies this occupation requires: solar installation, photovoltaic systems, and electrical safety. Occupational demand metrics from the Centers of Excellence indicate an unmet workforce gap of 232 on an annual basis.
        </p>
      </div>

      {/* Phase 2: SOC→TOP bridge — fades in at 0.30 */}
      <div style={{
        opacity: bridgeOpacity,
        maxHeight: showBridge ? 600 : 0,
        overflow: "hidden",
        transition: "opacity 0.3s ease, max-height 0.3s ease",
      }}>
        <GridHeaders template="90px 1fr 80px 100px 120px" labels={[
          { text: "SOC Code", primary: true },
          { text: "Occupation", primary: true },
          { text: "Region" },
          { text: "Wage", align: "right" },
          { text: "Annual Openings", align: "right" },
        ]} />
        <div style={{
          display: "grid", gridTemplateColumns: "90px 1fr 80px 100px 120px",
          padding: "10px 12px", background: "rgba(255,255,255,0.02)",
          borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 13,
        }}>
          <span style={{ color: "rgba(255,255,255,0.65)", fontFamily: "monospace", fontSize: 12 }}>47-2231</span>
          <span style={{ color: "rgba(255,255,255,0.85)" }}>Solar Photovoltaic Installers</span>
          <span style={{ color: "rgba(255,255,255,0.55)" }}>CVML</span>
          <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>$47,670</span>
          <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>280</span>
        </div>

        <div style={{ height: 12 }} />

        <GridHeaders template="90px 1fr 1fr 110px" labels={[
          { text: "TOP Code", primary: true },
          { text: "Program", primary: true },
          { text: "Award Level" },
          { text: "Annual Supply", align: "right" },
        ]} />
        <div style={{
          display: "grid", gridTemplateColumns: "90px 1fr 1fr 110px",
          padding: "10px 12px", background: "rgba(255,255,255,0.02)",
          borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 13,
        }}>
          <span style={{ color: "rgba(255,255,255,0.55)", fontFamily: "monospace", fontSize: 12 }}>094500</span>
          <span style={{ color: "rgba(255,255,255,0.75)" }}>Energy Systems Technology</span>
          <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>Associate Degree</span>
          <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>48</span>
        </div>

        <div style={{ padding: "20px 16px 16px" }}>
          {/* Openings bar */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(255,255,255,0.35)", width: 70, flexShrink: 0 }}>Openings</span>
            <div style={{ flex: 1, height: 24, background: "rgba(255,255,255,0.06)", borderRadius: 4, position: "relative", overflow: "hidden" }}>
              <div style={{ width: "100%", height: "100%", background: "rgba(255,255,255,0.12)", borderRadius: 4 }} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: "rgba(255,255,255,0.75)", width: 36, textAlign: "right", flexShrink: 0 }}>280</span>
          </div>

          {/* Supply bar */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, width: 70, flexShrink: 0 }}>Supply</span>
            <div style={{ flex: 1, height: 24, background: "rgba(255,255,255,0.06)", borderRadius: 4, position: "relative", overflow: "hidden" }}>
              <div style={{ width: `${(48 / 280) * 100}%`, height: "100%", background: BRAND, borderRadius: "4px 0 0 4px", boxShadow: `0 0 12px ${BRAND}30` }} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: BRAND, width: 36, textAlign: "right", flexShrink: 0 }}>48</span>
          </div>

          {/* Gap indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ width: 70, flexShrink: 0 }} />
            <div style={{ flex: 1, position: "relative" }}>
              <div style={{
                position: "absolute",
                left: `${(48 / 280) * 100}%`,
                right: 0,
                top: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}>
                <div style={{ width: "100%", height: 2, background: `${BRAND}40`, borderRadius: 1 }} />
                <div style={{ marginTop: 8, textAlign: "center" }}>
                  <span style={{ fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}80`, display: "block", marginBottom: 2 }}>Workforce Gap</span>
                  <span style={{ fontSize: 28, fontWeight: 700, color: BRAND, filter: `drop-shadow(0 0 10px ${BRAND}50)`, lineHeight: 1 }}>+232</span>
                </div>
              </div>
            </div>
            <span style={{ width: 36, flexShrink: 0 }} />
          </div>

          <div style={{ height: 60 }} />
        </div>
      </div>
    </Card>
  );
}
