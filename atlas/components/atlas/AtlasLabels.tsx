"use client";

import { DomainKey } from "@/lib/atlasScene";

const DOMAIN_NAMES: Record<DomainKey, string> = {
  government: "Government",
  college: "College",
  industry: "Industry",
};

type Props = {
  hoveredDomain: DomainKey | null;
};

export default function AtlasLabels({ hoveredDomain }: Props) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        zIndex: 5,
      }}
    >
      {/* Wordmark */}
      <div
        style={{
          position: "absolute",
          top: "24px",
          left: "36px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <img
          src="/kallipolis-logo.png"
          alt="Kallipolis logo"
          style={{ height: "36px", width: "auto" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "20px",
            color: "#ffffff",
            lineHeight: 1,
          }}
        >
          Kallipolis
        </span>
      </div>

      {/* Hover label — fades in when a domain is hovered */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 1 : 0,
          transition: "opacity 0.2s ease",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "13px",
          fontWeight: 600,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "#ffffff",
          whiteSpace: "nowrap",
        }}
      >
        {hoveredDomain ? DOMAIN_NAMES[hoveredDomain] : ""}
      </div>

      {/* Instruction — fades out when a domain is hovered */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 0 : 1,
          transition: "opacity 0.2s ease",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "11px",
          letterSpacing: "0.1em",
          color: "rgba(255,255,255,0.2)",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        Select a domain
      </div>
    </div>
  );
}
