const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const STUDENTS = [
  { id: "#247", focus: "Industrial Technology", courses: 11, gpa: 3.91 },
  { id: "#312", focus: "CNC Machining", courses: 9, gpa: 3.62 },
  { id: "#089", focus: "Welding Technology", courses: 7, gpa: 2.84 },
  { id: "#501", focus: "Automotive Systems", courses: 5, gpa: 2.41 },
];

function gpaColor(gpa: number): string {
  if (gpa >= 3.5) return "rgba(74, 222, 128, 0.9)";
  if (gpa >= 2.5) return "rgba(96, 165, 250, 0.9)";
  return "rgba(251, 191, 36, 0.9)";
}

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.2 }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function DemoStudents() {
  const grid = "24px 80px 1fr 80px 50px";

  return (
    <div>
      {/* Column headers */}
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Student</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Primary Focus</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>GPA</span>
      </div>

      {/* Rows */}
      {STUDENTS.map((s, i) => (
        <div
          key={s.id}
          style={{
            display: "grid",
            gridTemplateColumns: grid,
            alignItems: "center",
            padding: "12px 16px",
            background: "rgba(255,255,255,0.03)",
            borderBottom: i < STUDENTS.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
          }}
        >
          <Chevron />
          <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>{s.id}</span>
          <span style={{ fontFamily: FONT, fontSize: 13, color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.focus}</span>
          <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{s.courses}</span>
          <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 700, color: gpaColor(s.gpa), textAlign: "right" }}>{s.gpa.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}
