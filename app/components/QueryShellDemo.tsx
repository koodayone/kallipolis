"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// ── Scene definitions — one per analytical form ─────────────────────────────

type ResultRow = {
  id: string;
  label: string;
  detail: string;
};

type Scene = {
  form: string;
  query: string;
  message: string;
  results: ResultRow[];
};

const SCENES: Scene[] = [
  {
    form: "Students",
    query: "students in advanced manufacturing with highest GPA",
    message: "Found 3 students in manufacturing programs ranked by GPA with skill alignment.",
    results: [
      { id: "S-0412", label: "Industrial Technology", detail: "GPA 3.91 · 11 courses · 7 aligned skills" },
      { id: "S-0738", label: "CNC Machining", detail: "GPA 3.87 · 9 courses · 6 aligned skills" },
      { id: "S-1055", label: "Welding Technology", detail: "GPA 3.82 · 10 courses · 5 aligned skills" },
    ],
  },
  {
    form: "Courses",
    query: "courses that develop industrial manufacturing skills",
    message: "Found 3 courses developing industrial manufacturing competencies across 2 departments.",
    results: [
      { id: "MFGT 110", label: "Introduction to Manufacturing Processes", detail: "Machine operations · safety protocols · quality control" },
      { id: "MFGT 210", label: "Computer-Aided Manufacturing", detail: "CAM software · toolpath planning · production workflows" },
      { id: "WELD 101", label: "Industrial Welding Fundamentals", detail: "Arc welding · blueprint reading · materials science" },
    ],
  },
  {
    form: "Occupations",
    query: "highest paying manufacturing occupations in our region",
    message: "Found 3 occupations in the manufacturing sector ranked by annual wage.",
    results: [
      { id: "17-2112", label: "Industrial Engineers", detail: "$108,200 · 340 openings · 6.4% growth" },
      { id: "51-4041", label: "Machinists", detail: "$58,400 · 890 openings · 4.8% growth" },
      { id: "51-4011", label: "CNC Tool Operators", detail: "$52,100 · 1,240 openings · 5.2% growth" },
    ],
  },
  {
    form: "Employers",
    query: "employers aligned with our manufacturing program",
    message: "Found 3 employers with strong skill alignment to manufacturing curriculum.",
    results: [
      { id: "94.2%", label: "Pacific Precision Manufacturing", detail: "Aerospace components · 12 aligned roles" },
      { id: "89.7%", label: "Central Valley Fabrication", detail: "Industrial metalwork · 8 aligned roles" },
      { id: "86.1%", label: "Sierra Machining Group", detail: "CNC contract manufacturing · 6 aligned roles" },
    ],
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

  // Intersection observer
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

    // Step 1: Pause, then start typing
    timerRef.current = setTimeout(() => {
      setPhase("typing");

      let i = 0;
      intervalRef.current = setInterval(() => {
        i++;
        setTypedText(s.query.slice(0, i));
        if (i >= s.query.length) {
          if (intervalRef.current) clearInterval(intervalRef.current);

          // Step 2: Pause after typing, then loading
          timerRef.current = setTimeout(() => {
            setPhase("loading");

            // Step 3: Loading → results
            timerRef.current = setTimeout(() => {
              setShowResults(true);
              setPhase("results");

              // Step 4: Hold results, then advance to next scene
              timerRef.current = setTimeout(() => {
                setPhase("hold");

                // Brief fade gap, then next scene
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

  // Start on visibility
  useEffect(() => {
    if (!visible) return;
    runScene(0);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [visible, runScene]);

  return (
    <div ref={containerRef} style={{ maxWidth: 640, margin: "0 auto" }}>

      {/* Form indicator */}
      <div style={{ marginBottom: 12, transition: "opacity 0.4s ease", opacity: phase === "hold" ? 0.3 : 1 }}>
        <span style={{
          fontSize: 11, fontWeight: 700, textTransform: "uppercase",
          letterSpacing: "0.12em", color: "#f0425e",
        }}>
          {scene.form}
        </span>
      </div>

      {/* Input area */}
      <div
        style={{
          position: "relative",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 10,
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          transition: "opacity 0.4s ease",
          opacity: phase === "hold" ? 0.3 : 1,
        }}
      >
        {/* ? button */}
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            border: "1px solid rgba(240,66,94,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: phase === "idle" ? "0 0 8px rgba(240,66,94,0.2)" : "none",
            transition: "box-shadow 0.6s ease",
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 600, color: "#f0425e" }}>?</span>
        </div>

        {/* Input display */}
        <div style={{ flex: 1, minHeight: 20 }}>
          {typedText ? (
            <span style={{ fontSize: 15, color: "rgba(255,255,255,0.85)" }}>
              {typedText}
              {phase === "typing" && (
                <span style={{ opacity: 0.6, animation: "blink 1s step-end infinite" }}>|</span>
              )}
            </span>
          ) : (
            <span style={{ fontSize: 15, color: "rgba(255,255,255,0.25)" }}>
              Ask anything about this college...
            </span>
          )}
        </div>

        {/* Loading indicator */}
        {phase === "loading" && (
          <div style={{
            width: 16, height: 16, borderRadius: "50%",
            border: "2px solid rgba(240,66,94,0.2)",
            borderTopColor: "#f0425e",
            animation: "spin 0.8s linear infinite",
          }} />
        )}
      </div>

      {/* Results */}
      <div
        style={{
          maxHeight: showResults ? 400 : 0,
          opacity: showResults && phase !== "hold" ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.5s ease, opacity 0.4s ease",
          marginTop: 16,
        }}
      >
        {/* Result message */}
        <p style={{
          fontSize: 13, color: "rgba(255,255,255,0.4)", marginBottom: 12,
          lineHeight: 1.5,
        }}>
          {scene.message}
        </p>

        {/* Result rows */}
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {scene.results.map((r, i) => (
            <div
              key={r.id}
              style={{
                display: "grid",
                gridTemplateColumns: "76px 1fr",
                gap: 16,
                padding: "12px 16px",
                background: "rgba(255,255,255,0.03)",
                borderBottom: i < scene.results.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, color: "#f0425e", fontFamily: "monospace" }}>
                {r.id}
              </span>
              <div>
                <span style={{ fontSize: 14, color: "rgba(255,255,255,0.8)", display: "block" }}>
                  {r.label}
                </span>
                <span style={{ fontSize: 12, color: "rgba(255,255,255,0.35)" }}>
                  {r.detail}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
