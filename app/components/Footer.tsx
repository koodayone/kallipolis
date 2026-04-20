"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Footer() {
  const pathname = usePathname();
  const isLightPage = pathname === "/mission";

  const bg = isLightPage ? "#F5F2EB" : "#060d1f";
  const textClass = isLightPage ? "text-[#1a1a2e]/60" : "text-gray-400";
  const headingClass = isLightPage ? "text-sm font-medium uppercase tracking-widest text-[#1a1a2e]/70" : "text-sm font-medium uppercase tracking-widest text-gray-400";
  const linkClass = isLightPage
    ? "uppercase tracking-widest text-[#1a1a2e]/50 hover:text-[#1a1a2e] transition-colors"
    : "uppercase tracking-widest text-gray-500 hover:text-white transition-colors";
  const brandClass = isLightPage ? "text-[#1a1a2e] text-lg leading-none" : "text-white text-lg leading-none";
  const borderClass = isLightPage ? "border-t border-[#1a1a2e]/10" : "border-t border-gray-800";
  const bottomLinkClass = isLightPage ? "hover:text-[#1a1a2e] transition-colors" : "hover:text-white transition-colors";

  return (
    <footer className={textClass} style={{ backgroundColor: bg }}>
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
              className={brandClass}
              style={{ fontFamily: "var(--font-days-one)" }}
            >
              Kallipolis
            </span>
          </div>

          {/* Link columns */}
          <div className="flex flex-1" style={{ paddingTop: 5, position: "relative" }}>
            <div className="flex flex-col gap-3" style={{ position: "absolute", left: "44%", transform: "translateX(-50%)" }}>
              <h4 className={headingClass} style={{ fontFamily: "var(--font-days-one)" }}>About</h4>
              <Link href="/mission" className={linkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 5 }}>
                Mission
                <svg width="10" height="12" viewBox="0 0 20 24" fill="currentColor">
                  <polygon points="10,1 6,7 14,7" />
                  <polygon points="10,5 4,12 16,12" />
                  <polygon points="10,9.5 2,18 18,18" />
                  <rect x="8.5" y="18" width="3" height="5" rx="0.5" />
                </svg>
              </Link>
            </div>
            <div className="flex flex-col gap-3" style={{ marginLeft: "auto", marginRight: "3%" }}>
              <h4 className={headingClass} style={{ fontFamily: "var(--font-days-one)" }}>Documentation</h4>
              <Link href="/atlas" className={linkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
                Atlas
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill="currentColor" opacity="0.85" />
                  <path d="M12 13v9l9-5.5v-9L12 13z" fill="currentColor" opacity="0.55" />
                  <path d="M12 13v9L3 16.5v-9L12 13z" fill="currentColor" opacity="0.4" />
                </svg>
              </Link>
              <Link href="/partnerships" className={linkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
                Partnerships
                <svg width="10" height="10" viewBox="3 4 18 16" fill="none">
                  <circle cx="9.5" cy="14" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                  <circle cx="14.5" cy="10" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                </svg>
              </Link>
              <Link href="/sources" className={linkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
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
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className={`${borderClass} pt-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs`}>
          <span>&copy; {new Date().getFullYear()} Kallipolis Technologies. All rights reserved.</span>
          <div className="flex gap-6">
            <a href="#" className={bottomLinkClass}>Privacy</a>
            <a href="#" className={bottomLinkClass}>Terms</a>
            <a href="#" className={bottomLinkClass}>Contact</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
