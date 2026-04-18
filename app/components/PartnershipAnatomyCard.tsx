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

function SourceLine({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontSize: 12, color: "rgba(255,255,255,0.35)", fontStyle: "italic",
      margin: "12px 0 0", padding: "0 16px",
    }}>
      {children}
    </p>
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
  { name: "Sierra Grid Electric", sector: "Energy & Utilities", roles: 14, skills: 18 },
  { name: "Golden State Solar", sector: "Renewable Energy", roles: 9, skills: 12 },
  { name: "Central Valley Mechanical", sector: "Construction", roles: 11, skills: 15 },
  { name: "Pacific Infrastructure Group", sector: "Construction", roles: 7, skills: 10 },
];

const EXPANDED_EMPLOYER = {
  description: "Regional electrical contractor specializing in commercial and residential grid infrastructure across Central California.",
  occupation: {
    title: "Electricians",
    wage: 82340,
    description: "Install, maintain, and repair electrical wiring, equipment, and fixtures.",
    skills: [
      { skill: "Electrical Systems", course: "ELEC 101, ELEC 201" },
      { skill: "Circuit Design", course: "ELEC 145, ELEC 150" },
      { skill: "Safety Compliance", course: "CNST 110, ELEC 102" },
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
  { title: "Electricians", wage: "$82,340", openings: "340/yr", growth: "+8.2%" },
  { title: "HVAC Mechanics", wage: "$58,820", openings: "210/yr", growth: "+5.4%" },
  { title: "Construction Managers", wage: "$105,640", openings: "180/yr", growth: "+7.1%" },
];

const EXPANDED_OCCUPATION = {
  soc: "47-2111",
  description: "Install, maintain, and repair electrical wiring, equipment, and fixtures.",
  skills: [
    { skill: "Electrical Systems", course: "ELEC 101, ELEC 201" },
    { skill: "Circuit Design", course: "ELEC 145, ELEC 150" },
    { skill: "Safety Compliance", course: "CNST 110, ELEC 102" },
  ],
  region: "Central Valley / Mother Lode",
  employed: "3,140",
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
  { name: "Electrical Technology", courses: 10 },
  { name: "Construction Technology", courses: 7 },
  { name: "Environmental Control Technology", courses: 5 },
];

const EXPANDED_COURSES = [
  { code: "ELEC 101", name: "Fundamentals of Electricity", description: "Introduction to electrical theory, circuits, and safety practices for residential and commercial applications.", skills: ["Electrical Systems"] },
  { code: "ELEC 112", name: "Wiring Principles", description: "Hands-on training in wiring methods, conduit installation, and National Electrical Code compliance.", skills: ["Electrical Systems", "Safety Compliance"] },
  { code: "ELEC 145", name: "Residential Wiring", description: "Complete residential electrical installation including service entrance, branch circuits, and grounding systems.", skills: ["Circuit Design"] },
  { code: "ELEC 201", name: "Commercial Electrical Systems", description: "Advanced commercial and industrial electrical systems including three-phase power distribution.", skills: ["Electrical Systems", "Circuit Design"] },
  { code: "ELEC 295", name: "Electrical Code & Safety", description: "Comprehensive study of the National Electrical Code and Cal/OSHA electrical safety requirements.", skills: ["Safety Compliance"] },
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
  { id: "#412", focus: "Electrical Technology", courses: 11, gpa: 3.57 },
  { id: "#738", focus: "Construction Technology", courses: 9, gpa: 3.42 },
  { id: "#1055", focus: "Electrical Technology", courses: 10, gpa: 3.28 },
];

const EXPANDED_STUDENT_COURSES = [
  { code: "ELEC 201", name: "Commercial Electrical Systems", grade: "A", term: "2025-Fall" },
  { code: "ELEC 145", name: "Residential Wiring", grade: "A", term: "2025-Spring" },
  { code: "CNST 110", name: "Construction Safety", grade: "B", term: "2025-Spring" },
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
      {/* Headline metric */}
      <div style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.05)", marginBottom: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, padding: "16px 0" }}>
          <span style={{ fontSize: 20, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>428</span>
          <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>Students in Aligned Programs</span>
        </div>
      </div>

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
                  {/* Tab bar */}
                  <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: 12 }}>
                    <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: BRAND, padding: "6px 14px", borderBottom: `2px solid ${BRAND}`, marginBottom: -1 }}>Course History</span>
                    <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(255,255,255,0.3)", padding: "6px 14px", borderBottom: "2px solid transparent", marginBottom: -1 }}>Skill Profile</span>
                  </div>

                  {/* Course history */}
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

export function SupplyDemandBridgeBand() {
  return (
    <Card>
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
        <span style={{ color: "rgba(255,255,255,0.65)", fontFamily: "monospace", fontSize: 12 }}>47-2111</span>
        <span style={{ color: "rgba(255,255,255,0.85)" }}>Electricians</span>
        <span style={{ color: "rgba(255,255,255,0.55)" }}>CVML</span>
        <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>$82,340</span>
        <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>340</span>
      </div>

      <div style={{ height: 16 }} />

      <GridHeaders template="90px 1fr 1fr 110px" labels={[
        { text: "TOP Code", primary: true },
        { text: "Program", primary: true },
        { text: "Award Level" },
        { text: "Annual Supply", align: "right" },
      ]} />
      {[
        { top: "093400", program: "Electrical Technology", award: "Certificate (30<60 units)", supply: "42.33" },
        { top: "095200", program: "Construction Crafts Technology", award: "Associate Degree", supply: "8.67" },
        { top: "094600", program: "Environmental Control Technology (HVAC)", award: "Certificate (16<30 units)", supply: "15.00" },
      ].map((row) => (
        <div key={row.top} style={{
          display: "grid", gridTemplateColumns: "90px 1fr 1fr 110px",
          padding: "10px 12px", background: "rgba(255,255,255,0.02)",
          borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 13,
        }}>
          <span style={{ color: "rgba(255,255,255,0.55)", fontFamily: "monospace", fontSize: 12 }}>{row.top}</span>
          <span style={{ color: "rgba(255,255,255,0.75)" }}>{row.program}</span>
          <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>{row.award}</span>
          <span style={{ color: "rgba(255,255,255,0.65)", textAlign: "right" }}>{row.supply}</span>
        </div>
      ))}

      <div style={{ padding: "14px 16px", display: "flex", gap: 8, alignItems: "baseline" }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>Annual Openings: 340</span>
        <span style={{ color: "rgba(255,255,255,0.3)" }}>·</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>Annual Supply: 66</span>
        <span style={{ color: "rgba(255,255,255,0.3)" }}>·</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: "rgba(255,255,255,0.75)" }}>Gap: <span style={{ color: BRAND }}>+274</span></span>
      </div>

    </Card>
  );
}
