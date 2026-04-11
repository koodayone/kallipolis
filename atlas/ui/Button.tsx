import React from "react";

type Variant = "solid-gold" | "outlined" | "ghost";
type Size = "sm" | "md";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
};

const styles: Record<Variant, React.CSSProperties> = {
  "solid-gold": {
    background: "#c9a84c",
    color: "#111827",
    border: "1px solid #c9a84c",
    fontWeight: 600,
  },
  outlined: {
    background: "transparent",
    color: "#111827",
    border: "1px solid #d1d5db",
    fontWeight: 500,
  },
  ghost: {
    background: "transparent",
    color: "#6b7280",
    border: "1px solid transparent",
    fontWeight: 400,
  },
};

const sizes: Record<Size, React.CSSProperties> = {
  sm: { fontSize: "12px", padding: "6px 14px", letterSpacing: "0.06em" },
  md: { fontSize: "13px", padding: "9px 20px", letterSpacing: "0.04em" },
};

export default function Button({
  variant = "outlined",
  size = "md",
  children,
  disabled,
  style,
  ...props
}: Props) {
  return (
    <button
      {...props}
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        borderRadius: "6px",
        cursor: disabled ? "not-allowed" : "pointer",
        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
        textTransform: "uppercase",
        transition: "all 0.15s ease",
        opacity: disabled ? 0.45 : 1,
        ...styles[variant],
        ...sizes[size],
        ...style,
      }}
    >
      {children}
    </button>
  );
}
