export default function Problem() {
  return (
    <section className="bg-coastal-fog py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-pacific-navy mb-4">
          The Moment
        </p>
        {/* Green divider rule */}
        <div style={{ width: 64, height: 2, background: "#4A7C59", borderRadius: 1, opacity: 0.9, margin: "0 auto 24px" }} />

        <p className="text-[36px] md:text-[48px] font-bold leading-[1.12] tracking-[-0.02em] text-pure-text max-w-[700px] mx-auto">
          AI is disrupting the workforce. Institutions need to respond.
        </p>
      </div>
    </section>
  );
}
