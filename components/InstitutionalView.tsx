export default function InstitutionalView() {
  return (
    <section className="bg-redwood-green py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-xs font-medium uppercase tracking-[0.15em] text-white/40 mb-4">
          The Institutional View
        </p>
        <h2 className="text-4xl md:text-5xl font-bold leading-[1.15] text-white mb-6">
          Community colleges are central to the workforce development ecosystem.
        </h2>
        <p className="text-lg font-normal leading-relaxed text-white/70 max-w-[600px] mx-auto mb-14">
          2 million students. Fragmented partnerships. Kallipolis brings colleges, government, and industry closer together.
        </p>

        {/* Diagram placeholder */}
        <div className="border-2 border-dashed border-white/30 rounded-xl h-64 flex items-center justify-center">
          <span className="text-sm text-white/40">Institutional diagram — coming soon</span>
        </div>
      </div>
    </section>
  );
}
