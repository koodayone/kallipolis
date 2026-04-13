import EpistemologyGraph from "./EpistemologyGraph";

export default function EpistemologySection({ activeIndex = 0, opacity = 1 }: { activeIndex?: number; opacity?: number }) {
  return (
    <section style={{ backgroundColor: "#060d1f", paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 0 }}>
      <div style={{ display: "flex", gap: 48, alignItems: "stretch" }}>

        {/* Left column — header + points */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: 48 }}>

          {/* Header */}
          <div style={{ textAlign: "center" }}>
            <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
              The Epistemology
            </p>
            <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
            <h2 className="text-[24px] md:text-[30px] leading-[1.12] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              Insights grounded in<br />public datasets verified by public institutions.
            </h2>
          </div>

          {/* Epistemology mappings */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {[
              { unit: "Students", source: "Chancellor's Office Data Mart", desc: "Enrollment and academic outcomes from the statewide MIS." },
              { unit: "Courses", source: "College Curriculum Catalogs", desc: "Course descriptions, learning outcomes, and skill mappings obtained from institutional catalogs." },
              { unit: "Occupations", source: "Centers of Excellence", desc: "Regional labor market research and occupation demand signals by COE region." },
              { unit: "Employers", source: "Employment Development Department", desc: "County-level employer records from the EDD ALMIS database." },
            ].map((row) => (
              <div
                key={row.unit}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: 10,
                }}
              >
                <span style={{
                  fontSize: 15,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  color: "#c9a84c",
                  flexShrink: 0,
                  width: 130,
                }}>
                  {row.unit}
                </span>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{
                    fontSize: 18,
                    fontWeight: 600,
                    color: "rgba(255,255,255,0.85)",
                  }}>
                    {row.source}
                  </span>
                  <span style={{
                    fontSize: 14,
                    color: "rgba(255,255,255,0.4)",
                    lineHeight: 1.5,
                  }}>
                    {row.desc}
                  </span>
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* Right column — Four forms diagram */}
        <div style={{ flex: "0 0 50%", minHeight: 500 }}>
          <EpistemologyGraph activeIndex={activeIndex} opacity={opacity} />
        </div>
      </div>
    </section>
  );
}
