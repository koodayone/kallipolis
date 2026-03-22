"use client";

import { DomainKey } from "@/lib/atlasScene";
import { SchoolConfig } from "@/lib/schoolConfig";
import LogoutButton from "@/components/auth/LogoutButton";

type Props = {
  domain: DomainKey;
  onBack: () => void;
  school: SchoolConfig;
};

export default function DomainHeader({ onBack, school }: Props) {

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 20,
        background: "rgba(5, 14, 27, 0.95)",
        backdropFilter: "blur(8px)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        padding: "0 40px",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Back button — Kallipolis logo + gold Atlas label */}
      <button
        onClick={onBack}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "6px 0",
          color: "#ffffff",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "12px",
          fontWeight: 500,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          transition: "opacity 0.15s",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.75")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
      >
        <img
          src={school.logoPath}
          alt={school.name}
          style={{ height: "28px", width: "auto", objectFit: "contain" }}
        />
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M10 12L6 8l4-4"
            stroke="#ffffff"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
        {/* Kallipolis wordmark */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <img
            src="/kallipolis-logo.png"
            alt="Kallipolis"
            style={{ height: "28px", width: "auto", objectFit: "contain" }}
          />
          <span
            style={{
              fontFamily: "var(--font-days-one), sans-serif",
              fontSize: "16px",
              color: "#ffffff",
              lineHeight: 1,
            }}
          >
            Kallipolis
          </span>
        </div>
        <LogoutButton />
      </div>
    </header>
  );
}
