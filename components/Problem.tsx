const problems = [
  {
    title: "Fragmented information",
    body: "Placeholder. Institutions operate on siloed data with no shared substrate for meaning or decision-making.",
  },
  {
    title: "Slow coordination",
    body: "Placeholder. Alignment across teams and stakeholders is costly, error-prone, and breaks down at scale.",
  },
  {
    title: "Opaque reasoning",
    body: "Placeholder. Decisions are made in black boxes. Accountability is diffuse and trust erodes over time.",
  },
];

export default function Problem() {
  return (
    <section className="bg-gray-50 py-24 px-6 border-t border-gray-200">
      <div className="max-w-7xl mx-auto">
        <div className="mb-14">
          <p className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-3">
            The Problem
          </p>
          <h2 className="text-3xl font-bold text-gray-900">
            Institutions are flying blind
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {problems.map((p) => (
            <div key={p.title} className="bg-white border border-gray-200 rounded-lg p-6">
              {/* Icon placeholder */}
              <div className="w-10 h-10 bg-gray-200 rounded mb-4" />
              <h3 className="text-base font-semibold text-gray-900 mb-2">{p.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
