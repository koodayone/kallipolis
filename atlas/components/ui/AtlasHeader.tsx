"use client";

import { SchoolConfig } from "@/lib/schoolConfig";
import KallipolisBrand from "@/components/ui/KallipolisBrand";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
};

export default function AtlasHeader({ school, onBack }: Props) {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 30,
        background: "rgba(6, 13, 31, 0.95)",
        backdropFilter: "blur(8px)",
        padding: "0 40px",
        height: "72px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Back button — College Atlas cube + chevron */}
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "8px",
          transition: "opacity 0.15s",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.opacity = "0.7")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.opacity = "1")}
        aria-label="Back to College Atlas"
      >
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={school.brandColorNeon} opacity="0.85" />
          <path d="M12 13v9l9-5.5v-9L12 13z" fill={school.brandColorNeon} opacity="0.55" />
          <path d="M12 13v9L3 16.5v-9L12 13z" fill={school.brandColorNeon} opacity="0.4" />
          <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
        </svg>
        <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
          <path d="M10 12L6 8l4-4" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* College name — centered */}
      <span
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, calc(-50% + 1px))",
          fontFamily: "var(--font-days-one), sans-serif",
          fontSize: "18px",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.85)",
          whiteSpace: "nowrap",
          pointerEvents: "none",
        }}
      >
        {school.name}
      </span>

      {/* Kallipolis branding — top right */}
      <KallipolisBrand />
    </header>
  );
}
