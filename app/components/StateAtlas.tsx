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
    <section className="md:py-16 md:px-16 max-md:py-10 max-md:px-6" style={{ backgroundColor: "#060d1f" }}>
      <div className="flex md:flex-row md:gap-12 md:items-stretch max-md:flex-col max-md:gap-8">

        {/* Left column — map with college info overlaid in Nevada space */}
        <div className="relative md:basis-1/2 md:grow-0 md:shrink-0 md:min-h-[500px] max-md:w-full">
          <StateMap activeCollegeId={college.id} />

          {/* College info card — overlaid in the Nevada/empty space on desktop, stacked under the map on mobile */}
          <div
            className="md:absolute md:right-[13%] md:top-[12%] md:w-[42%] max-md:static max-md:mt-4 max-md:w-full"
            style={{
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
        <div className="flex flex-col justify-start md:flex-1 md:gap-12 max-md:gap-8">

          {/* Header block */}
          <div style={{ textAlign: "center" }}>
            <p className="text-sm font-medium uppercase tracking-[0.15em] text-white/40" style={{ marginBottom: 16 }}>
              The Atlas
            </p>
            <div style={{ width: 64, height: 2, background: neonColor, borderRadius: 1, opacity: 0.9, transition: `background ${FADE_DURATION}ms ease`, margin: "0 auto 24px" }} />
            <h2 className="text-[24px] md:text-[30px] leading-[1.12] tracking-[-0.02em] text-white" style={{ fontFamily: "var(--font-days-one)", fontWeight: 400 }}>
              116 schools. 73 districts. One intelligent network.
            </h2>
          </div>

          {/* Data points */}
          <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: 0.85, transition: `color ${FADE_DURATION}ms ease`, margin: 0 }}>
                Unified Perspective
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Harmonize academic &amp; labor market data to support workforce development for every region in the state.
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: 0.85, transition: `color ${FADE_DURATION}ms ease`, margin: 0 }}>
                Statewide Collaboration
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Collaborate with stakeholders statewide from a shared source of truth.
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <p style={{ fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: neonColor, opacity: 0.85, transition: `color ${FADE_DURATION}ms ease`, margin: 0 }}>
                Regional Insights
              </p>
              <p style={{ fontSize: 18, fontWeight: 500, lineHeight: 1.6, color: "rgba(255,255,255,0.85)", margin: 0 }}>
                Strategize workforce programs shaped by regional economic priorities.
              </p>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
