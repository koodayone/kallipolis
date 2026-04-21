"use client";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

export type RequiredSkillItem = { skill: string };

type Props = {
  skills: RequiredSkillItem[];
  brandColor: string;
  collegeName: string;
};

export default function RequiredSkillsList({ skills, brandColor, collegeName }: Props) {
  if (skills.length === 0) return null;
  return (
    <div>
      <span
        style={{ display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "10px", position: "relative" }}
        onMouseEnter={(e) => { const tip = e.currentTarget.querySelector("[data-tooltip]") as HTMLElement; if (tip) tip.style.opacity = "1"; }}
        onMouseLeave={(e) => { const tip = e.currentTarget.querySelector("[data-tooltip]") as HTMLElement; if (tip) tip.style.opacity = "0"; }}
      >
        <span style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase",
          color: brandColor, opacity: 0.6,
        }}>
          Required Skills ({skills.length})
        </span>
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none"
          style={{ cursor: "help", opacity: 0.4, transition: "opacity 0.15s" }}
          onMouseEnter={(e) => { (e.currentTarget as SVGSVGElement).style.opacity = "0.7"; }}
          onMouseLeave={(e) => { (e.currentTarget as SVGSVGElement).style.opacity = "0.4"; }}
        >
          <circle cx="8" cy="8" r="7" stroke={brandColor} strokeWidth="1" />
          <circle cx="8" cy="4.5" r="0.8" fill={brandColor} />
          <rect x="7.2" y="6.5" width="1.6" height="5" rx="0.8" fill={brandColor} />
        </svg>
        <span data-tooltip style={{
          position: "absolute", left: 0, bottom: "calc(100% + 6px)", zIndex: 10,
          background: "rgba(20,18,28,0.95)", border: `1px solid ${brandColor}20`,
          borderRadius: "8px", padding: "10px 14px", width: "260px",
          fontFamily: FONT, fontSize: "11px", fontWeight: 400, letterSpacing: "0",
          textTransform: "none", color: "rgba(255,255,255,0.55)", lineHeight: 1.5,
          opacity: 0, pointerEvents: "none", transition: "opacity 0.15s",
        }}>
          Skills this role requires that {collegeName} courses develop.
        </span>
      </span>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {skills.map((s) => (
          <div key={s.skill} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <circle cx="6" cy="6" r="5" stroke={brandColor} strokeWidth="1" />
              <path d="M4 6l1.5 1.5L8 5" stroke={brandColor} strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span style={{ fontFamily: FONT, fontSize: "13px", color: brandColor }}>{s.skill}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
