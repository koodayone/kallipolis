"use client";

import { DomainKey } from "@/lib/atlasScene";

const DOMAIN_NAMES: Record<DomainKey, string> = {
  government: "Government",
  college: "College",
  industry: "Industry",
};

// 11 rays fanning upward from the center-bottom of the viewbox (cx=28, cy=36)
// Angles in degrees: 0° = up, positive = clockwise
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

function RisingSun() {
  const cx = 28, cy = 36;
  const innerR = 15; // gap between disc edge and ray start

  return (
    <svg
      width="94"
      height="60"
      viewBox="0 0 56 36"
      fill="none"
      style={{ animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block", margin: "0 auto" }}
    >
      <defs>
        <clipPath id="sun-clip">
          <rect x="0" y="0" width="56" height="37" />
        </clipPath>
      </defs>
      {/* Rays + disc clipped to flat bottom */}
      <g clipPath="url(#sun-clip)">
      {RAYS.map((r, i) => {
        const rad = toRad(r.angle - 90); // -90 to rotate so 0° points up
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
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        );
      })}
      {/* Sun half-disc */}
      <path
        d={`M ${cx - innerR} ${cy} A ${innerR} ${innerR} 0 0 1 ${cx + innerR} ${cy} Z`}
        fill="#c9a84c"
      />
      </g>
    </svg>
  );
}

type Props = {
  hoveredDomain: DomainKey | null;
};

export default function AtlasLabels({ hoveredDomain }: Props) {
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

      {/* Sun + domain label — fade in together on hover */}
      <div
        style={{
          position: "absolute",
          top: "calc(24% - 74px)",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 1 : 0,
          transition: "opacity 0.5s ease-in-out",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <RisingSun />
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "18px",
            fontWeight: 600,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "#ffffff",
            whiteSpace: "nowrap",
          }}
        >
          {hoveredDomain ? DOMAIN_NAMES[hoveredDomain] : ""}
        </span>
      </div>

      {/* Institution logo + instruction — fades out when a domain is hovered */}
      <div
        style={{
          position: "absolute",
          top: "calc(24% - 74px)",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 0 : 1,
          transition: "opacity 0.5s ease-in-out",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "10px",
        }}
      >
        <img
          src="/foothill-logo-2.png"
          alt="Foothill College"
          style={{ height: "72px", width: "auto", objectFit: "contain" }}
        />
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "15px",
            letterSpacing: "0.1em",
            color: "rgba(255,255,255,0.85)",
            textTransform: "uppercase",
            whiteSpace: "nowrap",
          }}
        >
          Select a domain
        </span>
      </div>
    </div>
  );
}
