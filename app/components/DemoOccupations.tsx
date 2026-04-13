const FONT = "var(--font-geist), system-ui, sans-serif";
const ACCENT = "#c9a84c";

const OCCUPATIONS = [
  { title: "Industrial Engineers", wage: 108200, openings: 340, growth: 6.4 },
  { title: "Machinists", wage: 58400, openings: 890, growth: 4.8 },
  { title: "CNC Tool Operators", wage: 52100, openings: 1240, growth: 5.2 },
  { title: "Welders & Cutters", wage: 47800, openings: 780, growth: 3.1 },
];

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.2 }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function DemoOccupations() {
  const grid = "24px 1fr 90px 70px 90px";

  return (
    <div>
      {/* Column headers */}
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span />
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Occupation</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Wage</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Openings</span>
        <span style={{ fontFamily: FONT, fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>5yr Growth</span>
      </div>

      {/* Rows */}
      {OCCUPATIONS.map((occ, i) => (
        <div
          key={occ.title}
          style={{
            display: "grid",
            gridTemplateColumns: grid,
            alignItems: "center",
            padding: "12px 16px",
            background: "rgba(255,255,255,0.03)",
            borderBottom: i < OCCUPATIONS.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
          }}
        >
          <Chevron />
          <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{occ.title}</span>
          <span style={{ fontFamily: FONT, fontSize: 12, color: "rgba(255,255,255,0.5)", textAlign: "right" }}>${occ.wage.toLocaleString()}</span>
          <span style={{ fontFamily: FONT, fontSize: 12, color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{occ.openings.toLocaleString()}/yr</span>
          <span style={{ fontFamily: FONT, fontSize: 12, fontWeight: 500, color: "#4ade80", textAlign: "right" }}>+{occ.growth}%</span>
        </div>
      ))}
    </div>
  );
}
