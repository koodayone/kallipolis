import ActionBadge from "../../components/ActionBadge";

// ── Section primitives (light theme) ─────────────────────────────────────

const GREEN = "#2D5016";
const TEXT = "#1a1a2e";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.15em", color: GREEN, marginBottom: 16 }}>
      {children}
    </p>
  );
}

function GreenDivider() {
  return <div style={{ width: 64, height: 2, background: GREEN, borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />;
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2
      className="text-[24px] md:text-[32px] leading-[1.12] tracking-[-0.02em]"
      style={{ fontFamily: "var(--font-days-one)", fontWeight: 400, color: TEXT }}
    >
      {children}
    </h2>
  );
}

function LandscapeImage({ src, alt, position = "center 15%", height = 480 }: { src: string; alt: string; position?: string; height?: number }) {
  return (
    <div style={{ padding: "0 64px" }}>
      <img
        src={src}
        alt={alt}
        style={{
          width: "100%",
          height,
          objectFit: "cover",
          objectPosition: position,
          borderRadius: 10,
          display: "block",
        }}
      />
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────

export default function MissionPage() {
  return (
    <div style={{ background: "#F5F2EB", minHeight: "100vh" }}>

      {/* ── 1. Hero Image — Tahoe ── */}
      <div style={{ paddingTop: 80 }}>
        <LandscapeImage src="/tahoe_art.png" alt="Lake Tahoe" />
      </div>

      {/* ── 2. Mission Statement ── */}
      <section style={{ padding: "120px 64px", textAlign: "center" }}>
        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <Eyebrow>Mission</Eyebrow>
          <GreenDivider />
          <SectionHeading>
            Advance the spirit of reinvention<br />in our public institutions.
          </SectionHeading>
          <p style={{ fontSize: 17, lineHeight: 1.7, color: "#3d3a36", marginTop: 28 }}>
            Kallipolis is an ode to the State of California and the spirit of reinvention. We believe that there is no institution that more faithfully represents this spirit than California Community Colleges. In the face of historic technological and social change, it is imperative that we reinvent what it means to build the future. Developing a vibrant workforce is central to that cause, and it is here that Kallipolis aims to make its contribution.
          </p>
        </div>
      </section>

      {/* ── 4. Middle Image — Yosemite ── */}
      <LandscapeImage src="/yosemite_art.png" alt="Yosemite" position="center 58%" />

      {/* ── 4. About the Founder ── */}
      <section style={{ padding: "120px 64px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", gap: 48, alignItems: "center" }}>
          {/* Portrait */}
          <div style={{ flex: "0 0 240px", borderRadius: 10, overflow: "hidden" }}>
            <img
              src="/portrait.png"
              alt="Dayone Koo"
              style={{
                width: 240,
                height: 340,
                objectFit: "cover",
                display: "block",
              }}
            />
          </div>

          {/* Bio */}
          <div style={{ flex: 1 }}>
            <div style={{ textAlign: "center" }}>
              <Eyebrow>About the Founder</Eyebrow>
              <GreenDivider />
            </div>
            <p style={{ fontSize: 17, lineHeight: 1.7, color: "#3d3a36", marginTop: 28 }}>
              Dayone Koo is a proud graduate of the California Community Colleges system. He received an Associate of Arts in Social Sciences at Foothill College, where he first conceived the motivation to build software that empowers democratic institutions.
            </p>
            <p style={{ fontSize: 17, lineHeight: 1.7, color: "#3d3a36", marginTop: 20 }}>
              After Foothill, Dayone transferred to and graduated from UC Berkeley with a Bachelor of Arts in Computer Science. Upon graduation he gathered experience as a software engineer building global scale enterprise systems at Walmart and Salesforce. Founding Kallipolis is an attempt at pursuing his original motivation to build technology.
            </p>
          </div>
        </div>
      </section>

      {/* ── 5. Closing Image — Tenaya ── */}
      <LandscapeImage src="/tenaya_art.png" alt="Tenaya Lake" position="center 28%" height={520} />

      {/* ── 6. Cross-links ── */}
      <section style={{ background: "#F5F2EB", padding: "48px 64px", display: "flex", justifyContent: "center" }}>
        <div style={{ transform: "scale(1.04)", transformOrigin: "center" }}>
          <ActionBadge label="Home" neonColor="#2D5016" opacity={1} icon="sun" inline href="/" />
        </div>
      </section>
    </div>
  );
}
