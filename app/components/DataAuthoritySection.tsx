type Props = {
  unitName: string;
  authorityName: string;
  logoPath?: string;
  whatData: string;
  whatTransformation: string;
  whyThisSource: string;
  limitation: string;
  invitation: string;
};

export default function DataAuthoritySection({
  unitName,
  authorityName,
  logoPath,
  whatData,
  whatTransformation,
  whyThisSource,
  limitation,
  invitation,
}: Props) {
  return (
    <div
      style={{
        background: "rgba(255,255,255,0.03)",
        borderLeft: "3px solid #c9a84c",
        borderRadius: "0 8px 8px 0",
        padding: "32px 32px 28px",
        marginBottom: 24,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <span style={{
            fontSize: 11, fontWeight: 700, textTransform: "uppercase",
            letterSpacing: "0.12em", color: "#c9a84c", display: "block", marginBottom: 6,
          }}>
            {unitName}
          </span>
          <h3 style={{
            fontFamily: "var(--font-days-one)", fontWeight: 400,
            fontSize: 22, color: "rgba(255,255,255,0.9)", margin: 0,
          }}>
            {authorityName}
          </h3>
        </div>
        {logoPath && (
          <img
            src={logoPath}
            alt={`${authorityName} logo`}
            style={{ height: 40, width: "auto", opacity: 0.7, flexShrink: 0, marginLeft: 16 }}
          />
        )}
      </div>

      {/* Content rows */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <Row label="What data" text={whatData} />
        <Row label="What transformation" text={whatTransformation} />
        <Row label="Why this source" text={whyThisSource} />
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 16 }}>
          <Row label="Current limitation" text={limitation} />
          <div style={{ marginTop: 12, paddingLeft: 16, borderLeft: "2px solid rgba(201,168,76,0.25)" }}>
            <span style={{
              fontSize: 11, fontWeight: 600, textTransform: "uppercase",
              letterSpacing: "0.1em", color: "rgba(201,168,76,0.7)", display: "block", marginBottom: 4,
            }}>
              Invitation to collaborate
            </span>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: "rgba(255,255,255,0.6)", margin: 0 }}>
              {invitation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <span style={{
        fontSize: 10, fontWeight: 600, textTransform: "uppercase",
        letterSpacing: "0.1em", color: "rgba(255,255,255,0.3)", display: "block", marginBottom: 4,
      }}>
        {label}
      </span>
      <p style={{ fontSize: 15, lineHeight: 1.65, color: "rgba(255,255,255,0.7)", margin: 0 }}>
        {text}
      </p>
    </div>
  );
}
