export default function InstitutionalView() {
  return (
    <section className="bg-white py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <p className="text-sm font-semibold uppercase tracking-widest mb-4" style={{ color: "#002366" }}>
          The Institutional View
        </p>
        <h2 className="text-4xl font-bold text-gray-900 leading-tight mb-6">
          Community colleges are central to the workforce development ecosystem.
        </h2>
        <p className="text-lg text-gray-500 mb-14">
          2 million students. Fragmented partnerships. Kallipolis brings colleges, government, and industry closer together.
        </p>

        {/* Diagram placeholder */}
        <div className="border-2 border-dashed border-gray-300 rounded-xl h-64 flex items-center justify-center">
          <span className="text-sm text-gray-400">Institutional diagram — coming soon</span>
        </div>
      </div>
    </section>
  );
}
