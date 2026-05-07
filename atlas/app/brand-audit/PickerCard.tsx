"use client";

import { useState } from "react";

export type PickerRow = {
  id: string;
  name: string;
  url: string;
  thumb?: string;
  logoCrop?: string;
  status: string;
  error?: string | null;
  currentHex: string | null;
  rawHex: string | null;
  neonHex: string | null;
  generatedHex: string | null;
  proposedSource: string | null;
  confidence: string | null;
  dominance: number | null;
  note: string | null;
  delta: number;
};

type Pick = { hex: string; source: string; updated_at: string };

function isValidHex(s: string): boolean {
  return /^#?[0-9a-fA-F]{6}$/.test(s.trim());
}

function normHex(s: string): string {
  const t = s.trim();
  return (t.startsWith("#") ? t : `#${t}`).toLowerCase();
}

export default function PickerCard({
  row,
  initialPick,
}: {
  row: PickerRow;
  initialPick: Pick | null;
}) {
  const [pick, setPick] = useState<Pick | null>(initialPick);
  const [custom, setCustom] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  async function persistPick(hex: string, source: string) {
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch("/api/brand-picks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: row.id, hex, source }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error ?? `HTTP ${res.status}`);
      }
      const j = await res.json();
      setPick(j.pick);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function clearPick() {
    setBusy(true);
    setErr(null);
    try {
      await fetch(`/api/brand-picks?id=${encodeURIComponent(row.id)}`, {
        method: "DELETE",
      });
      setPick(null);
    } finally {
      setBusy(false);
    }
  }

  const candidates: Array<{ label: string; hex: string | null; source: string; sub: string }> = [
    { label: "Current", hex: row.currentHex, source: "current", sub: "live in atlas" },
    { label: "Generated", hex: row.generatedHex, source: "generated", sub: "logo file" },
    { label: "Raw", hex: row.rawHex, source: "raw", sub: row.proposedSource ?? "—" },
    { label: "Neon", hex: row.neonHex, source: "neon", sub: "HSL lift" },
  ];

  const driftBucket =
    row.delta < 0 ? "pending" :
    row.delta < 0.05 ? "match" :
    row.delta < 0.18 ? "near" :
    "drift";
  const driftLabel = { pending: "Pending", match: "Match", near: "Near", drift: "Drift" }[driftBucket];
  const driftColor = {
    pending: "rgba(255,255,255,0.35)",
    match: "rgba(120, 200, 140, 0.85)",
    near: "rgba(220, 180, 90, 0.85)",
    drift: "rgba(220, 100, 100, 0.95)",
  }[driftBucket];

  const pickedHex = pick?.hex ?? null;

  return (
    <div style={{
      borderRadius: 8,
      overflow: "hidden",
      background: pickedHex ? "rgba(255,255,255,0.05)" : "rgba(255,255,255,0.03)",
      border: pickedHex ? `2px solid ${pickedHex}` : "1px solid rgba(255,255,255,0.08)",
      display: "flex",
      flexDirection: "column",
      transition: "border-color 0.15s ease",
    }}>
      <a
        href={row.url}
        target="_blank"
        rel="noreferrer noopener"
        style={{ display: "block", position: "relative", aspectRatio: "1280 / 600", background: "#0a1428" }}
        title={`Open ${row.name} homepage`}
      >
        {row.thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={row.thumb}
            alt={`Header of ${row.name}`}
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }}
          />
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontFamily: "var(--font-inter), sans-serif", fontSize: 12, color: "rgba(255,255,255,0.4)" }}>
            No capture {row.error ? `· ${row.error}` : ""}
          </div>
        )}
      </a>

      {row.logoCrop && row.thumb && (
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "8px 18px", display: "flex", alignItems: "center", gap: 12, background: "rgba(0,0,0,0.25)" }}>
          <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", flexShrink: 0 }}>
            Logo crop
          </span>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={row.logoCrop}
            alt={`Logo region read for ${row.name}`}
            style={{ height: 36, border: "1px solid rgba(255,255,255,0.1)", background: "#fff" }}
          />
          {row.dominance !== null && (
            <span style={{ fontSize: 10, color: "rgba(255,255,255,0.45)", marginLeft: "auto" }}>
              {Math.round(row.dominance * 100)}% dom
            </span>
          )}
        </div>
      )}

      <div style={{ padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0, flex: 1 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {row.name}
            </span>
            <a
              href={row.url}
              target="_blank"
              rel="noreferrer noopener"
              style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", textDecoration: "none", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
            >
              {row.url.replace(/^https?:\/\//, "").replace(/\/$/, "")} ↗
            </a>
          </div>
          <span style={{
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            padding: "3px 8px",
            borderRadius: 999,
            background: "rgba(255,255,255,0.04)",
            color: driftColor,
            border: `1px solid ${driftColor}`,
            flexShrink: 0,
            whiteSpace: "nowrap",
          }}>
            {driftLabel}
          </span>
        </div>

        {/* Click-to-pick swatches */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {candidates.map(({ label, hex, source, sub }) => {
            const isPicked = pickedHex && hex && pickedHex.toLowerCase() === hex.toLowerCase();
            const disabled = !hex || busy;
            return (
              <button
                key={label}
                onClick={() => hex && persistPick(hex, source)}
                disabled={disabled}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 10px",
                  borderRadius: 4,
                  border: isPicked
                    ? `2px solid ${hex}`
                    : "1px solid rgba(255,255,255,0.10)",
                  background: isPicked ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.18)",
                  cursor: disabled ? "default" : "pointer",
                  opacity: disabled && !isPicked ? 0.45 : 1,
                  textAlign: "left",
                  fontFamily: "inherit",
                  color: "inherit",
                  transition: "background 0.1s ease",
                }}
                title={hex ? `Use ${hex} (${source})` : "no candidate"}
              >
                <span style={{
                  width: 24,
                  height: 24,
                  borderRadius: 3,
                  background: hex ?? "transparent",
                  border: hex ? "1px solid rgba(255,255,255,0.15)" : "1px dashed rgba(255,255,255,0.2)",
                  flexShrink: 0,
                }} />
                <span style={{ display: "flex", flexDirection: "column", minWidth: 0, flex: 1 }}>
                  <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.10em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)" }}>
                    {label} {isPicked ? "✓" : ""}
                  </span>
                  <span style={{ fontFamily: "Menlo, monospace", fontSize: 11, color: "#fff" }}>
                    {hex ?? "—"}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        {/* Custom hex input — native color spectrum + text */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* Native color picker — full RGB spectrum. Click to open the
              OS color wheel; selection writes back to the text input. */}
          <input
            type="color"
            value={isValidHex(custom) ? normHex(custom) : "#ffffff"}
            onChange={(e) => setCustom(e.target.value)}
            title="Open full color spectrum picker"
            style={{
              width: 28,
              height: 28,
              padding: 0,
              border: "1px solid rgba(255,255,255,0.20)",
              borderRadius: 3,
              background: "transparent",
              cursor: "pointer",
              flexShrink: 0,
            }}
          />
          <input
            type="text"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            placeholder="#rrggbb custom"
            style={{
              flex: 1,
              padding: "5px 8px",
              borderRadius: 3,
              border: "1px solid rgba(255,255,255,0.10)",
              background: "rgba(0,0,0,0.20)",
              color: "#fff",
              fontFamily: "Menlo, monospace",
              fontSize: 11,
              minWidth: 0,
            }}
          />
          <button
            onClick={() => isValidHex(custom) && persistPick(normHex(custom), "custom")}
            disabled={!isValidHex(custom) || busy}
            style={{
              padding: "5px 10px",
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              borderRadius: 3,
              border: "1px solid rgba(255,255,255,0.20)",
              background: isValidHex(custom) ? "rgba(120, 200, 140, 0.20)" : "rgba(255,255,255,0.04)",
              color: "#fff",
              cursor: isValidHex(custom) && !busy ? "pointer" : "default",
              opacity: isValidHex(custom) ? 1 : 0.5,
            }}
          >
            Pick
          </button>
        </div>

        {/* Pick state row */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "rgba(255,255,255,0.55)" }}>
          {pick ? (
            <>
              <span style={{
                width: 14,
                height: 14,
                borderRadius: 2,
                background: pick.hex,
                border: "1px solid rgba(255,255,255,0.18)",
                flexShrink: 0,
              }} />
              <span style={{ fontFamily: "Menlo, monospace", color: "#fff" }}>{pick.hex}</span>
              <span style={{ color: "rgba(255,255,255,0.4)" }}>· {pick.source}</span>
              <button
                onClick={clearPick}
                disabled={busy}
                style={{
                  marginLeft: "auto",
                  padding: "2px 8px",
                  fontSize: 9,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  borderRadius: 2,
                  border: "1px solid rgba(220, 100, 100, 0.40)",
                  background: "transparent",
                  color: "rgba(220, 100, 100, 0.85)",
                  cursor: busy ? "default" : "pointer",
                }}
              >
                Clear
              </button>
            </>
          ) : (
            <span style={{ fontStyle: "italic" }}>No pick yet — click a swatch above</span>
          )}
        </div>

        {err && (
          <span style={{ fontSize: 11, color: "rgba(220, 100, 100, 0.95)" }}>
            {err}
          </span>
        )}

        {row.note && (
          <span style={{ fontSize: 11, color: "rgba(220, 180, 90, 0.85)", lineHeight: 1.5 }}>
            {row.note}
          </span>
        )}
      </div>
    </div>
  );
}
