"use client";

import { useState, useEffect, useRef } from "react";

const INPUTS = [
  { label: "Students", icon: "🎓", color: "#c9a84c" },
  { label: "Courses", icon: "📖", color: "#c9a84c" },
  { label: "Occupations", icon: "⛑", color: "#c9a84c" },
  { label: "Employers", icon: "🏢", color: "#c9a84c" },
];

export default function ConvergenceDiagram() {
  const [active, setActive] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setActive(true); },
      { threshold: 0.4 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ maxWidth: 700, margin: "0 auto", padding: "32px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 0 }}>

        {/* Left — four input lanes */}
        <div style={{ flex: "0 0 160px", display: "flex", flexDirection: "column", gap: 16 }}>
          {INPUTS.map((input, i) => (
            <div
              key={input.label}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 14px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 6,
                opacity: active ? 1 : 0,
                transform: active ? "translateX(0)" : "translateX(-20px)",
                transition: `opacity 0.5s ease ${i * 0.12}s, transform 0.5s ease ${i * 0.12}s`,
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: input.color }}>
                {input.label}
              </span>
            </div>
          ))}
        </div>

        {/* Center — convergence lines (SVG) */}
        <div style={{ flex: 1, position: "relative", height: 200 }}>
          <svg width="100%" height="200" viewBox="0 0 300 200" preserveAspectRatio="none" style={{ display: "block" }}>
            {INPUTS.map((_, i) => {
              const startY = 25 + i * 50;
              return (
                <line
                  key={i}
                  x1="0" y1={startY}
                  x2="300" y2="100"
                  stroke="rgba(79,209,253,0.25)"
                  strokeWidth="1"
                  style={{
                    opacity: active ? 1 : 0,
                    transition: `opacity 0.6s ease ${0.5 + i * 0.1}s`,
                  }}
                />
              );
            })}
            {/* Center node */}
            <circle
              cx="300" cy="100" r="6"
              fill="#4fd1fd"
              style={{
                opacity: active ? 1 : 0,
                transition: "opacity 0.5s ease 0.9s",
              }}
            />
          </svg>
        </div>

        {/* Right — output */}
        <div style={{
          flex: "0 0 180px", display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
          opacity: active ? 1 : 0,
          transform: active ? "translateX(0)" : "translateX(20px)",
          transition: "opacity 0.6s ease 1.1s, transform 0.6s ease 1.1s",
        }}>
          <div style={{
            padding: "14px 20px",
            background: "rgba(79,209,253,0.08)",
            border: "1px solid rgba(79,209,253,0.2)",
            borderRadius: 8,
            textAlign: "center",
          }}>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#4fd1fd", display: "block", marginBottom: 4 }}>
              Partnership
            </span>
            <span style={{ fontSize: 13, color: "rgba(255,255,255,0.5)" }}>
              Proposal
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
