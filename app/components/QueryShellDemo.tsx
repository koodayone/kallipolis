"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// ── RisingSun (always gold) ─────────────────────────────────────────────────

const SUN_RAYS = [
  { angle: -90, long: true  }, { angle: -75, long: false },
  { angle: -60, long: true  }, { angle: -45, long: false },
  { angle: -30, long: true  }, { angle: -15, long: false },
  { angle:   0, long: true  }, { angle:  15, long: false },
  { angle:  30, long: true  }, { angle:  45, long: false },
  { angle:  60, long: true  }, { angle:  75, long: false },
  { angle:  90, long: true  },
];

function toRad(deg: number) { return (deg * Math.PI) / 180; }

function RisingSun({ size = 90, opacity = 1 }: { size?: number; opacity?: number }) {
  const cx = 28, cy = 36, innerR = 15;
  const c = "#c9a84c";
  return (
    <svg
      width={size} height={size * 0.6} viewBox="0 0 56 36" fill="none"
      style={{ filter: `drop-shadow(0 0 8px ${c}55)`, animation: "sun-glow 3s ease-in-out infinite", overflow: "hidden", display: "block", margin: "0 auto", opacity }}
    >
      <defs><clipPath id="qs-sun-clip"><rect x="0" y="0" width="56" height="37" /></clipPath></defs>
      <g clipPath="url(#qs-sun-clip)">
        {SUN_RAYS.map((r, i) => {
          const rad = toRad(r.angle - 90);
          const len = r.long ? 9 : 6;
          const x1 = cx + Math.cos(rad) * (innerR + 3);
          const y1 = cy + Math.sin(rad) * (innerR + 3);
          const x2 = cx + Math.cos(rad) * (innerR + 3 + len);
          const y2 = cy + Math.sin(rad) * (innerR + 3 + len);
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} className="sun-ray" style={{ stroke: c, animationDelay: `${i * 0.18}s` }} />;
        })}
        <path d={`M ${cx - innerR} ${cy} A ${innerR} ${innerR} 0 0 1 ${cx + innerR} ${cy} Z`} fill={c} />
      </g>
    </svg>
  );
}

// ── Scene definitions ───────────────────────────────────────────────────────

const ACCENT = "#f0425e";
const GOLD = "#c9a84c";

type Scene = {
  form: string;
  query: string;
  placeholder: string;
  message: string;
  renderResults: () => React.ReactNode;
};

function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ opacity: 0.2 }}>
      <path d="M4 2l4 4-4 4" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function StudentResults() {
  const grid = "24px 80px 1fr 70px 50px";
  const rows = [
    { id: "#412", focus: "Industrial Technology", courses: 11, gpa: 3.91 },
    { id: "#738", focus: "CNC Machining", courses: 9, gpa: 3.87 },
    { id: "#1055", focus: "Welding Technology", courses: 10, gpa: 3.82 },
  ];
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span /><span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Student</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Primary Focus</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>GPA</span>
      </div>
      {rows.map((s, i) => (
        <div key={s.id} style={{ display: "grid", gridTemplateColumns: grid, alignItems: "center", padding: "12px 16px", background: "rgba(255,255,255,0.03)", borderBottom: i < rows.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
          <Chevron /><span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.8)" }}>{s.id}</span>
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.55)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.focus}</span>
          <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.6)", textAlign: "right" }}>{s.courses}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: "rgba(74, 222, 128, 0.9)", textAlign: "right" }}>{s.gpa.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}

function CourseResults() {
  const grid = "24px 1fr auto";
  const courses = [
    { code: "MFGT 110", name: "Introduction to Manufacturing Processes" },
    { code: "MFGT 210", name: "Computer-Aided Manufacturing" },
    { code: "WELD 101", name: "Industrial Welding Fundamentals" },
  ];
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span /><span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Department</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Courses</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: grid, alignItems: "center", padding: "14px 16px", background: "rgba(255,255,255,0.06)" }}>
        <Chevron /><span style={{ fontSize: 14, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>Manufacturing Technology</span>
        <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textAlign: "right" }}>3 courses</span>
      </div>
      {courses.map((c, i) => (
        <div key={c.code} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px 10px 40px", background: "rgba(255,255,255,0.02)", borderBottom: i < courses.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "1px solid rgba(255,255,255,0.05)" }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: ACCENT, flexShrink: 0 }}>{c.code}</span>
          <span style={{ fontSize: 13, color: "rgba(255,255,255,0.75)" }}>{c.name}</span>
        </div>
      ))}
    </div>
  );
}

function OccupationResults() {
  const grid = "24px 1fr 90px 70px 80px";
  const rows = [
    { title: "Industrial Engineers", wage: 108200, openings: 340, growth: 6.4 },
    { title: "Machinists", wage: 58400, openings: 890, growth: 4.8 },
    { title: "CNC Tool Operators", wage: 52100, openings: 1240, growth: 5.2 },
  ];
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span /><span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Occupation</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Wage</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Openings</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Growth</span>
      </div>
      {rows.map((o, i) => (
        <div key={o.title} style={{ display: "grid", gridTemplateColumns: grid, alignItems: "center", padding: "12px 16px", background: "rgba(255,255,255,0.03)", borderBottom: i < rows.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
          <Chevron /><span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)" }}>{o.title}</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", textAlign: "right" }}>${o.wage.toLocaleString()}</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.45)", textAlign: "right" }}>{o.openings.toLocaleString()}/yr</span>
          <span style={{ fontSize: 12, fontWeight: 500, color: "#4ade80", textAlign: "right" }}>+{o.growth}%</span>
        </div>
      ))}
    </div>
  );
}

function EmployerResults() {
  const grid = "24px 1.2fr 1fr 60px 100px";
  const rows = [
    { name: "Pacific Precision Mfg.", sector: "Aerospace", roles: 12, skills: 18 },
    { name: "Central Valley Fabrication", sector: "Metalwork", roles: 8, skills: 14 },
    { name: "Sierra Machining Group", sector: "Contract Mfg.", roles: 6, skills: 11 },
  ];
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: grid, padding: "8px 16px", borderBottom: `1px solid ${ACCENT}20` }}>
        <span /><span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}90` }}>Employer</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60` }}>Sector</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "center" }}>Roles</span>
        <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${ACCENT}60`, textAlign: "right" }}>Skills</span>
      </div>
      {rows.map((e, i) => (
        <div key={e.name} style={{ display: "grid", gridTemplateColumns: grid, alignItems: "center", padding: "12px 16px", background: "rgba(255,255,255,0.03)", borderBottom: i < rows.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
          <Chevron /><span style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.name}</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{e.sector}</span>
          <span style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", textAlign: "center" }}>{e.roles}</span>
          <span style={{ fontSize: 11, color: ACCENT, background: `${ACCENT}20`, border: `1px solid ${ACCENT}30`, borderRadius: 100, padding: "3px 8px", textAlign: "center", whiteSpace: "nowrap", textTransform: "uppercase", letterSpacing: "0.05em" }}>{e.skills} Skills</span>
        </div>
      ))}
    </div>
  );
}

const SCENES: Scene[] = [
  {
    form: "Students",
    query: "students in advanced manufacturing with highest GPA",
    placeholder: "Ask me a question about students.",
    message: "Found 3 students in manufacturing programs ranked by GPA with skill alignment.",
    renderResults: () => <StudentResults />,
  },
  {
    form: "Courses",
    query: "courses that develop industrial manufacturing skills",
    placeholder: "Ask me a question about courses.",
    message: "Found 3 courses developing industrial manufacturing competencies.",
    renderResults: () => <CourseResults />,
  },
  {
    form: "Occupations",
    query: "highest paying manufacturing occupations in our region",
    placeholder: "Ask me a question about occupations.",
    message: "Found 3 occupations in the manufacturing sector ranked by annual wage.",
    renderResults: () => <OccupationResults />,
  },
  {
    form: "Employers",
    query: "employers aligned with our manufacturing program",
    placeholder: "Ask me a question about employers.",
    message: "Found 3 employers with strong skill alignment to manufacturing curriculum.",
    renderResults: () => <EmployerResults />,
  },
];

// ── Component ───────────────────────────────────────────────────────────────

type Phase = "idle" | "typing" | "loading" | "results" | "hold";

export default function QueryShellDemo() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [sceneIndex, setSceneIndex] = useState(0);
  const [typedText, setTypedText] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [visible, setVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const scene = SCENES[sceneIndex];

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !visible) setVisible(true); },
      { threshold: 0.3 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible]);

  const runScene = useCallback((idx: number) => {
    const s = SCENES[idx];
    setSceneIndex(idx);
    setTypedText("");
    setShowResults(false);
    setPhase("idle");

    timerRef.current = setTimeout(() => {
      setPhase("typing");
      let i = 0;
      intervalRef.current = setInterval(() => {
        i++;
        setTypedText(s.query.slice(0, i));
        if (i >= s.query.length) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          timerRef.current = setTimeout(() => {
            setPhase("loading");
            timerRef.current = setTimeout(() => {
              setShowResults(true);
              setPhase("results");
              timerRef.current = setTimeout(() => {
                setPhase("hold");
                timerRef.current = setTimeout(() => {
                  runScene((idx + 1) % SCENES.length);
                }, 1200);
              }, 5000);
            }, 1400);
          }, 600);
        }
      }, 80);
    }, 2000);
  }, []);

  useEffect(() => {
    if (!visible) return;
    runScene(0);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [visible, runScene]);

  const isActive = phase !== "hold";

  return (
    <div ref={containerRef} style={{ maxWidth: 760, margin: "0 auto", padding: "0 40px" }}>

      {/* Sun — always gold, centered */}
      <div style={{ textAlign: "center", marginBottom: 24, transition: "opacity 0.4s ease", opacity: isActive ? 1 : 0.3 }}>
        <RisingSun size={90} />
      </div>

      {/* Input — matches real QueryShell */}
      <div style={{ position: "relative", transition: "opacity 0.4s ease", opacity: isActive ? 1 : 0.3 }}>
        <div
          style={{
            width: "100%",
            padding: "18px 48px 18px 24px",
            background: "rgba(255,255,255,0.04)",
            border: `1px solid ${phase === "typing" || phase === "loading" ? `${ACCENT}50` : "rgba(255,255,255,0.10)"}`,
            borderRadius: 16,
            boxShadow: phase === "typing" || phase === "loading" ? `0 0 0 3px ${ACCENT}15` : "none",
            transition: "border-color 0.2s, box-shadow 0.2s",
            minHeight: 20,
          }}
        >
          {typedText ? (
            <span style={{ fontSize: 15, color: "#f0eef4" }}>
              {typedText}
              {phase === "typing" && <span style={{ opacity: 0.6, animation: "blink 1s step-end infinite" }}>|</span>}
            </span>
          ) : (
            <span style={{ fontSize: 15, color: "rgba(255,255,255,0.25)" }}>
              {scene.placeholder}
            </span>
          )}
        </div>

        {/* ? button — right side, subtle, matching real QueryShell */}
        <div style={{ position: "absolute", right: 16, top: "50%", transform: "translateY(-50%)" }}>
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" strokeWidth="1.2" stroke="rgba(255,255,255,0.25)" />
            <text x="8" y="11.5" textAnchor="middle" fontSize="10" fontWeight="600" fill="rgba(255,255,255,0.25)">?</text>
          </svg>
        </div>
      </div>

      {/* Results — form-specific row patterns */}
      <div
        style={{
          maxHeight: showResults ? 500 : 0,
          opacity: showResults && isActive ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.5s ease, opacity 0.4s ease",
          marginTop: 16,
        }}
      >
        <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", marginBottom: 12, lineHeight: 1.5 }}>
          {scene.message}
        </p>
        {scene.renderResults()}
      </div>
    </div>
  );
}
