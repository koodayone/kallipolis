"use client";

import { SchoolConfig } from "@/lib/schoolConfig";
import KallipolisBrand from "@/components/ui/KallipolisBrand";

type ParentShape = "dodecahedron" | "cube" | "tetrahedron";

type Props = {
  school: SchoolConfig;
  onBack: () => void;
  parentShape: ParentShape;
};

function ShapeIcon({ shape, color, edgeColor }: { shape: ParentShape; color: string; edgeColor: string }) {
  const size = 30;

  if (shape === "cube") {
    return (
      <svg width={size + 4} height={size + 4} viewBox="0 0 24 24" fill="none">
        <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={color} opacity="0.85" />
        <path d="M12 13v9l9-5.5v-9L12 13z" fill={color} opacity="0.55" />
        <path d="M12 13v9L3 16.5v-9L12 13z" fill={color} opacity="0.4" />
        <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke={edgeColor} strokeWidth="0.7" />
      </svg>
    );
  }

  if (shape === "dodecahedron") {
    return (
      <svg width={size + 4} height={size + 4} viewBox="0 0 24 24" fill="none">
        {/* Dodecahedron — looking straight at one face, pentagon centered */}
        {/* 5 surrounding faces (back to front) */}
        <polygon points="2.5,8.9 6.1,3.9 8.4,7 6.1,13.9 2.5,15.1" fill={color} opacity="0.35" />
        <polygon points="6.1,20.1 2.5,15.1 6.1,13.9 12,18.2 12,22" fill={color} opacity="0.4" />
        <polygon points="17.9,3.9 21.5,8.9 21.5,15.1 17.9,13.9 15.6,7" fill={color} opacity="0.5" />
        <polygon points="17.9,3.9 15.6,7 8.4,7 6.1,3.9 12,2" fill={color} opacity="0.6" />
        <polygon points="21.5,15.1 17.9,20.1 12,22 12,18.2 17.9,13.9" fill={color} opacity="0.7" />
        {/* Center pentagon (brightest) */}
        <polygon points="8.4,7 15.6,7 17.9,13.9 12,18.2 6.1,13.9" fill={color} opacity="0.85" />
        {/* Edges */}
        <path d="M8.4,7L15.6,7 M15.6,7L17.9,13.9 M17.9,13.9L12,18.2 M12,18.2L6.1,13.9 M6.1,13.9L8.4,7 M2.5,8.9L6.1,3.9 M6.1,3.9L8.4,7 M2.5,15.1L6.1,13.9 M2.5,8.9L2.5,15.1 M6.1,20.1L2.5,15.1 M12,22L12,18.2 M6.1,20.1L12,22 M17.9,3.9L21.5,8.9 M21.5,8.9L21.5,15.1 M21.5,15.1L17.9,13.9 M17.9,3.9L15.6,7 M12,2L6.1,3.9 M17.9,3.9L12,2 M21.5,15.1L17.9,20.1 M17.9,20.1L12,22" stroke={edgeColor} strokeWidth="0.5" />
      </svg>
    );
  }

  // tetrahedron — looking straight at one face, triangle centered
  return (
    <svg width={size + 4} height={size + 4} viewBox="0 0 24 24" fill="none">
      {/* 3 surrounding faces */}
      <polygon points="12,3.3 12,14.9 2,20.7" fill={color} opacity="0.45" />
      <polygon points="12,3.3 22,20.7 12,14.9" fill={color} opacity="0.6" />
      <polygon points="22,20.7 2,20.7 12,14.9" fill={color} opacity="0.35" />
      {/* Center triangle — the face we're looking at */}
      <polygon points="12,3.3 22,20.7 2,20.7" fill={color} opacity="0.85" />
      {/* Edges */}
      <path d="M12,3.3L22,20.7 M22,20.7L2,20.7 M2,20.7L12,3.3 M12,3.3L12,14.9 M22,20.7L12,14.9 M2,20.7L12,14.9" stroke={edgeColor} strokeWidth="0.6" />
    </svg>
  );
}

export default function AtlasHeader({ school, onBack, parentShape }: Props) {
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
      {/* Back button — parent shape + chevron */}
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
        <ShapeIcon shape={parentShape} color={school.brandColorNeon} edgeColor="rgba(255,255,255,0.55)" />
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
