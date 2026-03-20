"use client";

import { DomainKey } from "@/lib/atlasScene";
import { SchoolConfig } from "@/lib/schoolConfig";

const DOMAIN_LABELS: Record<DomainKey, { title: string; subtitle: string }> = {
  government: {
    title: "Government",
    subtitle: "Workforce & Compliance Reporting",
  },
  college: {
    title: "College",
    subtitle: "Institutional Inventory",
  },
  industry: {
    title: "Industry",
    subtitle: "Partnership Intelligence",
  },
};

type Props = {
  domain: DomainKey;
  onBack: () => void;
  school: SchoolConfig;
};

export default function DomainHeader({ domain, onBack, school }: Props) {
  const { title, subtitle } = DOMAIN_LABELS[domain];

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 20,
        background: "rgba(248, 247, 244, 0.95)",
        backdropFilter: "blur(8px)",
        borderBottom: "1px solid #e4e2dc",
        padding: "0 40px",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Back button */}
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
          color: "#6b7280",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "12px",
          fontWeight: 500,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          transition: "color 0.15s",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#111827")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "#6b7280")}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M10 12L6 8l4-4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        Atlas
      </button>

      {/* Domain title */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: school.brandColor,
          }}
        >
          {title}
        </span>
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "11px",
            fontWeight: 400,
            letterSpacing: "0.06em",
            color: "#9ca3af",
            textTransform: "uppercase",
          }}
        >
          {subtitle}
        </span>
      </div>

      {/* School logo */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e4e2dc",
          borderRadius: "6px",
          padding: "4px 10px",
          display: "flex",
          alignItems: "center",
        }}
      >
        <img
          src={school.logoPath}
          alt={school.name}
          style={{ height: "28px", width: "auto", objectFit: "contain" }}
        />
      </div>
    </header>
  );
}
