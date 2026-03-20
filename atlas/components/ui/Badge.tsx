import React from "react";

type Variant = "gold" | "neutral" | "success";

type Props = {
  children: React.ReactNode;
  variant?: Variant;
  style?: React.CSSProperties;
};

const variants: Record<Variant, React.CSSProperties> = {
  gold: {
    color: "#a07830",
    background: "#fdf8ee",
    border: "1px solid #e8d5a0",
  },
  neutral: {
    color: "#6b7280",
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
  },
  success: {
    color: "#166534",
    background: "#f0fdf4",
    border: "1px solid #bbf7d0",
  },
};

export default function Badge({ children, variant = "neutral", style }: Props) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "3px 10px",
        borderRadius: "100px",
        fontSize: "11px",
        fontWeight: 600,
        letterSpacing: "0.07em",
        textTransform: "uppercase",
        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
        whiteSpace: "nowrap",
        ...variants[variant],
        ...style,
      }}
    >
      {children}
    </span>
  );
}
