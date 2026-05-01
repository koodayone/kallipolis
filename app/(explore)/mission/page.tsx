import ActionBadge from "../../components/ActionBadge";
import FadeUp from "../../components/FadeUp";

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
  const mobileHeight = Math.round(height * 0.7);
  return (
    <div className="md:px-16 max-md:px-6">
      <img
        src={src}
        alt={alt}
        className="md:h-[var(--ld-h)] max-md:h-[var(--ld-mh)]"
        style={{
          "--ld-h": `${height}px`,
          "--ld-mh": `${mobileHeight}px`,
          width: "100%",
          objectFit: "cover",
          objectPosition: position,
          borderRadius: 10,
          display: "block",
        } as React.CSSProperties}
      />
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────

export default function MissionPage() {
  return (
    <div className="md:min-h-screen max-md:min-h-[100dvh]" style={{ background: "#F5F2EB" }}>

      {/* ── 1. Hero Image — Tahoe ── */}
      <FadeUp style={{ paddingTop: 80 }}>
        <LandscapeImage src="/tahoe_art.png" alt="Lake Tahoe" />
      </FadeUp>

      {/* ── 2. Mission Statement ── */}
      <section className="text-center md:py-[120px] md:px-16 max-md:py-16 max-md:px-6">
        <FadeUp style={{ maxWidth: 640, margin: "0 auto" }}>
          <Eyebrow>Mission</Eyebrow>
          <GreenDivider />
          <SectionHeading>
            Advance the spirit of reinvention<br />in our public institutions.
          </SectionHeading>
          <p style={{ fontSize: 17, lineHeight: 1.7, color: "#3d3a36", marginTop: 28 }}>
            Kallipolis is an ode to the State of California and the spirit of reinvention. We believe that there is no institution that more faithfully represents this spirit than California Community Colleges. In the face of historic technological and social change, it is imperative that we reinvent what it means to build the future. Developing a vibrant workforce is central to that cause, and it is here that Kallipolis aims to make its contribution.
          </p>
        </FadeUp>
      </section>

      {/* ── 4. Middle Image — Yosemite ── */}
      <FadeUp>
        <LandscapeImage src="/yosemite_art.png" alt="Yosemite" position="center 58%" />
      </FadeUp>

      {/* ── 4. About the Founder ── */}
      <section className="md:py-[120px] md:px-16 max-md:py-16 max-md:px-6">
        <FadeUp className="max-w-[900px] mx-auto flex md:flex-row md:gap-12 md:items-center max-md:flex-col max-md:gap-8 max-md:items-stretch">
          {/* Portrait */}
          <div className="rounded-[10px] overflow-hidden md:basis-[240px] md:grow-0 md:shrink-0 max-md:max-w-[280px] max-md:mx-auto max-md:w-full">
            <img
              src="/portrait.png"
              alt="Dayone Koo"
              className="md:w-[240px] md:h-[340px] max-md:w-full max-md:aspect-[240/340]"
              style={{
                objectFit: "cover",
                display: "block",
              }}
            />
          </div>

          {/* Bio */}
          <div className="md:flex-1 max-md:w-full">
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
        </FadeUp>
      </section>

      {/* ── 5. Closing Image — Tenaya ── */}
      <FadeUp>
        <LandscapeImage src="/tenaya_art.png" alt="Tenaya Lake" position="center 28%" height={520} />
      </FadeUp>

      {/* ── 6. Cross-links ── */}
      <FadeUp className="flex justify-center md:py-12 md:px-16 max-md:py-10 max-md:px-6" style={{ background: "#F5F2EB" }}>
        <div style={{ transform: "scale(1.04)", transformOrigin: "center" }}>
          <ActionBadge label="Home" neonColor="#2D5016" opacity={1} icon="sun" inline href="/" />
        </div>
      </FadeUp>
    </div>
  );
}
