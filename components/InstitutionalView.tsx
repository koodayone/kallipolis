import InstitutionalDiagram from "./InstitutionalDiagram";

const points = [
  { label: "Scale", text: "Largest system of higher education in the United States." },
  { label: "Centrality", text: "Connects industry, government, and the local workforce." },
  { label: "Positioning", text: "Kallipolis spreads intelligence across the ecosystem." },
];

export default function InstitutionalView() {
  return (
    <section className="bg-redwood-green" style={{ paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 0 }}>

      {/* Top block */}
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <p style={{ fontSize: 11, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
          The Institutional View
        </p>
        <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
        <h2 style={{ fontSize: 36, fontWeight: 700, lineHeight: 1.15, letterSpacing: "-0.02em", color: "white", margin: 0 }}>
          Community colleges are central to<br />workforce development.
        </h2>
      </div>

      {/* Bottom block */}
      <div style={{ display: "flex", gap: 48, alignItems: "stretch", paddingBottom: 64 }}>

        {/* Left column — points */}
        <div style={{ flex: "0 0 35%", display: "flex", flexDirection: "column", gap: 30, justifyContent: "center", alignSelf: "center" }}>
          {points.map((point) => (
            <div
              key={point.label}
              style={{
                borderLeft: "2px solid rgba(255,255,255,0.2)",
                paddingLeft: 16,
                display: "flex",
                flexDirection: "column",
                gap: 5,
              }}
            >
              <p style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#FFCC33", opacity: 0.85, margin: 0 }}>
                {point.label}
              </p>
              <p style={{ fontSize: 16, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                {point.text}
              </p>
            </div>
          ))}
        </div>

        {/* Right column — Three.js diagram */}
        <div style={{ flex: 1, minHeight: 300, borderRadius: 10, overflow: "hidden" }}>
          <InstitutionalDiagram />
        </div>
      </div>
    </section>
  );
}
