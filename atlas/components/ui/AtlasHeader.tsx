"use client";

import type { CSSProperties, ReactNode } from "react";
import { SchoolConfig } from "@/lib/schoolConfig";

type Props = {
  title: string;
  leftSlot?: ReactNode;
  rightSlot?: ReactNode;
  onBack?: () => void;
  school?: SchoolConfig;
  position?: "sticky" | "fixed" | "static";
  style?: CSSProperties;
};

export default function AtlasHeader({
  title,
  leftSlot,
  rightSlot,
  onBack,
  school,
  position = "sticky",
  style,
}: Props) {
  const backTint = school?.brandColorNeon ?? "#c9a84c";
  const backAriaLabel = school ? `Back to ${school.name}` : "Back to College Atlas";

  const resolvedLeft = leftSlot ?? (onBack ? (
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
      aria-label={backAriaLabel}
    >
      <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={backTint} opacity="0.85" />
        <path d="M12 13v9l9-5.5v-9L12 13z" fill={backTint} opacity="0.55" />
        <path d="M12 13v9L3 16.5v-9L12 13z" fill={backTint} opacity="0.4" />
        <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
      </svg>
      <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
        <path d="M10 12L6 8l4-4" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  ) : null);

  return (
    <header
      style={{
        position,
        ...(position !== "static" ? { top: 0, left: 0, right: 0 } : {}),
        zIndex: 30,
        flexShrink: 0,
        height: "72px",
        padding: "0 40px",
        background: "rgba(6, 13, 31, 0.95)",
        backdropFilter: "blur(8px)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        ...style,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", minWidth: 0 }}>
        {resolvedLeft}
      </div>

      <span
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          fontFamily: "var(--font-days-one), sans-serif",
          fontSize: "18px",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.85)",
          whiteSpace: "nowrap",
          pointerEvents: "none",
        }}
      >
        {title}
      </span>

      <div style={{ display: "flex", alignItems: "center", gap: "20px", minWidth: 0, justifyContent: "flex-end" }}>
        {rightSlot}
      </div>
    </header>
  );
}
