"use client";

import type { ReactNode } from "react";

// Shared design language for the Partnership Landscape Report family — used by
// both the per-(college, occupation) OpportunityReport and the aggregated
// SVAMP landscape, so the two read as the same artifact at different altitudes.

export const FONT = "var(--font-inter), Inter, system-ui, sans-serif";
export const MONO = "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace";

/** Magazine-style report header: an optional document-type eyebrow, a
 *  brand-tinted hairline, the subject title, then an optional mono meta
 *  classifier line (passed as children so each report composes its own
 *  classifiers). `accent` is the report's brand color (a college's brand, or
 *  the consortium accent). Omitting `eyebrow` yields a hairline-led header —
 *  used for embedded detail where the eyebrow would repeat the page's own. */
export function ReportHeader({
  eyebrow,
  title,
  accent,
  children,
}: {
  eyebrow?: string;
  title: string;
  accent: string;
  children?: ReactNode;
}) {
  return (
    <div style={{ marginBottom: "32px" }}>
      {eyebrow && (
        <div style={{
          fontFamily: FONT, fontSize: "13px", fontWeight: 700,
          letterSpacing: "0.22em", textTransform: "uppercase",
          color: accent, marginBottom: "14px",
        }}>
          {eyebrow}
        </div>
      )}
      <div style={{ height: "1px", background: `${accent}40`, marginBottom: "20px" }} />
      <h1 style={{
        fontFamily: FONT, fontSize: "28px", fontWeight: 600,
        color: "rgba(255,255,255,0.95)", letterSpacing: "-0.01em",
        margin: 0, lineHeight: 1.2,
      }}>
        {title}
      </h1>
      {/* Per-child alpha rather than a parent opacity (a parent opacity
          composites the whole subtree and multiplies child alphas down). */}
      {children && (
        <div style={{
          fontFamily: MONO, fontSize: "11px", fontWeight: 500,
          letterSpacing: "0.05em", fontVariantNumeric: "tabular-nums",
          marginTop: "12px", textTransform: "uppercase",
        }}>
          {children}
        </div>
      )}
    </div>
  );
}

/** A report section: a 3px brand accent bar + title, then arbitrary body. */
export function Section({ title, brandColor, children }: {
  title: string;
  brandColor: string;
  children: ReactNode;
}) {
  return (
    <div style={{ marginTop: "32px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
        <div style={{
          width: "3px", height: "16px", background: brandColor,
          borderRadius: "2px", flexShrink: 0, opacity: 0.85,
        }} />
        <h3 style={{
          fontFamily: FONT, fontSize: "15px", fontWeight: 600,
          color: "rgba(255,255,255,0.95)", letterSpacing: "-0.005em",
          margin: 0, lineHeight: 1.2,
        }}>
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

/** Report body prose. */
export function Prose({ children }: { children: ReactNode }) {
  return (
    <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.7)", lineHeight: 1.65, margin: 0 }}>
      {children}
    </p>
  );
}
