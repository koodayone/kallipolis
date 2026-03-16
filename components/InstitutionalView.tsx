const nodes = ["Policy Layer", "Data Layer", "Governance", "Operations", "Stakeholders"];

export default function InstitutionalView() {
  return (
    <section className="bg-white py-24 px-6 border-t border-gray-200">
      <div className="max-w-7xl mx-auto">
        <div className="mb-14">
          <p className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-3">
            Institutional View
          </p>
          <h2 className="text-3xl font-bold text-gray-900">
            How the institution sees itself
          </h2>
          <p className="mt-3 text-sm text-gray-500 max-w-xl">
            Placeholder. A diagram showing the layered structure of an institution — how information flows between layers and where friction accumulates.
          </p>
        </div>

        {/* Diagram */}
        <div className="border border-gray-200 rounded-xl p-10 bg-gray-50">
          <div className="flex items-center justify-between gap-4">
            {nodes.map((label, i) => (
              <div key={label} className="flex items-center gap-4 flex-1">
                <div className="flex-1 flex flex-col items-center">
                  <div className="w-full border border-gray-300 rounded-lg bg-white px-4 py-5 text-center">
                    <div className="w-6 h-6 bg-gray-200 rounded mx-auto mb-2" />
                    <span className="text-xs font-medium text-gray-700">{label}</span>
                  </div>
                </div>
                {i < nodes.length - 1 && (
                  <span className="text-gray-300 text-lg shrink-0">→</span>
                )}
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-gray-400 mt-6">
            Placeholder diagram — replace with actual architecture illustration
          </p>
        </div>
      </div>
    </section>
  );
}
