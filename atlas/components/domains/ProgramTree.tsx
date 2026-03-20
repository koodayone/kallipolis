"use client";

import { ProgramSummary } from "@/lib/api";

type Props = {
  programs: ProgramSummary[];
};

const COLORS = ["#c9a84c", "#b8973d", "#a5862e", "#927520", "#7e6411"];

export default function ProgramTree({ programs }: Props) {
  const PROG_HEIGHT = 44;
  const PROG_WIDTH = 220;
  const CURR_HEIGHT = 28;
  const CURR_WIDTH = 200;
  const H_GAP = 140;
  const V_PAD = 16;

  // Calculate vertical positions for programs (centered in their curriculum group)
  type ProgLayout = {
    prog: ProgramSummary;
    color: string;
    progY: number;
    curricula: { name: string; y: number }[];
  };

  const layouts: ProgLayout[] = [];
  let currY = V_PAD;

  programs.forEach((prog, pi) => {
    const groupHeight = prog.curricula.length * (CURR_HEIGHT + 8) - 8;
    const curricula = prog.curricula.map((c, ci) => ({
      name: c,
      y: currY + ci * (CURR_HEIGHT + 8),
    }));
    const progY = currY + groupHeight / 2 - PROG_HEIGHT / 2;
    layouts.push({ prog, color: COLORS[pi % COLORS.length], progY, curricula });
    currY += groupHeight + 32;
  });

  const totalHeight = currY + V_PAD;
  const totalWidth = PROG_WIDTH + H_GAP + CURR_WIDTH + 20;

  return (
    <div style={{ overflowX: "auto", width: "100%" }}>
      <svg
        width={totalWidth}
        height={totalHeight}
        viewBox={`0 0 ${totalWidth} ${totalHeight}`}
        style={{ display: "block" }}
      >
        {layouts.map(({ prog, color, progY, curricula }) => {
          const progCenterX = PROG_WIDTH / 2;
          const progCenterY = progY + PROG_HEIGHT / 2;
          const currStartX = PROG_WIDTH + H_GAP;

          return (
            <g key={prog.program_name}>
              {/* Program node */}
              <rect
                x={0}
                y={progY}
                width={PROG_WIDTH}
                height={PROG_HEIGHT}
                rx={7}
                fill="#ffffff"
                stroke={color}
                strokeWidth={1.5}
              />
              <text
                x={PROG_WIDTH / 2}
                y={progY + PROG_HEIGHT / 2 + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "12px",
                  fontWeight: 600,
                  fill: "#111827",
                }}
              >
                {prog.program_name.length > 24
                  ? prog.program_name.slice(0, 22) + "…"
                  : prog.program_name}
              </text>

              {/* Connector lines and curriculum nodes */}
              {curricula.map(({ name, y }) => {
                const currCenterY = y + CURR_HEIGHT / 2;
                const mx = PROG_WIDTH + H_GAP / 2;
                return (
                  <g key={name}>
                    <path
                      d={`M ${progCenterX + PROG_WIDTH / 2} ${progCenterY} C ${mx} ${progCenterY}, ${mx} ${currCenterY}, ${currStartX} ${currCenterY}`}
                      fill="none"
                      stroke={color}
                      strokeWidth={1}
                      strokeOpacity={0.45}
                    />
                    <rect
                      x={currStartX}
                      y={y}
                      width={CURR_WIDTH}
                      height={CURR_HEIGHT}
                      rx={5}
                      fill="#fafaf9"
                      stroke="#e4e2dc"
                      strokeWidth={1}
                    />
                    <text
                      x={currStartX + 10}
                      y={y + CURR_HEIGHT / 2 + 1}
                      dominantBaseline="middle"
                      style={{
                        fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                        fontSize: "11px",
                        fontWeight: 400,
                        fill: "#374151",
                      }}
                    >
                      {name.length > 28 ? name.slice(0, 26) + "…" : name}
                    </text>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
