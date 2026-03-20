import React from "react";

type Props = {
  children: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
};

export default function Card({ children, style, className }: Props) {
  return (
    <div
      className={className}
      style={{
        background: "#ffffff",
        border: "1px solid #e4e2dc",
        borderRadius: "10px",
        boxShadow: "0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
