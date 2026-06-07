"use client";

import { FONT, MONO } from "@/college-atlas/partnerships/reportChrome";
import { hexA, useMeasuredBox } from "@/college-atlas/partnerships/chartKit";
import type { ApiSvampProgram } from "@/college-atlas/partnerships/api";

// ── Program wage outcomes (dumbbell) ──────────────────────────────────────
// Median earnings for completers of each feeder program at three checkpoints
// relative to award completion (2 yrs before / 2 after / 5 after), pooled
// STATEWIDE at the TOP6 grain by credential type — not college-specific, and
// not a time series. Each row is one cohort: a track from the before-wage to
// the 5-year wage (the gap is the lift), the three stages color-coded and
// keyed; ranked by 5-year earnings. The before / 5-year figures are labeled
// inline so the lift survives a screenshot; +2yr shows on hover. Stages are a
// single-hue intensity ramp of the school's brand color (faded → full), so the
// 5-year outcome lands in the full brand color and the ramp itself reads as the
// climb — branding the panel per school the way the rest of the report is.

function wageRecipientLabel(rt: string): string {
  if (/Associate or Bacc/i.test(rt)) return "Degree";
  if (/Chancellor.?s Office/i.test(rt)) return "CO Cert";
  if (/Locally Approved/i.test(rt)) return "Local Cert";
  return rt.replace(/\s*Recipient\s*$/i, "");
}
// Fixed credential order so the rows read consistently across every program.
const WAGE_RT_RANK: Record<string, number> = { "Degree": 0, "CO Cert": 1, "Local Cert": 2 };

type WageCohort = { rt: string; before: number; after2: number | null; after5: number; n: number | null };
type WageGroup = { name: string; top6: string; cohorts: WageCohort[] };

function WageOutcomes({ programs, brandColor, fill = false }: { programs: ApiSvampProgram[]; brandColor: string;
  // fill: plot width follows the container's measured width (svg px == layout
  // units, so text holds its size at any panel width). Default false ⇒ the
  // report's fixed 760-wide figure, unchanged.
  fill?: boolean }) {
  const { ref: boxRef, box } = useMeasuredBox(fill);
  // Group by program; each program heads a block, its credential cohorts beneath
  // (ranked by 5-year wage). Programs ordered by their best 5-year outcome.
  const groups: WageGroup[] = programs
    .map((p) => ({
      name: p.name,
      top6: p.top6,
      cohorts: (p.wages ?? [])
        .filter((w) => w.wage_before != null && w.wage_after_5 != null)
        .map((w) => ({
          rt: wageRecipientLabel(w.recipient_type),
          before: w.wage_before as number,
          after2: w.wage_after_2,
          after5: w.wage_after_5 as number,
          n: w.n,
        }))
        .sort((a, b) => (WAGE_RT_RANK[a.rt] ?? 9) - (WAGE_RT_RANK[b.rt] ?? 9)),
    }))
    .filter((g) => g.cohorts.length > 0)
    .sort((a, b) =>
      Math.max(...b.cohorts.map((c) => c.after5)) - Math.max(...a.cohorts.map((c) => c.after5)));
  if (!groups.length) {
    // Report mode keeps its no-render behavior (prose carries the absence).
    // Fill mode (the dashboard) renders the shared ghost scaffold — the
    // chart frame with no series, TrendChart's empty-state grammar.
    if (!fill) return null;
    const gW = box?.w ?? 760, gH = box?.h ?? 200;
    const gTop = 18, gBase = gH - 26, gx1 = gW - 16, gcx = gx1 / 2, gcy = (gTop + gBase) / 2;
    return (
      <div ref={boxRef} style={{ marginTop: 14, flex: 1, minHeight: 150, position: "relative", overflow: "hidden" }}>
        {box && (
          <svg width={gW} height={gH} viewBox={`0 0 ${gW} ${gH}`} style={{ position: "absolute", inset: 0 }}>
            {[0.25, 0.5, 0.75].map((f, i) => (
              <line key={i} x1={0} x2={gx1} y1={gBase - f * (gBase - gTop)} y2={gBase - f * (gBase - gTop)} stroke="rgba(255,255,255,.05)" />
            ))}
            <line x1={0} x2={gx1} y1={gBase} y2={gBase} stroke="rgba(255,255,255,.1)" />
            <text x={gcx} y={gcy - 3} textAnchor="middle" style={{ fontFamily: FONT, fontSize: 14, fontWeight: 500, fill: "#9aa6bd" }}>No data reported</text>
            <text x={gcx} y={gcy + 16} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 10, fill: "#5e6a83" }}>via CCCCO DataMart</text>
          </svg>
        )}
      </div>
    );
  }

  const fmtK = (v: number) => "$" + Math.round(v / 1000) + "k";
  const wageWindow = programs.flatMap((p) => p.wages ?? []).find((w) => w.window)?.window ?? "";
  const maxVal = Math.max(...groups.flatMap((g) => g.cohorts.flatMap((c) => [c.before, c.after2 ?? 0, c.after5])));
  const step = 20000;
  const axisMax = Math.max(step, Math.ceil(maxVal / step) * step);
  const W = fill && box ? Math.max(box.w, 320) : 760;
  const plotL = 126, padR = 16, padT = 10, headerH = 38, axisH = 30;
  // Base row metrics. In fill mode the rows STRETCH to occupy the panel's
  // measured height — fonts and dots hold their size, the dumbbells spread,
  // and the axis pins to the bottom — so a tall panel reads as a chart, not
  // as a small figure floating in dead space.
  let rowH = 34, gap = 20;
  const nRows = groups.reduce((s, g) => s + g.cohorts.length, 0);
  let H = padT + groups.length * (headerH + gap) + nRows * rowH + axisH;
  if (fill && box && box.h > H) {
    const fixed = padT + groups.length * headerH + axisH;
    const s = (box.h - fixed) / (nRows * rowH + groups.length * gap);
    rowH *= s; gap *= s;
    H = box.h;
  }
  const axisY = H - axisH + 6;
  const X = (w: number) => plotL + (w / axisMax) * (W - plotL - padR);
  const ticks: number[] = [];
  for (let t = 0; t <= axisMax; t += step) ticks.push(t);
  // Stage ramp: faded brand → full brand (the 5-year destination). Accent only
  // on the data; chrome (TOP code, labels, axis) stays neutral.
  const stageB = hexA(brandColor, 0.5), stageA2 = hexA(brandColor, 0.72);
  const stageKey: [string, string, number][] = [
    ["2 yrs before award", stageB, 11], ["2 yrs after", stageA2, 11], ["5 yrs after", brandColor, 13],
  ];

  const els: React.ReactNode[] = [];
  let y = padT;
  groups.forEach((g, gi) => {
    els.push(
      <g key={`h${gi}`}>
        <text x={2} y={y + 15} style={{ fontFamily: FONT, fontSize: 14, fontWeight: 600, fill: "#e8ecf4" }}>
          {g.name}
          <tspan dx={9} style={{ fontWeight: 400, fill: "rgba(255,255,255,0.25)" }}>·</tspan>
          <tspan dx={7} style={{ fontFamily: MONO, fontSize: 11, fontWeight: 500, letterSpacing: "0.03em", fill: "#8893ab" }}>TOP {g.top6}</tspan>
        </text>
        <line x1={2} x2={W - padR} y1={y + 24} y2={y + 24} stroke="rgba(255,255,255,.08)" />
      </g>,
    );
    y += headerH;
    g.cohorts.forEach((c, ci) => {
      const cy = y + rowH / 2;
      // 5-year value sits right of its dot, but flips to the left if the dot is
      // so far right the label would overflow the chart.
      const a5x = X(c.after5);
      const a5lbl = fmtK(c.after5);
      const a5flip = a5x + 12 + a5lbl.length * 7 + 6 > W;
      els.push(
        <g key={`r${gi}-${ci}`}>
          <text x={16} y={cy + 4} style={{ fontFamily: FONT, fontSize: 12.5, fill: "#9aa6bd" }}>
            {c.rt}
            <tspan style={{ fontFamily: MONO, fontSize: 10, fill: "#5e6a83" }}>{c.n != null ? ` · n=${c.n}` : ""}</tspan>
          </text>
          <line x1={X(c.before)} x2={X(c.after5)} y1={cy} y2={cy} stroke={hexA(brandColor, 0.28)} strokeWidth={3} strokeLinecap="round" />
          <circle cx={X(c.before)} cy={cy} r={4} fill={stageB} />
          {c.after2 != null && <circle cx={X(c.after2)} cy={cy} r={4} fill={stageA2} />}
          <circle cx={X(c.after5)} cy={cy} r={6.5} fill={brandColor} stroke="#060d1f" strokeWidth={1.5} />
          <text x={X(c.before) - 10} y={cy + 4} textAnchor="end" style={{ fontFamily: MONO, fontSize: 10, fill: hexA(brandColor, 0.8) }}>{fmtK(c.before)}</text>
          {c.after2 != null && <text x={X(c.after2)} y={cy - 11} textAnchor="middle" style={{ fontFamily: MONO, fontSize: 9.5, fill: hexA(brandColor, 0.7) }}>{fmtK(c.after2)}</text>}
          <text x={a5flip ? a5x - 11 : a5x + 12} y={cy + 4} textAnchor={a5flip ? "end" : "start"} style={{ fontFamily: MONO, fontSize: 12, fontWeight: 500, fill: brandColor }}>{a5lbl}</text>
        </g>,
      );
      y += rowH;
    });
    y += gap;
  });

  const legendEl = (
    <div style={{ display: "flex", gap: 18, flexWrap: "wrap", justifyContent: "flex-end", paddingRight: `${(padR / W) * 100}%`, fontSize: 12, color: "#9aa6bd", marginBottom: 12, flex: "none" }}>
      {stageKey.map(([lbl, col, sz]) => (
        <span key={lbl} style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
          <span style={{ width: sz, height: sz, borderRadius: "50%", background: col, display: "inline-block" }} />
          {lbl}
        </span>
      ))}
    </div>
  );
  const axisEls = (
    <>
      {/* Clean bottom axis — baseline + short ticks, no full-height gridlines
          (which used to strike through the program headers). */}
      <line x1={plotL} x2={W - padR} y1={axisY} y2={axisY} stroke="rgba(255,255,255,.1)" />
      {ticks.map((t) => (
        <g key={t}>
          <line x1={X(t)} x2={X(t)} y1={axisY} y2={axisY + 4} stroke="rgba(255,255,255,.18)" />
          <text x={X(t)} y={axisY + 16} textAnchor={t === 0 ? "start" : t === axisMax ? "end" : "middle"} style={{ fontFamily: MONO, fontSize: 9, fill: "#5e6a83" }}>{fmtK(t)}</text>
        </g>
      ))}
    </>
  );
  const footnoteEl = (
    <div style={{ fontSize: 11, color: "#5e6a83", marginTop: 12, lineHeight: 1.6, flex: "none" }}>
      Earnings pooled statewide at the TOP6 grain by credential type — not college-specific.
      Degree = Associate or Baccalaureate Degree; CO Cert = Chancellor&apos;s Office Approved Certificate; Local Cert = Locally Approved Certificate; n = Total Awards{wageWindow ? ` ${wageWindow}` : ""}.
    </div>
  );

  if (fill) {
    // Measured-height layout: the svg is absolutely positioned inside the
    // measured area so its rendered height never feeds back into the row's
    // min-content (which would ratchet the band's height clamp upward).
    // No footnote — the dashboard visualizes only; the definitional and
    // statewide-grain caveats live in the report's footnote.
    return (
      <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, marginTop: 14 }}>
        {legendEl}
        <div ref={boxRef} style={{ flex: 1, minHeight: 0, position: "relative", overflow: "hidden" }}>
          {box && (
            <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0 }}>
              {els}
              {axisEls}
            </svg>
          )}
        </div>
      </div>
    );
  }
  return (
    <div style={{ marginTop: 14 }}>
      {legendEl}
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        {els}
        {axisEls}
      </svg>
      {footnoteEl}
    </div>
  );
}

export default WageOutcomes;
