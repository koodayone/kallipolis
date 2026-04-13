import Link from "next/link";

export default function Footer() {
  return (
    <footer className="text-gray-400" style={{ backgroundColor: "#060d1f" }}>
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex items-start mb-8">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <img
              src="/kallipolis-logo.png"
              alt="Kallipolis logo"
              height={40}
              style={{ height: "40px", width: "auto" }}
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
            <div className="flex flex-col gap-2">
              <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400">About</h4>
              <p className="text-xs uppercase tracking-widest text-gray-600">Coming Soon</p>
            </div>
            <div className="flex flex-col gap-2">
              <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400">Documentation</h4>
              <Link href="/atlas" className="text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Atlas</Link>
              <Link href="/sources" className="text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Sources</Link>
              <Link href="/partnerships" className="text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Partnerships</Link>
            </div>
            <div className="flex flex-col gap-2">
              <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400">Product</h4>
              <p className="text-xs uppercase tracking-widest text-gray-600">Coming Soon</p>
            </div>
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
