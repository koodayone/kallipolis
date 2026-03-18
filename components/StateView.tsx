import CaliforniaMap from "./CaliforniaMap";

const points = [
  { label: "Statewide Vision", text: "Kallipolis empowers California Community Colleges to serve 2 million students in every region of the state." },
  { label: "Our Software", text: "We unify data & spread intelligence across the ecosystem by deploying AI for empowering workforce development initiatives." },
];

export default function StateView() {
  return (
    <section className="bg-deep-charcoal" style={{ paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 64 }}>
      <div style={{ display: "flex", gap: 48, alignItems: "stretch" }}>

        {/* Left column — California map */}
        <div style={{ flex: "0 0 35%", minHeight: 400, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <CaliforniaMap />
        </div>

        {/* Right column — text */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: 48 }}>

          {/* Header block — top */}
          <div style={{ textAlign: "center" }}>
            <p className="text-sm font-medium uppercase tracking-[0.15em] text-white/40" style={{ marginBottom: 16 }}>
              The State View
            </p>
            <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
            <h2 className="text-[28px] md:text-[36px] font-bold leading-[1.12] tracking-[-0.02em] text-white">
              116 schools. 73 districts. One intelligent network.
            </h2>
          </div>

          {/* Data points — bottom */}
          <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
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
                <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#FFCC33", opacity: 0.85, margin: 0 }}>
                  {point.label}
                </p>
                <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                  {point.text}
                </p>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
