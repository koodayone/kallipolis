const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

type Column = {
  label: string;
  width: string;
  align?: "left" | "right" | "center";
};

type Props = {
  columns: Column[];
  gridTemplateColumns: string;
  brandColor: string;
};

export default function ColumnHeaders({ columns, gridTemplateColumns, brandColor }: Props) {
  return (
    <div style={{
      display: "grid", gridTemplateColumns,
      padding: "12px 16px", gap: "10px", alignItems: "center",
    }}>
      <span />
      {columns.map((col) => (
        <span key={col.label} style={{
          fontFamily: FONT, fontSize: "10px", fontWeight: 600,
          letterSpacing: "0.1em", textTransform: "uppercase",
          color: brandColor, opacity: 0.6,
          textAlign: col.align ?? "left",
        }}>
          {col.label}
        </span>
      ))}
    </div>
  );
}
