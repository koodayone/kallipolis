export default function KallipolisBrand() {
  // Content-sized (no flex grow): the brand sits at its natural width so a
  // flex-end rightSlot keeps it hard-right (State Atlas, college home) and a
  // leftSlot keeps it hard-left. An earlier flex:1-1-auto stretch (for a
  // narrow-width wordmark-drop) broke the rightSlot case by filling the cell
  // and left-aligning the mark next to the centered title — reverted.
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
      {/* next/image is overkill for a tiny fixed-size brand mark rendered
          in every header; the explicit height on the img is the only
          layout constraint we need. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "32px", width: "auto", objectFit: "contain" }} />
      <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "18px", color: "#ffffff", lineHeight: 1, whiteSpace: "nowrap" }}>
        Kallipolis
      </span>
    </div>
  );
}
