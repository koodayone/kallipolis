export default function KallipolisBrand() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
      {/* next/image is overkill for a tiny fixed-size brand mark rendered
          in every header; the explicit height on the img is the only
          layout constraint we need. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "32px", width: "auto", objectFit: "contain" }} />
      <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "18px", color: "#ffffff", lineHeight: 1 }}>
        Kallipolis
      </span>
    </div>
  );
}
