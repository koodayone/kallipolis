"use client";

export default function LoadingDots({ label = "Analyzing labor market alignment..." }: { label?: string }) {
  const dots = Array.from({ length: 9 }, (_, i) => i);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "28px",
        padding: "80px 0",
      }}
    >
      {/* 3×3 gold dot grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "10px",
        }}
      >
        {dots.map((i) => (
          <div
            key={i}
            className="gold-dot"
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "#c9a84c",
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>

      <p
        style={{
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "13px",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#9ca3af",
          fontWeight: 500,
        }}
      >
        {label}
      </p>
    </div>
  );
}
