const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const EMPLOYERS = [
  { name: "Pacific Precision Manufacturing", sector: "Aerospace Components", roles: 12, skills: 18 },
  { name: "Central Valley Fabrication", sector: "Industrial Metalwork", roles: 8, skills: 14 },
  { name: "Sierra Machining Group", sector: "Contract Manufacturing", roles: 6, skills: 11 },
  { name: "Valley Medical Center", sector: "Healthcare", roles: 9, skills: 9 },
];

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.2 }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function DemoEmployers() {
  const grid = "24px 1fr 160px 50px 80px";

  return (
    <div>
      {/* Column headers */}
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Employer</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Sector</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "center" }}>Roles</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Skills</span>
      </div>

      {/* Rows */}
      {EMPLOYERS.map((emp, i) => (
        <div
          key={emp.name}
          style={{
            display: "grid",
            gridTemplateColumns: grid,
            alignItems: "center",
            padding: "12px 16px",
            background: "rgba(255,255,255,0.03)",
            borderBottom: i < EMPLOYERS.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
          }}
        >
          <Chevron />
          <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{emp.name}</span>
          <span style={{ fontFamily: FONT, fontSize: 12, color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{emp.sector}</span>
          <span style={{ fontFamily: FONT, fontSize: 12, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>{emp.roles}</span>
          <span style={{
            fontFamily: FONT, fontSize: 11, color: ACCENT,
            background: `${ACCENT}20`, border: `1px solid ${ACCENT}30`,
            borderRadius: 100, padding: "3px 8px", textAlign: "center", whiteSpace: "nowrap",
          }}>
            {emp.skills} skills
          </span>
        </div>
      ))}
    </div>
  );
}
