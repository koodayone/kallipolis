import InstitutionalDiagram from "./InstitutionalDiagram";
import FourFormsDiagram from "./FourFormsDiagram";
import EpistemologyGraph from "./EpistemologyGraph";

const points = [
  { label: "Unmatched Scale", text: "California Community Colleges is the largest system of higher education in the United States." },
  { label: "Central Networks", text: "Colleges connect industry, government, and the local workforce." },
  { label: "Universal Access", text: "Individuals can enroll from all walks of life. Open admissions, low tuition, flexible commitments." },
];

export default function InstitutionalView({ dark = false, activeIndex = 0, opacity = 1 }: { dark?: boolean; activeIndex?: number; opacity?: number }) {
  if (dark) {
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

  return (
    <section style={{ backgroundColor: "#060d1f", paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 0 }}>

      {/* Top block */}
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
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
        <div style={{ flex: "0 0 45%", display: "flex", flexDirection: "column", gap: 30, justifyContent: "center", alignSelf: "center" }}>
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

        {/* Right column — Three.js diagram */}
        <div style={{ flex: 1, minHeight: 300, borderRadius: 10, overflow: "hidden" }}>
          <InstitutionalDiagram />
        </div>
      </div>
    </section>
  );
}
