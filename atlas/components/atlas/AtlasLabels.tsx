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
  { angle: -72, long: false },
  { angle: -54, long: true  },
  { angle: -36, long: false },
  { angle: -18, long: true  },
  { angle:   0, long: false },
  { angle:  18, long: true  },
  { angle:  36, long: false },
  { angle:  54, long: true  },
  { angle:  72, long: false },
  { angle:  90, long: true  },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

function RisingSun() {
  const cx = 28, cy = 36;
  const innerR = 15; // gap between disc edge and ray start

  return (
    <svg
      width="56"
      height="44"
      viewBox="0 0 56 44"
      fill="none"
      style={{ animation: "sun-glow 3s ease-in-out infinite", overflow: "visible" }}
    >
      {/* Rays */}
      {RAYS.map((r, i) => {
        const rad = toRad(r.angle - 90); // -90 to rotate so 0° points up
        const len = r.long ? 11 : 7;
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
          style={{ height: "36px", width: "auto" }}
        />
        <span
          style={{
            fontFamily: "var(--font-days-one), sans-serif",
            fontSize: "20px",
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
          top: "calc(20% - 72px)",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 1 : 0,
          transition: "opacity 0.35s ease",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "14px",
        }}
      >
        <RisingSun />
        <span
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
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

      {/* Instruction — fades out when a domain is hovered */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          transform: "translateX(-50%)",
          opacity: hoveredDomain ? 0 : 1,
          transition: "opacity 0.2s ease",
          fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
          fontSize: "11px",
          letterSpacing: "0.1em",
          color: "rgba(255,255,255,0.2)",
          textTransform: "uppercase",
          whiteSpace: "nowrap",
        }}
      >
        Select a domain
      </div>
    </div>
  );
}
