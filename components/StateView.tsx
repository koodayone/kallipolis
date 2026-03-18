import CaliforniaMap from "./CaliforniaMap";

export default function StateView() {
  return (
    <section className="bg-deep-charcoal" style={{ paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 64 }}>
      <div style={{ display: "flex", gap: 48, alignItems: "stretch" }}>

        {/* Left column — California map */}
        <div style={{ flex: "0 0 35%", minHeight: 400, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <CaliforniaMap />
        </div>

        {/* Right column — text */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <p className="text-xs font-medium uppercase tracking-[0.15em] text-white/40" style={{ marginBottom: 16 }}>
            The State View
          </p>
          <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, marginBottom: 24 }} />
          <h2 className="text-[36px] md:text-[48px] font-bold leading-[1.12] tracking-[-0.02em] text-white" style={{ marginBottom: 24 }}>
            116 schools. 73 districts. One intelligent network.
          </h2>
          <p className="text-lg font-normal leading-[1.6] tracking-normal text-white/60">
            California Community Colleges serve every region of the state. Kallipolis connects data and intelligence to respond to the workforce needs of a changing economy.
          </p>
        </div>

      </div>
    </section>
  );
}
