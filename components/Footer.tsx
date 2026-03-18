const columns = ["About", "Documentation", "Product"];

export default function Footer() {
  return (
    <footer className="bg-footer-dark text-gray-400 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex items-start mb-8">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <img
              src="/kallipolis-logo.png"
              alt="Kallipolis logo"
              height={32}
              style={{ height: "32px", width: "auto" }}
            />
            <span
              className="text-white text-lg leading-none"
              style={{ fontFamily: "var(--font-days-one)" }}
            >
              Kallipolis
            </span>
          </div>

          {/* Link columns */}
          <div className="flex flex-1 justify-evenly" style={{ paddingTop: 5 }}>
            {columns.map((col) => (
              <div key={col} className="flex flex-col gap-2">
                <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400">
                  {col}
                </h4>
                <p className="text-xs uppercase tracking-widest text-gray-600">Coming Soon</p>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800 pt-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
          <span>© {new Date().getFullYear()} Kallipolis Technologies. All rights reserved.</span>
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
