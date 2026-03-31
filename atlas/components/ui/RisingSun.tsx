import React from "react";

const RAYS = [
  { angle: -90, long: true  },
  { angle: -75, long: false },
  { angle: -60, long: true  },
  { angle: -45, long: false },
  { angle: -30, long: true  },
  { angle: -15, long: false },
  { angle:   0, long: true  },
  { angle:  15, long: false },
  { angle:  30, long: true  },
  { angle:  45, long: false },
  { angle:  60, long: true  },
  { angle:  75, long: false },
  { angle:  90, long: true  },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

type Props = {
  style?: React.CSSProperties;
  color?: string;
};

export default function RisingSun({ style, color }: Props) {
  const cx = 28, cy = 36;
  const innerR = 15;
  const c = color ?? "#c9a84c";

  return (
    <svg
      width="94"
      height="60"
      viewBox="0 0 56 36"
      fill="none"
      style={{ filter: `drop-shadow(0 0 8px ${c}55)`, animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block", margin: "0 auto", ...style }}
    >
      <defs>
        <clipPath id="sun-clip">
          <rect x="0" y="0" width="56" height="37" />
        </clipPath>
      </defs>
      <g clipPath="url(#sun-clip)">
        {RAYS.map((r, i) => {
          const rad = toRad(r.angle - 90);
          const len = r.long ? 9 : 6;
          const x1 = cx + Math.cos(rad) * (innerR + 3);
          const y1 = cy + Math.sin(rad) * (innerR + 3);
          const x2 = cx + Math.cos(rad) * (innerR + 3 + len);
          const y2 = cy + Math.sin(rad) * (innerR + 3 + len);
          return (
            <line
              key={i}
              x1={x1} y1={y1}
              x2={x2} y2={y2}
              className="sun-ray"
              style={{ stroke: c, animationDelay: `${i * 0.18}s` }}
            />
          );
        })}
        <path
          d={`M ${cx - innerR} ${cy} A ${innerR} ${innerR} 0 0 1 ${cx + innerR} ${cy} Z`}
          fill={c}
        />
      </g>
    </svg>
  );
}
