export default function KallipolisBrand() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
      <img src="/kallipolis-logo.png" alt="Kallipolis" style={{ height: "32px", width: "auto", objectFit: "contain" }} />
      <span style={{ fontFamily: "var(--font-days-one), sans-serif", fontSize: "18px", color: "#ffffff", lineHeight: 1 }}>
        Kallipolis
      </span>
    </div>
  );
}
