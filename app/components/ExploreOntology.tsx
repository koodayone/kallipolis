"use client";

import { useState } from "react";
import { FADE_DURATION } from "../lib/collegeRotation";

type Props = {
  label?: string;
  neonColor: string;
  opacity: number;
  icon?: "cube" | "lightbulb" | "chainlink" | "mail" | "play";
  inline?: boolean;
};

function CubeIcon({ color }: { color: string }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={color} opacity="0.85" />
      <path d="M12 13v9l9-5.5v-9L12 13z" fill={color} opacity="0.55" />
      <path d="M12 13v9L3 16.5v-9L12 13z" fill={color} opacity="0.4" />
      <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
    </svg>
  );
}

function LightbulbIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="2 2 20 20" fill="none">
      <path d="M12 2 L13 10 L12 9 L11 10 Z" fill={color} />
      <path d="M12 22 L13 14 L12 15 L11 14 Z" fill={color} />
      <path d="M2 12 L10 11 L9 12 L10 13 Z" fill={color} />
      <path d="M22 12 L14 11 L15 12 L14 13 Z" fill={color} />
      <circle cx="12" cy="12" r="2" fill={color} />
      <line x1="5" y1="5" x2="9" y2="9" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="19" y1="5" x2="15" y2="9" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="5" y1="19" x2="9" y2="15" stroke={color} strokeWidth="1" opacity="0.8" />
      <line x1="19" y1="19" x2="15" y2="15" stroke={color} strokeWidth="1" opacity="0.8" />
    </svg>
  );
}

function ChainlinkIcon({ color }: { color: string }) {
  return (
    <svg width="12" height="12" viewBox="3 4 18 16" fill="none">
      <circle cx="9.5" cy="14" r="5.5" stroke={color} strokeWidth="2" fill="none" opacity="0.85" />
      <circle cx="14.5" cy="10" r="5.5" stroke={color} strokeWidth="2" fill="none" opacity="0.85" />
    </svg>
  );
}

function PlayIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
      <polygon points="6,3 21,12 6,21" fill={color} opacity="0.85" stroke={color} strokeWidth="1" strokeLinejoin="round" />
    </svg>
  );
}

function MailIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="12" viewBox="0 0 24 18" fill="none">
      <rect x="1" y="1" width="22" height="16" rx="2" stroke={color} strokeWidth="1.5" fill="none" opacity="0.85" />
      <path d="M1 1 L12 10 L23 1" stroke={color} strokeWidth="1.5" fill="none" opacity="0.85" />
    </svg>
  );
}

export default function ExploreOntology({ label = "Explore Ontology", neonColor, opacity, icon = "cube", inline = false }: Props) {
  const [hovered, setHovered] = useState(false);

  const badge = (
      <div
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 18px",
          border: `1px solid ${neonColor}`,
          borderRadius: 6,
          cursor: "pointer",
          opacity,
          transform: hovered ? "scale(1.05)" : "scale(1)",
          background: hovered ? `${neonColor}15` : "transparent",
          boxShadow: hovered ? `0 0 12px ${neonColor}30` : "none",
          transition: `opacity ${FADE_DURATION}ms ease, border-color ${FADE_DURATION}ms ease, transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease`,
        }}
      >
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: hovered ? "#ffffff" : neonColor,
            transition: `color 0.2s ease`,
          }}
        >
          {label}
        </span>
        {icon === "cube" && <CubeIcon color={hovered ? "#ffffff" : neonColor} />}
        {icon === "lightbulb" && <LightbulbIcon color={hovered ? "#ffffff" : neonColor} />}
        {icon === "chainlink" && <ChainlinkIcon color={hovered ? "#ffffff" : neonColor} />}
        {icon === "mail" && <MailIcon color={hovered ? "#ffffff" : neonColor} />}
        {icon === "play" && <PlayIcon color={hovered ? "#ffffff" : neonColor} />}
      </div>
  );

  if (inline) return badge;

  return (
    <section style={{ background: "#060d1f", padding: "0 64px 24px", textAlign: "center" }}>
      {badge}
    </section>
  );
}
