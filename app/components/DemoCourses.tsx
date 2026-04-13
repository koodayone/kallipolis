const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const DEPARTMENTS = [
  {
    name: "Manufacturing Technology",
    count: 5,
    expanded: true,
    courses: [
      { code: "MFGT 110", name: "Introduction to Manufacturing Processes" },
      { code: "MFGT 145", name: "Industrial Safety and Quality Control" },
      { code: "MFGT 210", name: "Computer-Aided Manufacturing" },
    ],
  },
  {
    name: "Welding Technology",
    count: 3,
    expanded: false,
    courses: [],
  },
];

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="12" height="12" viewBox="0 0 12 12" fill="none"
      style={{ opacity: 0.2, transform: open ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}
    >
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function DemoCourses() {
  const grid = "24px 1fr auto";

  return (
    <div>
      {/* Column headers */}
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Department</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
      </div>

      {/* Department rows */}
      {DEPARTMENTS.map((dept, di) => (
        <div key={dept.name}>
          {/* Department header */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: grid,
              alignItems: "center",
              padding: "14px 16px",
              background: dept.expanded ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.03)",
              borderBottom: !dept.expanded && di < DEPARTMENTS.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
            }}
          >
            <Chevron open={dept.expanded} />
            <span style={{ fontFamily: FONT, fontSize: 14, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{dept.name}</span>
            <span style={{ fontFamily: FONT, fontSize: 12, color: "rgba(255,255,255,0.4)", textAlign: "right" }}>{dept.count} courses</span>
          </div>

          {/* Nested course rows */}
          {dept.expanded && dept.courses.map((course, ci) => (
            <div
              key={course.code}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 12px 10px 40px",
                background: "rgba(255,255,255,0.02)",
                borderBottom: ci < dept.courses.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "1px solid rgba(255,255,255,0.05)",
              }}
            >
              <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 600, color: ACCENT, flexShrink: 0 }}>{course.code}</span>
              <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.75)" }}>{course.name}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
