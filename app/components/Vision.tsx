import ActionBadge from "./ActionBadge";

export default function Vision() {
  return (
    <section className="relative overflow-hidden py-24 px-6 md:min-h-[780px] max-md:min-h-[600px]">

      {/* 1. Background image */}
      <img
        src="/hero-illustration.jpg"
        alt=""
        aria-hidden="true"
        className="ken-burns"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", objectPosition: "center 75%", zIndex: 0 }}
      />

      {/* 2. Dark overlay */}
      <div aria-hidden="true" style={{ position: "absolute", inset: 0, background: "rgba(0,10,30,0.25)", zIndex: 1 }} />

      {/* 3. Gradient overlay */}
      <div aria-hidden="true" style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(0,18,64,0.65) 0%, rgba(0,35,102,0.5) 30%, rgba(10,74,143,0.25) 60%, rgba(26,111,173,0.08) 85%, transparent 100%)", zIndex: 2 }} />


{/* 4. Content */}
      <div className="pt-22" style={{ position: "relative", zIndex: 3 }}>
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-sm font-medium uppercase tracking-[0.15em] text-white/40 mb-4">
            Institutional Intelligence
          </p>

          {/* Gold divider rule */}
          <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />

          <h1 className="text-[40px] md:text-[56px] leading-[1.08] tracking-[-0.03em] text-white mb-6" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
            California&apos;s<br />intelligence layer for<br />workforce development
          </h1>

          {/* Primary call to action — same Preview destination as the
              persistent nav CTA. Sized full (not compact) so it reads
              as the primary action surface; the nav CTA defers visually.
              Hidden below md: the atlas is not yet mobile-optimized, so
              we don't surface entry points on touch viewports. */}
          <div className="max-md:hidden" style={{ marginTop: 32 }}>
            <ActionBadge
              label="Preview"
              neonColor="#f5e6c8"
              opacity={1}
              icon="play"
              inline
              prominent
              href="https://preview.kallipolis.us"
              newTab
            />
          </div>
        </div>
      </div>

      {/* Radial gold glow */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)",
          width: 600, height: 260, pointerEvents: "none",
          background: "radial-gradient(ellipse at 50% 100%, rgba(255,204,51,0.13) 0%, rgba(255,204,51,0.04) 45%, transparent 70%)",
        }}
      />
    </section>
  );
}
