"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";
import { SchoolConfig } from "@/config/schoolConfig";

const FONT = "var(--font-inter), Inter, system-ui, sans-serif";

export type Column = {
  label: string;
  width: string;
  align?: "left" | "right" | "center";
};

type Props<T> = {
  items: T[];
  initialCap: number;
  batchSize: number;
  columns: Column[];
  renderRow: (item: T, index: number) => ReactNode;
  keyExtractor: (item: T) => string;
  entityName: string;
  school: SchoolConfig;
};

export default function EntityScrollList<T>({
  items, initialCap, batchSize, columns, renderRow, keyExtractor, entityName, school,
}: Props<T>) {
  const [visibleCount, setVisibleCount] = useState(initialCap);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Reset when items change (e.g., new search results)
  useEffect(() => { setVisibleCount(initialCap); }, [items, initialCap]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && visibleCount < items.length) {
        setVisibleCount((prev) => Math.min(prev + batchSize, items.length));
      }
    }, { threshold: 0.1 });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [visibleCount, items.length, batchSize]);

  const visible = items.slice(0, visibleCount);

  const hdrStyle: React.CSSProperties = {
    fontFamily: FONT, fontSize: "10px", fontWeight: 600,
    letterSpacing: "0.1em", textTransform: "uppercase",
    color: school.brandColorLight, opacity: 0.6,
  };

  const gridTemplate = `24px ${columns.map((c) => c.width).join(" ")}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {/* Column headers */}
      <div style={{
        display: "grid", gridTemplateColumns: gridTemplate,
        padding: "12px 16px", gap: "10px", alignItems: "center",
      }}>
        <span />
        {columns.map((col) => (
          <span key={col.label} style={{ ...hdrStyle, textAlign: col.align ?? "left" }}>
            {col.label}
          </span>
        ))}
      </div>

      {visible.map((item, i) => (
        <div key={keyExtractor(item)}>{renderRow(item, i)}</div>
      ))}

      {visibleCount < items.length && (
        <div ref={sentinelRef} style={{ padding: "14px", textAlign: "center" }}>
          <p style={{ fontFamily: FONT, fontSize: "12px", color: "rgba(255,255,255,0.25)" }}>
            Showing {visibleCount} of {items.length.toLocaleString()} {entityName}...
          </p>
        </div>
      )}
      {items.length === 0 && (
        <p style={{ fontFamily: FONT, fontSize: "14px", color: "rgba(255,255,255,0.35)", padding: "40px 0", textAlign: "center" }}>
          No {entityName} match that query. Try a different question.
        </p>
      )}
    </div>
  );
}
