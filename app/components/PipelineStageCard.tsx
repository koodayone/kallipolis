type Props = {
  number: string;
  name: string;
  inputs: string;
  outputs: string;
  methodology: string;
};

const BRAND = "#4fd1fd";

export default function PipelineStageCard({ number, name, inputs, outputs, methodology }: Props) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: 8,
      padding: "24px 28px",
      flex: 1,
      display: "flex",
      flexDirection: "column",
      gap: 16,
    }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          border: `1px solid ${BRAND}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: BRAND }}>{number}</span>
        </div>
        <h4 style={{
          fontFamily: "var(--font-days-one)", fontWeight: 400,
          fontSize: 18, color: "rgba(255,255,255,0.9)", margin: 0,
        }}>
          {name}
        </h4>
      </div>

      {/* Methodology */}
      <p style={{ fontSize: 14, lineHeight: 1.65, color: "rgba(255,255,255,0.6)", margin: 0 }}>
        {methodology}
      </p>

      {/* Inputs / Outputs */}
      <div style={{ display: "flex", gap: 24, borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 12 }}>
        <div style={{ flex: 1 }}>
          <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "rgba(255,255,255,0.25)", display: "block", marginBottom: 4 }}>
            Inputs
          </span>
          <p style={{ fontSize: 13, lineHeight: 1.5, color: "rgba(255,255,255,0.5)", margin: 0 }}>
            {inputs}
          </p>
        </div>
        <div style={{ flex: 1 }}>
          <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: `${BRAND}90`, display: "block", marginBottom: 4 }}>
            Outputs
          </span>
          <p style={{ fontSize: 13, lineHeight: 1.5, color: "rgba(255,255,255,0.5)", margin: 0 }}>
            {outputs}
          </p>
        </div>
      </div>
    </div>
  );
}
