import TwoFormsDiagram from "./TwoFormsDiagram";
import ActionBadge from "./ActionBadge";

const points = [
  { label: "Generative Proposals", text: "Generate intelligent partnership proposals adhering to Strong Workforce Program standards." },
  { label: "Regional Engagement", text: "Align employer-specific partnerships with regional SWP development plans." },
  { label: "Labor Market Integration", text: "Instantly identify TOP codes, SOC mappings, supply-demand gaps, and quantifiable student impact." },
];

export default function PartnershipsSection() {
  return (
    <section style={{ backgroundColor: "#060d1f", paddingTop: 40, paddingLeft: 64, paddingRight: 64, paddingBottom: 0 }}>

      <div style={{ display: "flex", gap: 48, alignItems: "stretch", paddingBottom: 64 }}>

        {/* Left column — header + points */}
        <div style={{ flex: "0 0 42%", display: "flex", flexDirection: "column", gap: 24, justifyContent: "center", alignSelf: "center" }}>

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
              Intelligent Partnerships
            </p>
            <div style={{ width: 64, height: 2, background: "#4fd1fd", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
            <h2 className="text-[22px] md:text-[28px] leading-[1.15] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              Drive partnerships that advance a<br />Strong Workforce.
            </h2>
          </div>
          {points.map((point) => (
            <div
              key={point.label}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 5,
              }}
            >
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#4fd1fd", opacity: 0.85, margin: 0 }}>
                {point.label}
              </p>
              <p style={{ fontSize: 15, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                {point.text}
              </p>
            </div>
          ))}
        </div>

        {/* Right column — Three.js diagram + badge */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ minHeight: 280, borderRadius: 10, overflow: "hidden" }}>
            <TwoFormsDiagram />
          </div>
          <div style={{ textAlign: "center", marginTop: -40 }}>
            <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline />
          </div>
        </div>
      </div>
    </section>
  );
}
