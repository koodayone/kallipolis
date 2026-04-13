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
          {/* Search icon */}
          <button onClick={() => setOpen((o) => !o)} aria-label="Search" className="text-white hover:text-white transition-colors">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>

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

      {/* Slide-down curtain */}
      <div
        style={{
          maxHeight: open ? 120 : 0,
          overflow: "hidden",
          transition: "max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          backgroundColor: scrolled ? "#060d1f" : "transparent",
          borderTop: open ? "1px solid rgba(255,255,255,0.1)" : "none",
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-center gap-8">
          <Link href="/atlas" className="text-xs uppercase tracking-widest text-white/40 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Atlas</Link>
          <Link href="/sources" className="text-xs uppercase tracking-widest text-white/40 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Sources</Link>
          <Link href="/partnerships" className="text-xs uppercase tracking-widest text-white/40 hover:text-white transition-colors" style={{ textDecoration: "none" }}>Partnerships</Link>
        </div>
      </div>
    </nav>
  );
}
