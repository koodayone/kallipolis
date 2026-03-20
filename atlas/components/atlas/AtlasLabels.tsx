"use client";

import { DomainKey } from "@/lib/atlasScene";

type LabelConfig = {
  domain: DomainKey;
  title: string;
  subtitle: string;
  // Approximate screen positions (percent from top/left)
  top: string;
  left: string;
  align: "left" | "right" | "center";
};

const LABELS: LabelConfig[] = [
  {
    domain: "government",
    title: "Government",
    subtitle: "Workforce & Compliance",
    top: "8%",
    left: "55%",
    align: "left",
  },
  {
    domain: "college",
    title: "College",
    subtitle: "Institutional Inventory",
    top: "44%",
    left: "57%",
    align: "left",
  },
  {
    domain: "industry",
    title: "Industry",
    subtitle: "Partnership Intelligence",
    top: "70%",
    left: "55%",
    align: "left",
  },
];

export default function AtlasLabels() {
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

      {/* Domain labels */}
      {LABELS.map((label) => (
        <div
          key={label.domain}
          style={{
            position: "absolute",
            top: label.top,
            left: label.left,
            display: "flex",
            flexDirection: "column",
            gap: "3px",
            transform: "translateY(-50%)",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "12px",
              fontWeight: 600,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "#c9a84c",
            }}
          >
            {label.title}
          </span>
          <span
            style={{
              fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
              fontSize: "11px",
              fontWeight: 400,
              letterSpacing: "0.04em",
              color: "rgba(255,255,255,0.35)",
            }}
          >
            {label.subtitle}
          </span>
        </div>
      ))}

      {/* Bottom instruction */}
      <div
        style={{
          position: "absolute",
          bottom: "32px",
          left: "50%",
          transform: "translateX(-50%)",
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
