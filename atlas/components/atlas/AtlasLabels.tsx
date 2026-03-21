"use client";

import { DomainKey } from "@/lib/atlasScene";
import RisingSun from "@/components/ui/RisingSun";

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
          style={{ height: "40px", width: "auto" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "22px",
            color: "#ffffff",
            lineHeight: 1,
          }}
        >
          Kallipolis
        </span>
      </div>

      {/* Sun + domain label — fade in together on hover */}
      <div
        style={{
          position: "absolute",
          top: "calc(24% - 74px)",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 1 : 0,
          transition: "opacity 0.5s ease-in-out",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <RisingSun />
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "18px",
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "#ffffff",
            whiteSpace: "nowrap",
          }}
        >
          {hoveredDomain ? DOMAIN_NAMES[hoveredDomain] : ""}
        </span>
      </div>

      {/* Institution logo + instruction — fades out when a domain is hovered */}
      <div
        style={{
          position: "absolute",
          top: "calc(24% - 74px)",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 0 : 1,
          transition: "opacity 0.5s ease-in-out",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <img
          src="/foothill-logo-2.png"
          alt="Foothill College"
          style={{ height: "72px", width: "auto", objectFit: "contain" }}
        />
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "15px",
            letterSpacing: "0.1em",
            color: "rgba(255,255,255,0.85)",
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          Select a domain
        </span>
      </div>
    </div>
  );
}
