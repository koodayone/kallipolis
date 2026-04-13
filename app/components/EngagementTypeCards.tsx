const BRAND = "#b0a0ff";

const TYPES = [
  {
    label: "Internship Pipeline",
    description: "Structured on-site work experience connecting students to real workplace environments. The standard pipeline: gather employer context, select a primary occupation, identify relevant curriculum and students, generate a placement-ready proposal.",
    distinguishing: "Direct path from skill alignment to workplace placement.",
  },
  {
    label: "Curriculum Co-Design",
    description: "Employer shapes program content by identifying curriculum gaps. Extends the standard pipeline with a gap skill identification step — the system finds one skill the employer needs that the curriculum does not yet develop, and proposes how to close it.",
    distinguishing: "Adds gap skill identification and remediation strategy.",
  },
  {
    label: "Advisory Board",
    description: "Ongoing strategic guidance from industry into institutional planning. Selects multiple identity-defining occupations, synthesizes an advisory thesis explaining why the employer's perspective matters, and generates inaugural board agenda topics.",
    distinguishing: "Multi-occupation selection, thesis synthesis, and agenda generation.",
  },
];

export default function EngagementTypeCards() {
  return (
    <div style={{ display: "flex", gap: 20, maxWidth: 960, margin: "0 auto" }}>
      {TYPES.map((type) => (
        <div
          key={type.label}
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            padding: "24px 20px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {/* Type badge */}
          <span style={{
            alignSelf: "flex-start",
            padding: "4px 12px", borderRadius: 100,
            fontSize: 11, fontWeight: 600, letterSpacing: "0.05em",
            background: `${BRAND}20`, color: BRAND, border: `1px solid ${BRAND}40`,
          }}>
            {type.label}
          </span>

          {/* Description */}
          <p style={{ fontSize: 14, lineHeight: 1.65, color: "rgba(255,255,255,0.6)", margin: 0, flex: 1 }}>
            {type.description}
          </p>

          {/* Distinguishing feature */}
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
            <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, display: "block", marginBottom: 4 }}>
              Distinguishing feature
            </span>
            <p style={{ fontSize: 13, lineHeight: 1.5, color: "rgba(255,255,255,0.5)", margin: 0 }}>
              {type.distinguishing}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
