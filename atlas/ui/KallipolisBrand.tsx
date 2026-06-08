"use client";

import { useMeasuredWidth } from "@/ui/measure";

export default function KallipolisBrand() {
  // Container-driven shedding: when the brand's cell can't fit the wordmark
  // beside the sun (~150px), the wordmark drops and the sun carries the
  // identity alone. The wrapper STRETCHES into its cell (flex 1 1 auto) so
  // the measurement reads AVAILABLE width, not content width — otherwise the
  // compact form would measure its own small footprint and never re-expand.
  // First unmeasured frame renders full.
  const { ref, width } = useMeasuredWidth(true);
  const sunOnly = width != null && width < 150;
  return (
    <div ref={ref} style={{ flex: "1 1 auto", minWidth: 0, display: "flex", alignItems: "center", gap: "7px" }}>
      {/* next/image is overkill for a tiny fixed-size brand mark rendered
          in every header; the explicit height on the img is the only
          layout constraint we need. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "32px", width: "auto", objectFit: "contain" }} />
      {!sunOnly && (
        <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "18px", color: "#ffffff", lineHeight: 1, whiteSpace: "nowrap" }}>
          Kallipolis
        </span>
      )}
    </div>
  );
}
