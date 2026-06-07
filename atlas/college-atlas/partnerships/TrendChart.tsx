"use client";

import { useState } from "react";
import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import {
  hexA, parseTerm, edgeAnchor, PLOT, valueChip, placeChipYs, niceStep, useMeasuredBox,
} from "@/college-atlas/partnerships/chartKit";

// ── Shared trend chart: per-program lines ↔ stacked area ───────────────────
// One chart for both Program Enrollments and Program Awards, with a mode the
// user toggles:
//   • "lines"   — each program a line on a shared axis: individual trajectory
//                 and relative size. Nulls are gaps, drawn through. (Default
//                 for enrollment.)
//   • "stacked" — programs stacked so total output reads at the top edge:
//                 throughput and mix. Nulls count as 0. (Default for awards.)
// Color is keyed to the program's position in the cell, so a program keeps one
// hue across both charts and both modes. Hover a program (legend, line, or
// band) to focus it; its per-slot values appear as chips above the points.
// Leading/trailing columns no program reports are trimmed (calendars differ).
type TrendSeries = { top6: string; name: string; vals: (number | null)[] };

// Sentinel hover value for the stacked "Total" trend (the summed top edge),
// distinct from any program's index.
const TOTAL_FOCUS = -1;

function TrendChart({ series, labels, defaultMode, colorOf, axisStyle = "thinned", modeLabels = { lines: "Per program", stacked: "Stacked" }, hideSeriesTag = false, empty = false, demandLine, fill = false }: { series: TrendSeries[]; labels: string[]; defaultMode: "lines" | "stacked" | "demand"; colorOf: (top6: string) => string; axisStyle?: "thinned" | "twoTier"; modeLabels?: { lines: string; stacked: string; demand?: string }; hideSeriesTag?: boolean; empty?: boolean; demandLine?: { value: number; label: string; color: string };
  // fill: plot width follows the container's measured width (svg px == layout
  // units, so axis/label text holds its size at any panel width). Default
  // false ⇒ the report's fixed PLOT.W figure, unchanged.
  fill?: boolean }) {
  // "demand" is the third mode the demandLine prop unlocks: the stacked view
  // re-scaled so the reference line fits — supply read at market scale. When
  // the prop is absent (e.g. the targeted college view), a carried-over
  // "demand" mode falls back to stacked rather than rendering a missing line.
  const [mode, setMode] = useState<"lines" | "stacked" | "demand">(defaultMode);
  const effMode = mode === "demand" && !demandLine ? "stacked" : mode;
  const stackedBasis = effMode !== "lines";
  const [hover, setHover] = useState<number | null>(null);
  const { ref: boxRef, box } = useMeasuredBox(fill);
  const { padL, padR, padT } = PLOT;
  // Measured plot ⇒ viewBox px == container px ⇒ scale 1, fonts constant.
  // In fill mode the ref sits on the chart area between the mode toggle and
  // the legend, and BOTH dimensions follow it: the plot stretches into
  // whatever height the panel grants (PLOT.H stays the intrinsic minimum so
  // auto-height bands don't collapse). Until the first measurement lands,
  // PLOT geometry renders one report-proportioned frame rather than nothing.
  const W = fill && box ? Math.max(box.w, 320) : PLOT.W;
  // The two-tier axis (season row + year row) needs extra room below the plot;
  // adding it to both H and padB keeps the plot height identical to single-tier.
  const twoTier = axisStyle === "twoTier";
  const H = fill && box ? Math.max(box.h, PLOT.H) : PLOT.H + (twoTier ? 20 : 0);
  const padB = PLOT.padB + (twoTier ? 20 : 0);
  const base = H - padB, top = padT;

  // Shared x-axis renderer — the SINGLE source for both the populated chart and
  // the no-data ghost, so the empty state gets the identical two-tier season/year
  // axis (compact "Wi/Sp/Fa" + grouped years) rather than a parallel rendering
  // that overlaps full-term labels. Takes the column set + its X scale.
  const axisEls = (cols: number[], X: (k: number) => number) => {
    const n = cols.length;
    if (twoTier) {
      // A compact season label under every term, the year grouped beneath with
      // faint dividers — names every term without crowding.
      const parsed = cols.map((c) => parseTerm(labels[c]));
      const seasonEls = parsed.map((p, k) => (
        <g key={`s${k}`}>
          <line x1={X(k)} x2={X(k)} y1={base} y2={base + 3} stroke="rgba(255,255,255,.12)" />
          <text x={X(k)} y={base + 14} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 8.5, fill: "#5e6a83" }}>{p.season}</text>
        </g>
      ));
      const groups: { year: string; ks: number[] }[] = [];
      parsed.forEach((p, k) => {
        const last = groups[groups.length - 1];
        if (last && last.year === p.year) last.ks.push(k);
        else groups.push({ year: p.year, ks: [k] });
      });
      const yearEls = groups.map((g, gi) => {
        const cx = g.ks.reduce((a, b) => a + X(b), 0) / g.ks.length;
        const lx = Math.min(Math.max(cx, padL + 16), W - padR - 16);
        return (
          <g key={`y${gi}`}>
            {gi > 0 && <line x1={(X(g.ks[0]) + X(g.ks[0] - 1)) / 2} x2={(X(g.ks[0]) + X(g.ks[0] - 1)) / 2} y1={top} y2={base + 34} stroke="rgba(255,255,255,.13)" />}
            <text x={lx} y={base + 33} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10.5, fill: "#9aa6bd" }}>{g.year}</text>
          </g>
        );
      });
      return <>{seasonEls}{yearEls}</>;
    }
    // Thin labels so a long axis never crowds: at most ~12, always the last.
    const stride = Math.ceil(n / 12);
    return cols.map((c, k) => ((k % stride === 0 || k === n - 1) ? (
      <text key={c} x={X(k)} y={H - 8} textAnchor={n === 1 ? "middle" : edgeAnchor(k, n)} style={{ fontFamily: MONO, fontSize: 9.5, fill: "#5e6a83" }}>{labels[c]}</text>
    ) : null));
  };

  // No-data "ghost scaffold": the real chart frame — baseline + faint gridlines +
  // the SAME axis (via axisEls) — with no series and a calm centered label, so an
  // empty panel holds its exact footprint and reads in the chart's own design
  // language. No y-axis numbers — there's no measured scale, so it never reads
  // as a zero.
  if (empty) {
    // One uniform no-data state across every view (awards/enrollment ·
    // programs/occupations), independent of the populated chart's axis style:
    //   • single-tier height (PLOT.H) — twoTier's extra room is for an axis we
    //     don't draw, so dropping it keeps awards + enrollment ghosts identical;
    //   • no x-axis — term/year ticks are meaningless with no series, and a stray
    //     consortium-wide axis (which the occupation cell view happens to pass)
    //     is exactly what made this look different from the programs view;
    //   • gridlines flush to the left edge (no y-number gutter needed), label
    //     centered within that left-extended area so it reads balanced.
    const eH = fill && box ? Math.max(box.h, 150) : PLOT.H;
    const gBase = eH - PLOT.padB, gTop = padT;
    const gx0 = 0, gx1 = W - padR, gcx = (gx0 + gx1) / 2, gcy = (gTop + gBase) / 2;
    const ghost = (svgProps: React.SVGProps<SVGSVGElement>) => (
      <svg {...svgProps} viewBox={`0 0 ${W} ${eH}`}>
        {[0.25, 0.5, 0.75].map((f, i) => (
          <line key={i} x1={gx0} x2={gx1} y1={gBase - f * (gBase - gTop)} y2={gBase - f * (gBase - gTop)} stroke="rgba(255,255,255,.05)" />
        ))}
        <line x1={gx0} x2={gx1} y1={gBase} y2={gBase} stroke="rgba(255,255,255,.1)" />
        <text x={gcx} y={gcy - 3} textAnchor="middle" style={{ fontFamily: FONT, fontSize: 14, fontWeight: 500, fill: "#9aa6bd" }}>No data reported</text>
        <text x={gcx} y={gcy + 16} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10, fill: "#5e6a83" }}>via CCCCO DataMart</text>
      </svg>
    );
    if (fill) {
      return (
        <div ref={boxRef} style={{ marginTop: 14, flex: 1, minHeight: PLOT.H, position: "relative", overflow: "hidden" }}>
          {box && ghost({ width: W, height: eH, style: { position: "absolute", inset: 0 } })}
        </div>
      );
    }
    return (
      <div style={{ marginTop: 14 }}>
        {ghost({ width: "100%", preserveAspectRatio: "xMidYMid meet", style: { display: "block" } })}
      </div>
    );
  }

  const L = labels.length;
  // Programs with any data, carrying original index (→ stable color).
  const shownAll = series
    .map((s, idx) => ({ s, idx }))
    .filter((it) => it.s.vals.some((v) => v != null && v > 0));
  if (!shownAll.length) return null;
  // Keep only columns ≥1 shown program reports — drops not just the empty
  // boundary terms but every term the displayed college never runs (e.g. a
  // semester college's Winter terms), so the axis fits the calendar shown.
  const cols: number[] = [];
  for (let i = 0; i < L; i++) if (shownAll.some((it) => it.s.vals[i] != null)) cols.push(i);
  if (!cols.length) return null;
  const n = cols.length;
  const shown = shownAll.map((it) => ({ s: it.s, idx: it.idx, vals: cols.map((c) => it.s.vals[c]) }));

  const X = (k: number) => (n === 1 ? (padL + W - padR) / 2 : padL + (k / (n - 1)) * (W - padL - padR));

  const lineMax = Math.max(...shown.flatMap((it) => it.vals.filter((v): v is number => v != null)));
  const totals = cols.map((_, k) => shown.reduce((sum, it) => sum + (it.vals[k] ?? 0), 0));
  const stackMax = Math.max(...totals, 1);
  // vs. demand: the axis stretches to include the reference line — the stack
  // compressing against it IS the supply/demand read.
  const dataMax = effMode === "lines" ? lineMax
    : effMode === "demand" && demandLine ? Math.max(stackMax, demandLine.value)
    : stackMax;
  const step = niceStep(dataMax);
  const axisMax = Math.ceil(dataMax / step) * step;
  const Y = (v: number) => base - (v / axisMax) * (base - top);
  const ticks: number[] = [];
  for (let t = step; t <= axisMax; t += step) ticks.push(t);

  // Stacked geometry (largest-total at the base for a stable footing).
  const ordered = stackedBasis
    ? [...shown].sort((a, b) =>
        b.vals.reduce((s: number, v) => s + (v ?? 0), 0) - a.vals.reduce((s: number, v) => s + (v ?? 0), 0))
    : shown;
  const acc = cols.map(() => 0);
  const bands = ordered.map((it) => {
    const color = colorOf(it.s.top6);
    const loY = acc.slice();
    const hiY = cols.map((_, k) => loY[k] + (it.vals[k] ?? 0));
    for (let k = 0; k < n; k++) acc[k] = hiY[k];
    return { it, color, loY, hiY };
  });
  const single = n === 1;
  const barW = Math.min(72, (W - padL - padR) * 0.5);
  const focused = hover != null ? shown.find((it) => it.idx === hover) : undefined;

  return (
    <div style={fill ? { marginTop: 14, display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } : { marginTop: 14 }}>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8, flex: "none" }}>
        <div style={{ display: "inline-flex", border: "1px solid rgba(255,255,255,.12)", borderRadius: 8, overflow: "hidden" }}>
          {([...(["lines", "stacked"] as const), ...(demandLine ? (["demand"] as const) : [])]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{ appearance: "none", border: "none", cursor: "pointer", background: effMode === m ? "rgba(255,255,255,.1)" : "transparent", color: effMode === m ? "#e8ecf4" : "#9aa6bd", fontFamily: FONT, fontSize: 11.5, fontWeight: 500, padding: "5px 12px", transition: "background .12s, color .12s" }}
            >
              {m === "lines" ? modeLabels.lines : m === "stacked" ? modeLabels.stacked : (modeLabels.demand ?? "Demand")}
            </button>
          ))}
        </div>
      </div>
      {/* In fill mode the svg is absolutely positioned inside the measured
          area so its rendered size never feeds the row's min-content (which
          would ratchet the band's height clamp); PLOT.H is the floor. */}
      <div ref={fill ? boxRef : undefined} style={fill ? { flex: 1, minHeight: PLOT.H, position: "relative", overflow: "hidden" } : undefined}>
      <svg
        width={fill ? W : "100%"}
        height={fill ? H : undefined}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio={fill ? undefined : "xMidYMid meet"}
        style={fill ? { position: "absolute", inset: 0 } : { display: "block" }}
      >
        <line x1={padL} x2={W - padR} y1={base} y2={base} stroke="rgba(255,255,255,.1)" />
        {ticks.map((t) => (
          <g key={t}>
            <line x1={padL} x2={W - padR} y1={Y(t)} y2={Y(t)} stroke="rgba(255,255,255,.05)" />
            <text x={padL - 6} y={Y(t) + 3} textAnchor="end" style={{ fontFamily: MONO, fontSize: 9, fill: "#5e6a83" }}>{t.toLocaleString("en-US")}</text>
          </g>
        ))}

        {effMode === "lines"
          ? shown.map((it) => {
              const color = colorOf(it.s.top6);
              const on = hover === it.idx, faded = hover != null && !on;
              const pts: { x: number; y: number; k: number }[] = [];
              it.vals.forEach((v, k) => { if (v != null) pts.push({ x: X(k), y: Y(v), k }); });
              if (!pts.length) return null;
              const path = pts.map((q, j) => (j ? "L" : "M") + q.x.toFixed(1) + " " + q.y.toFixed(1)).join(" ");
              const lastPt = pts[pts.length - 1];
              return (
                <g key={it.s.top6}>
                  <path d={path} fill="none" stroke={color} strokeWidth={on ? 3 : 2} strokeLinejoin="round" strokeLinecap="round" opacity={faded ? 0.12 : on ? 1 : 0.82} />
                  {on
                    ? pts.map((q) => <circle key={q.k} cx={q.x} cy={q.y} r={3} fill={color} />)
                    : hover == null && <circle cx={lastPt.x} cy={lastPt.y} r={2.4} fill={color} />}
                  {/* invisible wide hit area so the thin line itself is hoverable */}
                  <path d={path} fill="none" stroke="transparent" strokeWidth={14} style={{ pointerEvents: "stroke", cursor: "pointer" }} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)} />
                </g>
              );
            })
          : bands.map(({ it, color, loY, hiY }) => {
              const on = hover === it.idx, faded = hover != null && !on;
              let shape: React.ReactNode;
              if (single) {
                const x = X(0) - barW / 2;
                shape = <rect x={x} y={Y(hiY[0])} width={barW} height={Math.max(0, Y(loY[0]) - Y(hiY[0]))} fill={color} opacity={faded ? 0.12 : on ? 0.72 : 0.5} />;
              } else {
                const up = cols.map((_, k) => `${k ? "L" : "M"}${X(k).toFixed(1)} ${Y(hiY[k]).toFixed(1)}`).join(" ");
                const down = cols.map((_, k) => n - 1 - k).map((k) => `L${X(k).toFixed(1)} ${Y(loY[k]).toFixed(1)}`).join(" ");
                shape = (
                  <>
                    <path d={`${up} ${down} Z`} fill={color} opacity={faded ? 0.12 : on ? 0.62 : 0.4} stroke="none" />
                    <path d={up} fill="none" stroke={color} strokeWidth={on ? 2.4 : 1.4} strokeLinejoin="round" opacity={faded ? 0.2 : 1} />
                  </>
                );
              }
              return (
                <g key={it.s.top6} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)} style={{ cursor: "pointer" }}>
                  {shape}
                </g>
              );
            })}

        {/* Stacked "Total": the summed trend along the top edge with its own
            value chips — focusable from the legend's Total row. */}
        {stackedBasis && hover === TOTAL_FOCUS && !single && (
          <path
            d={cols.map((_, k) => `${k ? "L" : "M"}${X(k).toFixed(1)} ${Y(totals[k]).toFixed(1)}`).join(" ")}
            fill="none" stroke="#e8ecf4" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round"
          />
        )}
        {stackedBasis && hover === TOTAL_FOCUS && (() => {
          const pts = totals.map((tv, k) => ({ x: X(k), y: Y(tv), v: tv })).filter((p) => p.v > 0);
          const ys = placeChipYs(pts, top + 9, base - 9);
          return <g>{pts.map((p, i) => valueChip(p.x, ys[i], p.v, "#e8ecf4", i, W))}</g>;
        })()}
        {/* Focused program: a value on every term, placed just above its point
            and bumped to the other side only if it would overlap its neighbor,
            so all show without colliding. Drawn last, on top of every series. */}
        {focused && (() => {
          const color = colorOf(focused.s.top6);
          const pts: { x: number; y: number; v: number }[] = [];
          if (effMode === "lines") {
            focused.vals.forEach((v, k) => { if (v != null) pts.push({ x: X(k), y: Y(v), v }); });
          } else {
            const b = bands.find((x) => x.it.idx === focused.idx);
            if (!b) return null;
            b.hiY.forEach((hv, k) => { if ((b.it.vals[k] ?? 0) > 0) pts.push({ x: X(k), y: Y(hv), v: b.it.vals[k] as number }); });
          }
          const ys = placeChipYs(pts, top + 9, base - 9);
          return <g>{pts.map((p, i) => valueChip(p.x, ys[i], p.v, color, i, W))}</g>;
        })()}

        {/* Regional addressable demand — the reference line the vs. demand
            mode exists for. Drawn last (over the bands), value pinned at its
            right end; the legend row carries the full grounding. */}
        {effMode === "demand" && demandLine && (
          <g>
            <line x1={padL} x2={W - padR} y1={Y(demandLine.value)} y2={Y(demandLine.value)} stroke={demandLine.color} strokeWidth={2} />
            <text x={W - padR} y={Y(demandLine.value) - 7} textAnchor="end" style={{ fontFamily: MONO, fontSize: 10.5, fontWeight: 600, fill: demandLine.color }}>
              {demandLine.value.toLocaleString("en-US")}/yr
            </text>
          </g>
        )}

        {axisEls(cols, X)}
      </svg>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", marginTop: 12, flex: "none" }}>
        {effMode === "demand" && demandLine && (
          <div style={{ gridColumn: "1 / -1", display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, minWidth: 0 }}>
            <span style={{ width: 16, height: 3, borderRadius: 2, background: demandLine.color, flex: "none" }} />
            <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: hexA(demandLine.color, 0.9), fontWeight: 500 }}>{demandLine.label}</span>
            <span style={{ fontFamily: MONO, fontSize: 10.5, color: hexA(demandLine.color, 0.75), flex: "none" }}>{demandLine.value.toLocaleString("en-US")}/yr</span>
          </div>
        )}
        {stackedBasis && (() => {
          const ton = hover === TOTAL_FOCUS, tdim = hover != null && hover !== TOTAL_FOCUS;
          return (
            <div onMouseEnter={() => setHover(TOTAL_FOCUS)} onMouseLeave={() => setHover(null)}
              style={{ gridColumn: "1 / -1", display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, background: ton ? "rgba(255,255,255,.07)" : "transparent", opacity: tdim ? 0.45 : 1, transition: "background .12s, opacity .12s", minWidth: 0 }}>
              <span style={{ width: 16, height: 3, borderRadius: 2, background: "#e8ecf4", flex: "none" }} />
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#e8ecf4", fontWeight: 500 }}>Total</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#5e6a83", flex: "none" }}>{totals[n - 1].toLocaleString("en-US")}</span>
            </div>
          );
        })()}
        {shown.map((it) => {
          const color = colorOf(it.s.top6);
          const on = hover === it.idx, dim = hover != null && !on;
          return (
            <div key={it.s.top6} onMouseEnter={() => setHover(it.idx)} onMouseLeave={() => setHover(null)}
              style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12.5, padding: "6px 9px", borderRadius: 8, background: on ? "rgba(255,255,255,.07)" : "transparent", opacity: dim ? 0.45 : 1, transition: "background .12s, opacity .12s", minWidth: 0 }}>
              <span style={{ width: 16, height: stackedBasis ? 10 : 3, borderRadius: stackedBasis ? 3 : 2, background: color, opacity: stackedBasis ? 0.62 : 1, flex: "none" }} />
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#9aa6bd" }}>{it.s.name}</span>
              {!hideSeriesTag && <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#5e6a83", flex: "none" }}>TOP {it.s.top6}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default TrendChart;
export type { TrendSeries };
