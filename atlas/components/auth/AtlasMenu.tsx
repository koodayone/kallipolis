"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type NavItem = {
  label: string;
  href?: string;
  onClick?: () => void;
  icon?: React.ReactNode;
};

type Props = {
  navItems?: NavItem[];
};

const DEFAULT_NAV: NavItem[] = [{ label: "State View", href: "/state" }];

export default function AtlasMenu({ navItems = DEFAULT_NAV }: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      {/* Hamburger icon */}
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "8px",
          display: "flex",
          flexDirection: "column",
          gap: "5px",
          transition: "opacity 0.15s",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = open ? "1" : "0.65")}
        aria-label="Menu"
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              display: "block",
              width: "24px",
              height: "2px",
              background: "rgba(255,255,255,0.65)",
              borderRadius: "1px",
            }}
          />
        ))}
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              right: 0,
              background: "rgba(10,15,25,0.95)",
              backdropFilter: "blur(8px)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              padding: "6px 0",
              minWidth: "160px",
              zIndex: 100,
            }}
          >
            {navItems.map((item) => {
              const style: React.CSSProperties = {
                display: "block",
                width: "100%",
                textAlign: "left" as const,
                padding: "14px 20px",
                color: "rgba(255,255,255,0.7)",
                fontSize: "13px",
                fontWeight: 500,
                letterSpacing: "0.08em",
                textTransform: "uppercase" as const,
                fontFamily: FONT,
                textDecoration: "none",
                background: "none",
                border: "none",
                cursor: "pointer",
                transition: "color 0.1s, background 0.1s",
              };
              const onEnter = (e: React.MouseEvent) => {
                (e.currentTarget as HTMLElement).style.color = "#ffffff";
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.06)";
              };
              const onLeave = (e: React.MouseEvent) => {
                (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)";
                (e.currentTarget as HTMLElement).style.background = "transparent";
              };

              const content = item.icon ? (
                <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {item.icon}
                  {item.label}
                </span>
              ) : item.label;

              return item.href ? (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  style={style}
                  onMouseEnter={onEnter}
                  onMouseLeave={onLeave}
                >
                  {content}
                </Link>
              ) : (
                <button
                  key={item.label}
                  onClick={() => { setOpen(false); item.onClick?.(); }}
                  style={style}
                  onMouseEnter={onEnter}
                  onMouseLeave={onLeave}
                >
                  {content}
                </button>
              );
            })}
            <button
              onClick={handleLogout}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "14px 20px",
                color: "rgba(255,255,255,0.7)",
                fontSize: "13px",
                fontWeight: 500,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                fontFamily: FONT,
                background: "none",
                border: "none",
                cursor: "pointer",
                transition: "color 0.1s, background 0.1s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#ffffff";
                e.currentTarget.style.background = "rgba(255,255,255,0.06)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "rgba(255,255,255,0.7)";
                e.currentTarget.style.background = "transparent";
              }}
            >
              Log Out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
