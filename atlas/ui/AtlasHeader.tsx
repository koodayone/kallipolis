"use client";

import { useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { SchoolConfig } from "@/config/schoolConfig";
import { PREVIEW_MODE } from "@/preview/mode";

type Props = {
  title: string;
  // Compact identity for narrow widths (e.g. "SVAMP" for the consortium's
  // full name). When the full title no longer fits its center track, the
  // header swaps to this instead of ellipsizing a wordmark — shedding by
  // identity, not mutilation. Absent ⇒ the full title ellipsizes.
  shortTitle?: string;
  leftSlot?: ReactNode;
  rightSlot?: ReactNode;
  onBack?: () => void;
  school?: SchoolConfig;
  position?: "sticky" | "fixed" | "static";
  style?: CSSProperties;
  // Override the back-cube tint (defaults to the school's neon, else gold).
  cubeTint?: string;
  // Force the gold "Preview Mode" label on regardless of PREVIEW_MODE — for
  // surfaces that are always preview prototypes.
  showPreview?: boolean;
  // Override the centered title font size (defaults to 20px) — useful for
  // longer titles that would otherwise crowd the header.
  titleSize?: string;
};

export default function AtlasHeader({
  title,
  shortTitle,
  leftSlot,
  rightSlot,
  onBack,
  school,
  position = "sticky",
  style,
  cubeTint,
  showPreview = false,
  titleSize = "20px",
}: Props) {
  const backTint = cubeTint ?? school?.brandColorNeon ?? "#c9a84c";
  const backAriaLabel = school ? `Back to ${school.name}` : "Back to College Atlas";

  // Title-fit detection: a GHOST span carries the full title in flow
  // (visibility hidden) and sizes the center track up to its natural width;
  // when the track is squeezed below that (compared against the ghost's
  // stable natural width, so the swap can't oscillate), the VISIBLE overlay
  // shows shortTitle instead — or ellipsizes when no shortTitle exists.
  // Defaults to the full title where ResizeObserver is unavailable (SSR,
  // tests) — the wide-layout truth.
  const cellRef = useRef<HTMLDivElement | null>(null);
  const ghostRef = useRef<HTMLSpanElement | null>(null);
  const [compact, setCompact] = useState(false);
  useEffect(() => {
    const cell = cellRef.current, ghost = ghostRef.current;
    if (!cell || !ghost || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      setCompact(cell.clientWidth < ghost.offsetWidth - 1);
    });
    ro.observe(cell);
    return () => ro.disconnect();
  }, [title]);

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

  const titleStyle: CSSProperties = {
    fontFamily: "var(--font-days-one), sans-serif",
    fontSize: titleSize,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "rgba(255,255,255,0.85)",
    whiteSpace: "nowrap",
  };

  return (
    // Three-track grid: equal side tracks keep the title page-centered, but —
    // unlike the old absolutely-positioned span — the title is IN FLOW, so it
    // negotiates for space and can never overlap the slots. The sides carry a
    // floor (minmax 88px — icon-only nav / the sun alone) because the auto
    // center is sized BEFORE fr distribution and would otherwise starve them;
    // the shedding ladder that falls out: nav labels first, then the brand
    // wordmark, and the title compresses (shortTitle/ellipsis) last.
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
        display: "grid",
        gridTemplateColumns: "minmax(88px, 1fr) auto minmax(88px, 1fr)",
        columnGap: "20px",
        alignItems: "center",
        ...style,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", minWidth: 0 }}>
        {resolvedLeft}
      </div>

      <div ref={cellRef} style={{ position: "relative", minWidth: 0, overflow: "hidden", height: "100%", pointerEvents: "none" }}>
        {/* Ghost — sizes the track to the full title when space allows;
            never displayed, never changes, so fit detection is stable. */}
        <span ref={ghostRef} aria-hidden style={{ ...titleStyle, visibility: "hidden", display: "inline-block" }}>
          {title}
        </span>
        {/* Visible title — centered in whatever width the track won. */}
        <span
          style={{
            ...titleStyle,
            position: "absolute",
            left: 0,
            right: 0,
            top: "50%",
            transform: "translateY(-50%)",
            textAlign: "center",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {compact && shortTitle ? shortTitle : title}
        </span>
        {(PREVIEW_MODE || showPreview) && (
          <span
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: "calc(50% + 15px)",
              textAlign: "center",
              fontSize: "9px",
              fontWeight: 500,
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: "rgba(201, 168, 76, 0.65)",
              whiteSpace: "nowrap",
            }}
          >
            Preview Mode
          </span>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "20px", minWidth: 0, justifyContent: "flex-end" }}>
        {rightSlot}
      </div>
    </header>
  );
}
