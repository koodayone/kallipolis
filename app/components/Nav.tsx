"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Nav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 80);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close the hamburger menu whenever the route changes.
  useEffect(() => { setOpen(false); }, [pathname]);

  const isLightPage = pathname === "/mission";
  const menuLinkClass = isLightPage
    ? "text-sm uppercase tracking-widest text-[#1a1a2e] hover:text-[#1a1a2e]/60 transition-colors"
    : "text-sm uppercase tracking-widest text-white hover:text-white/60 transition-colors";

  const bgStyle = isLightPage
    ? { backgroundColor: "#F5F2EB" }
    : scrolled
      ? { backgroundColor: "#060d1f", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }
      : { backgroundColor: "transparent" };

  return (
    <nav
      className="fixed top-0 z-50 w-full"
      style={{ ...bgStyle, transition: "background-color 0.3s ease" }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo + wordmark */}
        <Link href="/" className="flex items-center gap-3" style={{ textDecoration: "none" }}>
          <img
            src="/kallipolis-logo.png"
            alt="Kallipolis logo"
            height={40}
            style={{ height: "40px", width: "auto" }}
          />
          <span
            className={`${isLightPage ? "text-[#1a1a2e]" : "text-white"} text-xl leading-none`}
            style={{ fontFamily: "var(--font-days-one)" }}
          >
            Kallipolis
          </span>
        </Link>

        {/* Right controls */}
        <div className="flex items-center gap-4">
          {/* Hamburger */}
          <button
          onClick={() => setOpen((o) => !o)}
          aria-label={open ? "Close menu" : "Open menu"}
          className="flex flex-col justify-center items-center gap-[5px] w-8 h-8 focus:outline-none"
        >
          <span
            className={`block h-[2px] w-5 ${isLightPage ? "bg-[#1a1a2e]" : "bg-white"} transition-all duration-300 origin-center`}
            style={{ transform: open ? "translateY(7px) rotate(45deg)" : "none" }}
          />
          <span
            className={`block h-[2px] w-5 ${isLightPage ? "bg-[#1a1a2e]" : "bg-white"} transition-all duration-300`}
            style={{ opacity: open ? 0 : 1 }}
          />
          <span
            className={`block h-[2px] w-5 ${isLightPage ? "bg-[#1a1a2e]" : "bg-white"} transition-all duration-300 origin-center`}
            style={{ transform: open ? "translateY(-7px) rotate(-45deg)" : "none" }}
          />
        </button>
        </div>

      </div>

      {/* Slide-down menu — right-aligned, compact */}
      <div style={{ position: "absolute", right: 0, top: 64, background: isLightPage ? "#F5F2EB" : (scrolled ? "#060d1f" : "transparent"), borderRadius: "0 0 0 8px", zIndex: 50, transition: "background 0.3s ease" }}>
        <div
          style={{
            maxHeight: open ? 240 : 0,
            overflow: "hidden",
            transition: "max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 14, padding: "16px 24px 20px" }}>
            {pathname !== "/" && (
              <Link href="/" className={menuLinkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
                Home
                <svg width="20" height="14" viewBox="6 12 44 26" fill="none" style={{ overflow: "hidden", position: "relative", top: -1 }}>
                  <defs><clipPath id="nav-sun-clip"><rect x="6" y="10" width="44" height="28" /></clipPath></defs>
                  <g clipPath="url(#nav-sun-clip)">
                    <path d={`M ${28 - 12} 36 A 12 12 0 0 1 ${28 + 12} 36 Z`} fill="currentColor" />
                    {[-90, -60, -30, 0, 30, 60, 90].map((angle, i) => {
                      const rad = (angle - 90) * Math.PI / 180;
                      const x1 = 28 + Math.cos(rad) * 16;
                      const y1 = 36 + Math.sin(rad) * 16;
                      const x2 = 28 + Math.cos(rad) * 22;
                      const y2 = 36 + Math.sin(rad) * 22;
                      return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />;
                    })}
                  </g>
                </svg>
              </Link>
            )}
            <Link href="/atlas" className={menuLinkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
              Atlas
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill="currentColor" opacity="0.85" />
                <path d="M12 13v9l9-5.5v-9L12 13z" fill="currentColor" opacity="0.55" />
                <path d="M12 13v9L3 16.5v-9L12 13z" fill="currentColor" opacity="0.4" />
                <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="currentColor" strokeWidth="0.7" opacity="0.55" />
              </svg>
            </Link>
            <Link href="/partnerships" className={menuLinkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
              Partnerships
              <svg width="12" height="12" viewBox="3 4 18 16" fill="none">
                <circle cx="9.5" cy="14" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                <circle cx="14.5" cy="10" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
              </svg>
            </Link>
            <Link href="/sources" className={menuLinkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
              Sources
              <svg width="14" height="14" viewBox="2 2 20 20" fill="none">
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
            <Link href="/mission" className={menuLinkClass} style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 6 }}>
              Mission
              <svg width="12" height="14" viewBox="0 0 20 24" fill="currentColor">
                <polygon points="10,1 6,7 14,7" />
                <polygon points="10,5 4,12 16,12" />
                <polygon points="10,9.5 2,18 18,18" />
                <rect x="8.5" y="18" width="3" height="5" rx="0.5" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
