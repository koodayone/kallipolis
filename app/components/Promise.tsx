export default function Promise() {
  return (
    <section
      className="pt-12 pb-24 px-6"
      style={{
        backgroundImage: "url('/sunny_modernism_3.png')",
        backgroundSize: "cover",
        backgroundPosition: "top",
        minHeight: 620,
      }}
    >
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-sm font-medium uppercase tracking-[0.15em] text-pacific-navy mb-4">
          The Promise
        </p>
        <div style={{ width: 64, height: 2, background: "#FFCC33", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />
        <h2
          className="text-[32px] md:text-[40px] leading-[1.12] tracking-[-0.02em] text-pure-text"
          style={{ fontFamily: "var(--font-days-one)", fontWeight: 400, textShadow: "none" }}
        >
          Activating human potential, with California leading the way.
        </h2>
      </div>
    </section>
  );
}
