import TwoFormsDiagram from "./TwoFormsDiagram";
import ActionBadge from "./ActionBadge";

const points = [
  { label: "Generative Proposals", text: "Generate intelligent partnership proposals adhering to Strong Workforce Program standards." },
  { label: "Regional Engagement", text: "Align employer-specific partnerships with regional SWP development plans." },
  { label: "Labor Market Integration", text: "Instantly identify TOP codes, SOC mappings, supply-demand gaps, and quantifiable student impact." },
];

export default function PartnershipsSection() {
  return (
    <section className="md:pt-10 md:px-16 md:pb-0 max-md:pt-8 max-md:px-6 max-md:pb-0" style={{ backgroundColor: "#060d1f" }}>

      <div className="flex md:flex-row md:gap-12 md:items-stretch md:pb-16 max-md:flex-col max-md:gap-8 max-md:pb-12">

        {/* Left column — header + points */}
        <div className="flex flex-col justify-center md:basis-[42%] md:grow-0 md:shrink-0 md:gap-6 md:self-center max-md:gap-5 max-md:self-stretch">

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: "rgba(255,255,255,0.45)", marginBottom: 16 }}>
              Intelligent Partnerships
            </p>
            <div style={{ width: 64, height: 2, background: "#4fd1fd", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
            <h2 className="text-[22px] md:text-[28px] leading-[1.15] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              Drive partnerships that advance a Strong Workforce.
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
        <div className="flex flex-col gap-2 md:flex-1 max-md:w-full">
          <div className="rounded-[10px] overflow-hidden md:min-h-[280px] max-md:min-h-[360px]">
            <TwoFormsDiagram />
          </div>
          <div className="text-center md:-mt-10 max-md:mt-2">
            <ActionBadge label="Explore Partnerships" neonColor="#4fd1fd" opacity={1} icon="chainlink" inline href="/partnerships" />
          </div>
        </div>
      </div>
    </section>
  );
}
