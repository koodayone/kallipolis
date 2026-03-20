"use client";

import { useEffect, useState } from "react";
import { getInstitution, InstitutionSummary } from "@/lib/api";
import Card from "@/components/ui/Card";
import ProgramTree from "./ProgramTree";

export default function CollegeView() {
  const [data, setData] = useState<InstitutionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInstitution()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div style={{ padding: "56px 40px", maxWidth: "900px", margin: "0 auto" }}>
        <p style={{ color: "#9ca3af", fontFamily: "var(--font-inter), Inter, sans-serif", fontSize: "14px" }}>
          Unable to load institutional data. Ensure the backend is running.
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: "56px 40px", maxWidth: "900px", margin: "0 auto" }}>
        <div style={{ display: "flex", gap: "8px" }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="gold-dot"
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                background: "#c9a84c",
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  const totalCurricula = data.programs.reduce((sum, p) => sum + p.curricula.length, 0);

  return (
    <div
      style={{
        maxWidth: "960px",
        margin: "0 auto",
        padding: "56px 40px 80px",
        display: "flex",
        flexDirection: "column",
        gap: "40px",
      }}
    >
      {/* Institution summary */}
      <div>
        <h1
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "24px",
            fontWeight: 600,
            color: "#111827",
            letterSpacing: "-0.02em",
            marginBottom: "6px",
          }}
        >
          {data.institution_name}
        </h1>
        <p
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "14px",
            color: "#6b7280",
            marginBottom: "24px",
          }}
        >
          {data.region}
        </p>

        {/* Stats */}
        <div style={{ display: "flex", gap: "20px" }}>
          {[
            { label: "Programs", value: data.programs.length },
            { label: "Curricula", value: totalCurricula },
          ].map(({ label, value }) => (
            <div
              key={label}
              style={{
                background: "#ffffff",
                border: "1px solid #e4e2dc",
                borderRadius: "8px",
                padding: "16px 24px",
                minWidth: "120px",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "28px",
                  fontWeight: 600,
                  color: "#111827",
                  letterSpacing: "-0.03em",
                }}
              >
                {value}
              </div>
              <div
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "11px",
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: "#9ca3af",
                  marginTop: "4px",
                }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Relational visualization */}
      <div>
        <h2
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "#9ca3af",
            marginBottom: "20px",
          }}
        >
          Program Structure
        </h2>
        <Card style={{ padding: "28px" }}>
          <ProgramTree programs={data.programs} />
        </Card>
      </div>

      {/* Program cards */}
      <div>
        <h2
          style={{
            fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "#9ca3af",
            marginBottom: "20px",
          }}
        >
          Programs
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {data.programs.map((prog) => (
            <Card key={prog.program_name} style={{ padding: "24px" }}>
              <h3
                style={{
                  fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                  fontSize: "15px",
                  fontWeight: 600,
                  color: "#111827",
                  marginBottom: "12px",
                }}
              >
                {prog.program_name}
              </h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {prog.curricula.map((c) => (
                  <span
                    key={c}
                    style={{
                      display: "inline-block",
                      padding: "4px 12px",
                      background: "#fafaf9",
                      border: "1px solid #e4e2dc",
                      borderRadius: "100px",
                      fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                      fontSize: "12px",
                      color: "#374151",
                    }}
                  >
                    {c}
                  </span>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
