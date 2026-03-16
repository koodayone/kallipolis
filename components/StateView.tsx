export default function StateView() {
  return (
    <section className="py-24 px-6" style={{ backgroundColor: "#002366" }}>
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-white/50 mb-4">
          The State View
        </p>
        <h2 className="text-4xl font-bold text-white leading-tight mb-6">
          116 schools. 73 districts. One intelligent network.
        </h2>
        <p className="text-lg text-white/60 mb-14">
          California Community Colleges serve every region of the state. Kallipolis connects data and intelligence to respond to the workforce needs of a changing economy.
        </p>

        {/* Constellation placeholder */}
        <div className="border-2 border-dashed border-white/30 rounded-xl h-64 flex items-center justify-center">
          <span className="text-sm text-white/40">California constellation — coming soon</span>
        </div>
      </div>
    </section>
  );
}
