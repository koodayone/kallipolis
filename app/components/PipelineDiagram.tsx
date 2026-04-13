const STAGES = [
  { number: "1", label: "Courses", description: "Catalog extraction and skill derivation", color: "#c9a84c" },
  { number: "2", label: "Occupations", description: "COE demand feed and OEWS supplement", color: "#c9a84c" },
  { number: "3", label: "Employers", description: "EDD scraping and LLM enrichment", color: "#c9a84c" },
  { number: "4", label: "Students", description: "Synthetic generation calibrated to DataMart", color: "#c9a84c" },
  { number: "5", label: "Ontology Assembly", description: "Graph loading into the unified knowledge model", color: "#FFCC33" },
];

export default function PipelineDiagram() {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {STAGES.map((stage, i) => (
          <div key={stage.number}>
            {/* Stage card */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                padding: "16px 24px",
                background: i === STAGES.length - 1 ? "rgba(255,204,51,0.06)" : "rgba(255,255,255,0.03)",
                border: `1px solid ${i === STAGES.length - 1 ? "rgba(255,204,51,0.15)" : "rgba(255,255,255,0.06)"}`,
                borderRadius: 8,
              }}
            >
              {/* Stage number */}
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  border: `1px solid ${stage.color}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 600, color: stage.color }}>
                  {stage.number}
                </span>
              </div>

              {/* Label + description */}
              <div>
                <span style={{
                  fontSize: 15, fontWeight: 600,
                  color: i === STAGES.length - 1 ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.75)",
                }}>
                  {stage.label}
                </span>
                <p style={{
                  fontSize: 13, color: "rgba(255,255,255,0.4)",
                  margin: "2px 0 0", lineHeight: 1.5,
                }}>
                  {stage.description}
                </p>
              </div>
            </div>

            {/* Connector line */}
            {i < STAGES.length - 1 && (
              <div style={{ display: "flex", justifyContent: "center", padding: "4px 0" }}>
                <div style={{ width: 1, height: 20, background: "rgba(201,168,76,0.25)" }} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
