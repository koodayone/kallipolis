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
          <div className="flex flex-1" style={{ paddingTop: 5, position: "relative" }}>
            <div className="flex flex-col gap-3" style={{ position: "absolute", left: "44%", transform: "translateX(-50%)" }}>
              <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400" style={{ fontFamily: "var(--font-days-one)" }}>About</h4>
              <p className="uppercase tracking-widest text-gray-600" style={{ fontFamily: "var(--font-days-one)", fontSize: 10 }}>Coming Soon</p>
            </div>
            <div className="flex flex-col gap-3" style={{ marginLeft: "auto", marginRight: "3%" }}>
              <h4 className="text-sm font-medium uppercase tracking-widest text-gray-400" style={{ fontFamily: "var(--font-days-one)" }}>Documentation</h4>
              <Link href="/atlas" className="uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 10, display: "inline-flex", alignItems: "center", gap: 6 }}>
                Atlas
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill="currentColor" opacity="0.85" />
                  <path d="M12 13v9l9-5.5v-9L12 13z" fill="currentColor" opacity="0.55" />
                  <path d="M12 13v9L3 16.5v-9L12 13z" fill="currentColor" opacity="0.4" />
                </svg>
              </Link>
              <Link href="/sources" className="uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 10, display: "inline-flex", alignItems: "center", gap: 6 }}>
                Sources
                <svg width="10" height="10" viewBox="2 2 20 20" fill="none">
                  <path d="M12 2 L13 10 L12 9 L11 10 Z" fill="currentColor" />
                  <path d="M12 22 L13 14 L12 15 L11 14 Z" fill="currentColor" />
                  <path d="M2 12 L10 11 L9 12 L10 13 Z" fill="currentColor" />
                  <path d="M22 12 L14 11 L15 12 L14 13 Z" fill="currentColor" />
                  <circle cx="12" cy="12" r="2" fill="currentColor" />
                  <line x1="5" y1="5" x2="9" y2="9" stroke="currentColor" strokeWidth="1" opacity="0.8" />
                  <line x1="19" y1="5" x2="15" y2="9" stroke="currentColor" strokeWidth="1" opacity="0.8" />
                  <line x1="5" y1="19" x2="9" y2="15" stroke="currentColor" strokeWidth="1" opacity="0.8" />
                  <line x1="19" y1="19" x2="15" y2="15" stroke="currentColor" strokeWidth="1" opacity="0.8" />
                </svg>
              </Link>
              <Link href="/partnerships" className="uppercase tracking-widest text-gray-500 hover:text-white transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 10, display: "inline-flex", alignItems: "center", gap: 6 }}>
                Partnerships
                <svg width="10" height="10" viewBox="3 4 18 16" fill="none">
                  <circle cx="9.5" cy="14" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                  <circle cx="14.5" cy="10" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                </svg>
              </Link>
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
