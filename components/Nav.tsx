"use client";

import { useState } from "react";

export default function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 w-full" style={{ backgroundColor: "#002366" }}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo + wordmark */}
        <div className="flex items-center gap-3">
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
        </div>

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

      {/* Slide-down curtain */}
      <div
        style={{
          maxHeight: open ? 120 : 0,
          overflow: "hidden",
          transition: "max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          backgroundColor: "#002366",
          borderTop: open ? "1px solid rgba(255,255,255,0.1)" : "none",
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-8 flex items-center justify-center">
          <p className="text-xs uppercase tracking-widest text-white/40">Coming Soon</p>
        </div>
      </div>
    </nav>
  );
}
