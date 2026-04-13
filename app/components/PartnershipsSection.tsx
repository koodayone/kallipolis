import TwoFormsDiagram from "./TwoFormsDiagram";

const points = [
  { label: "Generative Proposals", text: "Draft intelligent partnership proposals justified by Strong Workforce standards." },
  { label: "Tailored Engagement", text: "Generate employer-specific narratives for internship pipelines, advisory boards, and curriculum co-design." },
  { label: "Labor Market Integration", text: "Instantaneously identify TOP codes, SOC mappings, supply-demand gaps, and quantifiable student impact relevant to industry partnerships." },
];

export default function PartnershipsSection() {
  return (
    <section style={{ backgroundColor: "#060d1f", paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 0 }}>

      <div style={{ display: "flex", gap: 48, alignItems: "stretch", paddingBottom: 64 }}>

        {/* Left column — Three.js diagram */}
        <div style={{ flex: "0 0 45%", minHeight: 300, borderRadius: 10, overflow: "hidden" }}>
          <TwoFormsDiagram />
        </div>

        {/* Right column — header + points */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 30, justifyContent: "center", alignSelf: "center" }}>

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
              Intelligent Partnerships
            </p>
            <div style={{ width: 64, height: 2, background: "#b0a0ff", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
            <h2 className="text-[22px] md:text-[28px] leading-[1.15] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              Data-driven partnerships compliant with Strong Workforce.
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
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#b0a0ff", opacity: 0.85, margin: 0 }}>
                {point.label}
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                {point.text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
