"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

export default function Nav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const handleLogoClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    if (pathname === "/") return;
    const content = document.querySelector("[data-fade-target]") as HTMLElement
      ?? document.querySelector("main") as HTMLElement;
    if (content) {
      content.style.transition = "opacity 0.4s ease";
      content.style.opacity = "0";
      setTimeout(() => router.push("/"), 400);
    } else {
      router.push("/");
    }
  }, [pathname, router]);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 80);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const bgStyle = scrolled
    ? { backgroundColor: "#060d1f", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }
    : { backgroundColor: "transparent" };

  return (
    <nav
      className="fixed top-0 z-50 w-full"
      style={{ ...bgStyle, transition: "background-color 0.3s ease" }}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo + wordmark */}
        <Link href="/" onClick={handleLogoClick} className="flex items-center gap-3" style={{ textDecoration: "none" }}>
          <img
            src="/kallipolis-logo.png"
            alt="Kallipolis logo"
            height={40}
            style={{ height: "40px", width: "auto" }}
          />
          <span
            className="text-white text-xl leading-none"
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
            className="block h-[2px] w-5 bg-white transition-all duration-300 origin-center"
            style={{ transform: open ? "translateY(7px) rotate(45deg)" : "none" }}
          />
          <span
            className="block h-[2px] w-5 bg-white transition-all duration-300"
            style={{ opacity: open ? 0 : 1 }}
          />
          <span
            className="block h-[2px] w-5 bg-white transition-all duration-300 origin-center"
            style={{ transform: open ? "translateY(-7px) rotate(-45deg)" : "none" }}
          />
        </button>
        </div>

      </div>

      {/* Slide-down menu — right-aligned, compact */}
      <div style={{ position: "absolute", right: 0, top: 64, background: scrolled ? "#060d1f" : "transparent", borderRadius: "0 0 0 8px", zIndex: 50, transition: "background 0.3s ease" }}>
        <div
          style={{
            maxHeight: open ? 160 : 0,
            overflow: "hidden",
            transition: "max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 14, padding: "16px 24px 20px" }}>
            <Link href="/atlas" className="text-sm uppercase tracking-widest text-white hover:text-white/60 transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
              Atlas
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill="currentColor" opacity="0.85" />
                <path d="M12 13v9l9-5.5v-9L12 13z" fill="currentColor" opacity="0.55" />
                <path d="M12 13v9L3 16.5v-9L12 13z" fill="currentColor" opacity="0.4" />
                <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="currentColor" strokeWidth="0.7" opacity="0.55" />
              </svg>
            </Link>
            <Link href="/sources" className="text-sm uppercase tracking-widest text-white hover:text-white/60 transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
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
            <Link href="/partnerships" className="text-sm uppercase tracking-widest text-white hover:text-white/60 transition-colors" style={{ textDecoration: "none", fontFamily: "var(--font-days-one)", display: "inline-flex", alignItems: "center", gap: 8 }}>
              Partnerships
              <svg width="12" height="12" viewBox="3 4 18 16" fill="none">
                <circle cx="9.5" cy="14" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
                <circle cx="14.5" cy="10" r="5.5" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.85" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
