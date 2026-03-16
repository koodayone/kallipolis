const columns = [
  {
    heading: "About",
    links: ["Our Story", "Team", "Principles", "Careers"],
  },
  {
    heading: "Documentation",
    links: ["Getting Started", "API Reference", "Concepts", "Changelog"],
  },
  {
    heading: "Product",
    links: ["Features", "Pricing", "Roadmap", "Status"],
  },
];

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-4 gap-12 mb-16">
          {/* Brand */}
          <div>
            <span className="text-white font-bold text-lg">Kallipolis</span>
            <p className="mt-3 text-sm leading-relaxed">
              Placeholder. A one-sentence description of what Kallipolis is and who it's for.
            </p>
          </div>

          {/* Link columns */}
          {columns.map((col) => (
            <div key={col.heading}>
              <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                {col.heading}
              </h4>
              <ul className="space-y-3">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm hover:text-white transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
          <span>© {new Date().getFullYear()} Kallipolis. All rights reserved.</span>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
