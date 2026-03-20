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
          top: "28px",
          left: "36px",
          display: "flex",
          flexDirection: "column",
          gap: "2px",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "#c9a84c",
          }}
        >
          Kallipolis
        </span>
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "11px",
            fontWeight: 400,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.3)",
          }}
        >
          Atlas
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
          color: "#c9a84c",
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
