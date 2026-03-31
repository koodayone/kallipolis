"use client";

import { useState, useEffect } from "react";
import { DomainKey } from "@/lib/atlasScene";
import { SchoolConfig } from "@/lib/schoolConfig";
import RisingSun from "@/components/ui/RisingSun";

const DOMAIN_NAMES: Record<DomainKey, string> = {
  government: "Government",
  college: "College",
  industry: "Industry",
};

const CAMERA_Z = 9;
const TAN_HALF_FOV = Math.tan((50 / 2) * (Math.PI / 180));
const DOMAIN_WORLD_X: Record<DomainKey, number> = {
  government: -3.6,
  college: 0,
  industry: 4.0,
};

function projectX(worldX: number, aspect: number): number {
  const ndcX = worldX / (CAMERA_Z * TAN_HALF_FOV * aspect);
  return ((ndcX + 1) / 2) * 100;
}

type Props = {
  hoveredDomain: DomainKey | null;
  school: SchoolConfig;
};

export default function AtlasLabels({ hoveredDomain, school }: Props) {
  const [labelPositions, setLabelPositions] = useState({
    government: 25,
    college: 50,
    industry: 75,
  });

  useEffect(() => {
    const compute = () => {
      const aspect = window.innerWidth / window.innerHeight;
      setLabelPositions({
        government: projectX(DOMAIN_WORLD_X.government, aspect),
        college: projectX(DOMAIN_WORLD_X.college, aspect),
        industry: projectX(DOMAIN_WORLD_X.industry, aspect),
      });
    };
    compute();
    window.addEventListener("resize", compute);
    return () => window.removeEventListener("resize", compute);
  }, []);
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        zIndex: 5,
      }}
    >
      {/* Wordmark */}
      <div
        style={{
          position: "absolute",
          top: "24px",
          left: "36px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <img
          src="/kallipolis-logo.png"
          alt="Kallipolis logo"
          style={{ height: "40px", width: "auto" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "22px",
            color: "#ffffff",
            lineHeight: 1,
          }}
        >
          Kallipolis
        </span>
      </div>

      {/* College name — centered top */}
      <span
        style={{
          position: "absolute",
          top: "26px",
          left: "50%",
          transform: "translateX(-50%)",
          height: "40px",
          display: "flex",
          alignItems: "center",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "15px",
          fontWeight: 600,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.85)",
          whiteSpace: "nowrap",
          pointerEvents: "none",
        }}
      >
        {school.name}
      </span>

      {/* Sun + label area */}
      <div
        style={{
          position: "absolute",
          top: "calc(26% - 74px)",
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        {/* Sun fades in on hover */}
        <div style={{ opacity: hoveredDomain ? 1 : 0, transition: "opacity 0.5s ease-in-out", height: "60px" }}>
          <RisingSun />
        </div>
        {/* Label text — swaps between instruction and domain name */}
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "15px",
            fontWeight: 600,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.85)",
            whiteSpace: "nowrap",
          }}
        >
          {hoveredDomain ? DOMAIN_NAMES[hoveredDomain] : "Select a domain"}
        </span>
      </div>


      {/* Domain labels — always visible beneath each shape */}
      {(["government", "college", "industry"] as DomainKey[]).map((key) => (
        <span
          key={key}
          style={{
            position: "absolute",
            bottom: "12%",
            left: `${labelPositions[key]}%`,
            transform: "translateX(-50%)",
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.13em",
            textTransform: "uppercase",
            color: hoveredDomain === key ? "#c9a84c" : "rgba(255,255,255,0.35)",
            whiteSpace: "nowrap",
            pointerEvents: "none",
            transition: "color 0.3s ease-in-out",
          }}
        >
          {DOMAIN_NAMES[key]}
        </span>
      ))}

    </div>
  );
}
