import { FADE_DURATION } from "../lib/collegeRotation";

type Props = {
  label?: string;
  neonColor: string;
  opacity: number;
  icon?: "cube" | "lightbulb";
};

function CubeIcon({ color }: { color: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={color} opacity="0.85" />
      <path d="M12 13v9l9-5.5v-9L12 13z" fill={color} opacity="0.55" />
      <path d="M12 13v9L3 16.5v-9L12 13z" fill={color} opacity="0.4" />
      <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
    </svg>
  );
}

function LightbulbIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="2 2 20 20" fill="none">
      <path d="M12 2 L13 10 L12 9 L11 10 Z" fill={color} />
      <path d="M12 22 L13 14 L12 15 L11 14 Z" fill={color} />
      <path d="M2 12 L10 11 L9 12 L10 13 Z" fill={color} />
      <path d="M22 12 L14 11 L15 12 L14 13 Z" fill={color} />
      <circle cx="12" cy="12" r="2" fill={color} />
      <line x1="5" y1="5" x2="9" y2="9" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="19" y1="5" x2="15" y2="9" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="5" y1="19" x2="9" y2="15" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="19" y1="19" x2="15" y2="15" stroke={color} strokeWidth="1" opacity="0.8" />
    </svg>
  );
}

export default function ExploreOntology({ label = "Explore Ontology", neonColor, opacity, icon = "cube" }: Props) {
  return (
    <section style={{ background: "#060d1f", padding: "0 64px 24px", textAlign: "center" }}>
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 18px",
          border: `1px solid ${neonColor}`,
          borderRadius: 6,
          cursor: "default",
          opacity,
          transition: `opacity ${FADE_DURATION}ms ease, border-color ${FADE_DURATION}ms ease`,
        }}
      >
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: neonColor,
            transition: `color ${FADE_DURATION}ms ease`,
          }}
        >
          {label}
        </span>
        {icon === "cube" ? <CubeIcon color={neonColor} /> : <LightbulbIcon color={neonColor} />}
      </div>
    </section>
  );
}
