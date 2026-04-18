"use client";

import { useRef, useState } from "react";
import { useScroll, useMotionValueEvent } from "framer-motion";
import React from "react";
import {
  EmployerLandscapeBand,
  OccupationalDemandBand,
  CurriculumAlignmentBand,
  StudentImpactBand,
  SupplyDemandBridgeBand,
} from "./PartnershipAnatomyCard";

const BRAND = "#4fd1fd";
const STEP_COUNT = 5;

// ── RisingSun ────────────────────────────────────────────────────────────

const SUN_RAYS = [
  { angle: -90, long: true },  { angle: -75, long: false },
  { angle: -60, long: true },  { angle: -45, long: false },
  { angle: -30, long: true },  { angle: -15, long: false },
  { angle:   0, long: true },  { angle:  15, long: false },
  { angle:  30, long: true },  { angle:  45, long: false },
  { angle:  60, long: true },  { angle:  75, long: false },
  { angle:  90, long: true },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

function RisingSun() {
  const cx = 28, cy = 36, innerR = 15;
  const color = "#c9a84c";
  return (
    <svg
      width="100" height="62" viewBox="0 0 56 36" fill="none"
      style={{ filter: `drop-shadow(0 0 8px ${color}55)`, animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block", margin: "0 auto" }}
    >
      <defs>
        <clipPath id="journey-sun-clip">
          <rect x="0" y="0" width="56" height="37" />
        </clipPath>
      </defs>
      <g clipPath="url(#journey-sun-clip)">
        {SUN_RAYS.map((r, i) => {
          const rad = toRad(r.angle - 90);
          const len = r.long ? 9 : 6;
          const x1 = cx + Math.cos(rad) * (innerR + 3);
          const y1 = cy + Math.sin(rad) * (innerR + 3);
          const x2 = cx + Math.cos(rad) * (innerR + 3 + len);
          const y2 = cy + Math.sin(rad) * (innerR + 3 + len);
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              className="sun-ray"
              style={{ stroke: color, animationDelay: `${i * 0.18}s` }}
            />
          );
        })}
        <path
          d={`M ${cx - innerR} ${cy} A ${innerR} ${innerR} 0 0 1 ${cx + innerR} ${cy} Z`}
          fill={color}
        />
      </g>
    </svg>
  );
}

// ── Steps ────────────────────────────────────────────────────────────────

const STEPS = [
  {
    num: "01",
    question: "Which employers in my region are top candidates for a partnership?",
    prose: "Identify partnership opportunities from a landscape of organizations whose hiring needs align with your curriculum.",
    Band: EmployerLandscapeBand,
    hasAccordion: true,
  },
  {
    num: "02",
    question: "What occupations does this employer hire for?",
    prose: "Every employer is connected to the occupations it hires for — with regional wages, growth rates, and annual openings.",
    Band: OccupationalDemandBand,
    hasAccordion: true,
  },
  {
    num: "03",
    question: "Which of our academic departments have most synergy with this employer?",
    prose: "Specific departments at your college whose coursework develops the skills this employer's occupations require.",
    Band: CurriculumAlignmentBand,
    hasAccordion: true,
  },
  {
    num: "04",
    question: "Which students will benefit from this partnership?",
    prose: "Know which students can benefit the most from a partnership — by coursework, by skills, and by academic performance.",
    Band: StudentImpactBand,
    hasAccordion: true,
  },
  {
    num: "05",
    question: "What unmet regional labor market demand will this partnership address?",
    prose: "Proposals that instantaneously bridge TOP to SOC codes. Precisely quantify how your school supplies unmet labor demand.",
    Band: SupplyDemandBridgeBand,
    hasAccordion: true,
  },
];

// Fixed layout positions (px from top of sticky frame)
const SUN_TOP = 80;
const TEXT_TOP = 160;
const BAND_TOP = 320;

// ── Progress Indicator ───────────────────────────────────────────────────

function ProgressIndicator({ activeStep, stepProgress }: { activeStep: number; stepProgress: number }) {
  return (
    <div style={{
      position: "absolute",
      right: 24,
      top: "50%",
      transform: "translateY(-50%)",
      display: "flex",
      flexDirection: "column",
      gap: 12,
      zIndex: 20,
    }}>
      {STEPS.map((_, i) => {
        const isPast = i < activeStep;
        const isActive = i === activeStep;
        const fillPercent = isPast ? 100 : isActive ? stepProgress * 100 : 0;

        return (
          <div
            key={i}
            style={{
              width: 4,
              height: 44,
              borderRadius: 2,
              background: "rgba(255,255,255,0.08)",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${fillPercent}%`,
              borderRadius: 2,
              background: BRAND,
              boxShadow: isActive || isPast ? "0 0 8px rgba(79,209,253,0.4)" : "none",
            }} />
          </div>
        );
      })}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────

export default function PartnershipJourney() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });
  const [activeStep, setActiveStep] = useState(0);
  const [stepProgress, setStepProgress] = useState(0);
  const [sunVisible, setSunVisible] = useState(false);

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    const step = Math.min(STEP_COUNT - 1, Math.floor(v * STEP_COUNT));
    const progressWithinStep = (v * STEP_COUNT) - step;
    setActiveStep(step);
    setStepProgress(progressWithinStep);
    setSunVisible(v > 0.02);
  });

  const active = STEPS[activeStep];

  // Content opacity: fade out near end of step, fade in at start
  const isLastStep = activeStep === STEP_COUNT - 1;
  const isFirstStep = activeStep === 0;
  let contentOpacity = 1;
  if (!isLastStep && stepProgress > 0.85) {
    contentOpacity = (1 - stepProgress) / 0.15;
  }
  if (!isFirstStep && stepProgress < 0.15) {
    contentOpacity = stepProgress / 0.15;
  }

  return (
    <div
      ref={containerRef}
      style={{ height: `${STEP_COUNT * 100}vh`, position: "relative" }}
    >
      <div style={{
        position: "sticky",
        top: 0,
        height: "100vh",
        overflow: "hidden",
        opacity: sunVisible ? 1 : 0.15,
        transition: "opacity 0.8s ease",
      }}>
        {/* Sun — fixed position */}
        <div style={{
          position: "absolute",
          top: SUN_TOP,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 10,
        }}>
          <RisingSun />
        </div>

        {/* Text area — fixed position, content fades */}
        <div style={{
          position: "absolute",
          top: TEXT_TOP,
          left: "50%",
          transform: "translateX(-50%)",
          width: "100%",
          maxWidth: 900,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          padding: "0 64px",
          opacity: contentOpacity,
        }}>
          {/* Number + Question */}
          <div style={{
            position: "relative",
            maxWidth: 480,
            width: "100%",
            opacity: 1,
          }}>
            <span
              key={`num-${activeStep}`}
              style={{
                position: "absolute",
                right: "calc(100% + 24px)",
                top: -4,
                fontFamily: "var(--font-days-one)",
                fontSize: 36,
                fontWeight: 700,
                color: BRAND,
                opacity: 0.35,
                whiteSpace: "nowrap",
                lineHeight: 1,
                animation: "fade-in-quick 0.25s ease",
              }}
            >
              {active.num}
            </span>
            <p
              key={`q-${activeStep}`}
              style={{
                fontSize: 17,
                fontWeight: 500,
                lineHeight: 1.4,
                color: "rgba(255,255,255,0.8)",
                margin: 0,
                textAlign: "center",
                animation: "fade-in-quick 0.25s ease",
              }}
            >
              {active.question}
            </p>
          </div>

          {/* Prose */}
          <p
            key={`p-${activeStep}`}
            style={{
              fontSize: 14,
              lineHeight: 1.6,
              color: "rgba(255,255,255,0.4)",
              margin: 0,
              textAlign: "center",
              maxWidth: 460,
              animation: "fade-in-quick 0.25s ease",
            }}
          >
            {active.prose}
          </p>
        </div>

        {/* Band area — fixed position, content fades */}
        <div style={{
          position: "absolute",
          top: BAND_TOP,
          left: "50%",
          transform: "translateX(-50%)",
          width: "100%",
          maxWidth: 900,
          padding: "0 24px",
          opacity: contentOpacity,
        }}>
          <div
            key={`band-${activeStep}`}
            style={{ animation: "fade-in-quick 0.25s ease" }}
          >
            {active.hasAccordion
              ? React.createElement(active.Band, { expandProgress: stepProgress })
              : <active.Band />
            }
          </div>
        </div>

        <ProgressIndicator activeStep={activeStep} stepProgress={stepProgress} />
      </div>
    </div>
  );
}
