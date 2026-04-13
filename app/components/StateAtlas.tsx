"use client";

import dynamic from "next/dynamic";
import { NEON_COLORS } from "./StateMap";
import { ROTATION_COLLEGES, FADE_DURATION } from "../lib/collegeRotation";

const StateMap = dynamic(() => import("./StateMap"), { ssr: false });

type Props = {
  activeIndex: number;
  opacity: number;
};

export default function StateAtlas({ activeIndex, opacity }: Props) {
  const college = ROTATION_COLLEGES[activeIndex];
  const neonColor = NEON_COLORS[college.id] ?? college.neonHex;

  return (
    <section style={{ backgroundColor: "#060d1f", paddingTop: 64, paddingLeft: 64, paddingRight: 64, paddingBottom: 64 }}>
      <div style={{ display: "flex", gap: 48, alignItems: "stretch" }}>

        {/* Left column — map with college info overlaid in Nevada space */}
        <div style={{ flex: "0 0 50%", minHeight: 500, position: "relative" }}>
          <StateMap activeCollegeId={college.id} />

          {/* College info card — overlaid in the Nevada/empty space */}
          <div
            style={{
              position: "absolute",
              right: "13%",
              top: "12%",
              width: "42%",
              opacity,
              transition: `opacity ${FADE_DURATION}ms ease`,
              border: `1px solid ${neonColor}`,
              borderRadius: 6,
              padding: "12px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              cursor: "default",
              pointerEvents: "none",
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <h3
                style={{
                  fontFamily: "var(--font-days-one)",
                  fontSize: 16,
                  fontWeight: 400,
                  color: "white",
                  margin: 0,
                  lineHeight: 1.2,
                }}
              >
                {college.name}
              </h3>
              <p
                style={{
                  fontSize: 9,
                  fontWeight: 600,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: neonColor,
                  opacity: 0.7,
                  margin: 0,
                }}
              >
                {college.district}
              </p>
            </div>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
              <path d="M12 2L3 7.5 12 13l9-5.5L12 2z" fill={neonColor} opacity="0.85" />
              <path d="M12 13v9l9-5.5v-9L12 13z" fill={neonColor} opacity="0.55" />
              <path d="M12 13v9L3 16.5v-9L12 13z" fill={neonColor} opacity="0.4" />
              <path d="M12 2L3 7.5v9L12 22l9-5.5v-9L12 2z M12 13L3 7.5 M12 13l9-5.5 M12 13v9" stroke="rgba(255,255,255,0.55)" strokeWidth="0.7" />
            </svg>
          </div>
        </div>

        {/* Right column — text */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: 48 }}>

          {/* Header block */}
          <div style={{ textAlign: "center" }}>
            <p className="text-sm font-medium uppercase tracking-[0.15em] text-white/40" style={{ marginBottom: 16 }}>
              The State Atlas
            </p>
            <div style={{ width: 64, height: 2, background: neonColor, borderRadius: 1, opacity, transition: `opacity ${FADE_DURATION}ms ease`, margin: "0 auto 24px" }} />
            <h2 className="text-[24px] md:text-[30px] leading-[1.12] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              116 schools. 73 districts. One intelligent network.
            </h2>
          </div>

          {/* Data points */}
          <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: opacity * 0.85, transition: `opacity ${FADE_DURATION}ms ease`, margin: 0 }}>
                Unified Perspective
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Harmonize academic &amp; labor market data to support workforce development for 2 million students.
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: opacity * 0.85, transition: `opacity ${FADE_DURATION}ms ease`, margin: 0 }}>
                Statewide Collaboration
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Collaborate with stakeholders statewide based on a shared source of truth.
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: opacity * 0.85, transition: `opacity ${FADE_DURATION}ms ease`, margin: 0 }}>
                Regional Insights
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Drive tailored partnership strategies based on regional supply &amp; demand signals.
              </p>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
