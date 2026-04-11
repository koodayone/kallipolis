const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Props = {
  source: string;
};

export default function DataCitation({ source }: Props) {
  return (
    <div style={{
      paddingTop: "12px",
      borderTop: "1px solid rgba(255,255,255,0.05)",
      fontFamily: FONT,
      fontSize: "11px",
      color: "rgba(255,255,255,0.4)",
      letterSpacing: "0.02em",
    }}>
      Source: {source}
    </div>
  );
}
