const nodes = [
  { label: "Node Alpha", x: "15%", y: "20%" },
  { label: "Node Beta", x: "45%", y: "10%" },
  { label: "Node Gamma", x: "75%", y: "25%" },
  { label: "Node Delta", x: "25%", y: "60%" },
  { label: "Node Epsilon", x: "55%", y: "55%" },
  { label: "Node Zeta", x: "80%", y: "65%" },
];

export default function StateView() {
  return (
    <section className="bg-slate-900 text-white py-24 px-6 border-t border-slate-800">
      <div className="max-w-7xl mx-auto">
        <div className="mb-14">
          <p className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-3">
            State View
          </p>
          <h2 className="text-3xl font-bold text-white">
            The constellation of state
          </h2>
          <p className="mt-3 text-sm text-slate-400 max-w-xl">
            Placeholder. A live view of how entities, decisions, and relationships map across the system at any given moment.
          </p>
        </div>

        {/* Constellation */}
        <div className="relative border border-slate-700 rounded-xl bg-slate-800 h-72 overflow-hidden">
          {/* Connecting lines (decorative) */}
          <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <line x1="15%" y1="20%" x2="45%" y2="10%" stroke="#334155" strokeWidth="1" />
            <line x1="45%" y1="10%" x2="75%" y2="25%" stroke="#334155" strokeWidth="1" />
            <line x1="15%" y1="20%" x2="25%" y2="60%" stroke="#334155" strokeWidth="1" />
            <line x1="45%" y1="10%" x2="55%" y2="55%" stroke="#334155" strokeWidth="1" />
            <line x1="75%" y1="25%" x2="80%" y2="65%" stroke="#334155" strokeWidth="1" />
            <line x1="25%" y1="60%" x2="55%" y2="55%" stroke="#334155" strokeWidth="1" />
            <line x1="55%" y1="55%" x2="80%" y2="65%" stroke="#334155" strokeWidth="1" />
          </svg>

          {/* Nodes */}
          {nodes.map((node) => (
            <div
              key={node.label}
              className="absolute flex flex-col items-center -translate-x-1/2 -translate-y-1/2"
              style={{ left: node.x, top: node.y }}
            >
              <div className="w-3 h-3 rounded-full bg-indigo-400 ring-4 ring-indigo-900" />
              <span className="mt-2 text-xs text-slate-400 whitespace-nowrap">{node.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
